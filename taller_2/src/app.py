"""Chat de EcoMarket por consola.

    python -m src.app                       # chat con el LLM configurado
    python -m src.app --solo-recuperacion   # fragmentos, puntajes y veredicto, sin cargar el LLM

Flujo fijo: enrutador por reglas -> pedido | devolución | RAG.
"""
import argparse
import sys
from functools import lru_cache

from src import rag_chain
from src.config import K, RELEVANCE_THRESHOLD, USE_RULES
from src.llm import USAGE, LLMError, describe
from src.orders import extract_tracking, find_order
from src.retriever import get_chunks, get_retriever, get_store, retrieve
from src.router import route
from src.rules import check_return, parse_return_request

# Se crean una sola vez: cargar el modelo de embeddings y las cadenas es lo costoso
@lru_cache(maxsize=1)
def _store():
    return get_store()


@lru_cache(maxsize=1)
def _retriever():
    return get_retriever(_store())


@lru_cache(maxsize=None)
def _chain(name: str, use_rules: bool = True):
    return rag_chain.return_chain(use_rules) if name == "return" else getattr(rag_chain, f"{name}_chain")()


# ---------- Flujos ----------

def answer_order(text: str) -> str:
    tracking = extract_tracking(text)
    order = find_order(tracking)
    if order is None:
        # Sin LLM y sin inventar: el número no existe en pedidos.json
        return (f"No encontré ningún pedido con el número {tracking}. Verifica que tenga el formato ECM seguido "
                "de 5 dígitos o escribe a soporte@ecomarket.example.")
    order_text = (f"Número de seguimiento: {order['tracking_number']}\nProducto: {order['product']}\n"
                  f"Estado: {order['status']}\nFecha estimada de entrega: {order['estimated_delivery']}\n"
                  f"Enlace de seguimiento: {order['tracking_url']}")
    return _chain("order").invoke({"order": order_text, "question": text})


def answer_rag(text: str) -> str:
    docs = _retriever().invoke(text)  # ya viene filtrado por el umbral de relevancia
    if not docs:
        return rag_chain.NOT_AVAILABLE  # sin llamar al LLM
    return _chain("rag").invoke({"context": rag_chain.format_context(docs), "question": text})


def answer_return(text: str, use_rules: bool) -> str:
    data = parse_return_request(text)
    # Si el texto no trae ningún dato de un caso concreto («¿cuántos días tengo para devolver?»)
    # es una pregunta sobre la política: se atiende con el RAG normal, no con el verificador.
    if all(v is None for v in data.values()):
        return answer_rag(text)

    # El enrutador ya decidió que el tema es devolución: se busca solo en la política, sin umbral
    docs = [d for d, _ in retrieve(text, K, _store(), doc_type="politica")]
    context = rag_chain.format_context(docs)
    if not use_rules:
        return _chain("return", False).invoke({"context": context, "question": text})

    verdict = check_return(**data)
    if verdict["aceptada"] is None:  # faltan datos: se piden, no se adivinan
        needed = "\n".join(f"- {f}" for f in verdict["faltantes"])
        return ("Para revisar tu devolución necesito que me indiques:\n" + needed +
                "\nCuéntamelo en un solo mensaje, por ejemplo: «Quiero devolver unos audífonos, los recibí hace "
                "10 días, están sin usar y con su empaque original».")
    if verdict["aceptada"]:
        # Los pasos (sección 7) y el reembolso (8) no siempre salen en el top 4; sin ellos el LLM los inventa
        have = {d.metadata["chunk_id"] for d in docs}
        docs += get_chunks([c for c in ("politica::7", "politica::8") if c not in have], _store())
        context = rag_chain.format_context(docs)
    return _chain("return", True).invoke({
        "verdict": "ACEPTADA" if verdict["aceptada"] else "RECHAZADA",
        "reasons": "\n".join(f"- {m}" for m in verdict["motivos"]),
        "context": context, "question": text})


def respond(text: str, use_rules: bool = USE_RULES) -> str:
    kind = route(text)
    if kind == "order":
        answer = answer_order(text)
    elif kind == "return":
        answer = answer_return(text, use_rules)
    else:
        answer = answer_rag(text)
    return rag_chain.to_plain_text(answer)


# ---------- Modo sin LLM ----------

def show_retrieval(text: str, use_rules: bool = USE_RULES) -> None:
    kind = route(text)
    print(f"ruta: {kind}")
    if kind == "order":
        order = find_order(extract_tracking(text))
        print("pedido:", order if order else "no encontrado -> se respondería que no existe")
        return
    only_policy = False  # True = caso concreto de devolución: se busca solo en la política
    if kind == "return":
        data = parse_return_request(text)
        if all(v is None for v in data.values()):
            print("sin datos de un caso concreto -> se atiende como pregunta de política (RAG)")
        else:
            only_policy = True
            print("datos extraídos:", data)
            print("verificador:", check_return(**data) if use_rules else "(USE_RULES=0: decidiría el LLM)")
    results = retrieve(text, K, _store(), doc_type="politica" if only_policy else None)
    for doc, score in results:
        mark = "pasa" if score >= RELEVANCE_THRESHOLD else "bajo el umbral"
        print(f"  {score:.3f} [{mark}] {doc.metadata['chunk_id']}")
    passed = any(s >= RELEVANCE_THRESHOLD for _, s in results)
    print(f"umbral {RELEVANCE_THRESHOLD}: " + ("hay contexto, se llamaría al LLM" if passed
                                               else "ningún fragmento lo supera -> mensaje fijo, sin LLM"))


# ---------- CLI ----------

def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # tildes y «» también cuando la salida no es una consola
    parser = argparse.ArgumentParser(description="Asistente de atención al cliente de EcoMarket")
    parser.add_argument("--solo-recuperacion", action="store_true",
                        help="muestra fragmentos, puntajes y veredicto sin cargar el LLM")
    args = parser.parse_args()

    if args.solo_recuperacion:
        print("Modo sin LLM. Escribe una pregunta ('salir' para terminar).")
    else:
        try:
            generator = describe()
        except LLMError as e:  # p. ej. LLM_PROVIDER con un valor no válido: se avisa sin traza
            raise SystemExit(str(e))
        print(f"EcoMarket — generador: {generator} | reglas de devolución: {'sí' if USE_RULES else 'no'}")
        print("Escribe tu consulta ('salir' para terminar).")

    while True:
        try:
            text = input("\nTú: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not text:
            continue
        if text.lower() in ("salir", "exit", "quit"):
            break
        try:
            if args.solo_recuperacion:
                show_retrieval(text)
            else:
                print("\nAsistente:", respond(text))
                if USAGE["calls"]:
                    print(f"[tokens de la sesión: entrada {USAGE['input_tokens']}, salida {USAGE['output_tokens']}]")
        except LLMError as e:
            # Sin cambio automático de modelo: se informa y el usuario decide (ver README)
            print(f"\nAsistente: no pude generar la respuesta. {e}")


if __name__ == "__main__":
    main()
