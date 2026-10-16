"""Experimentos de modificación: qué pasa al cambiar una pieza del sistema (código o prompt).

    python -m evaluation.eval_modificaciones

1. k (sin LLM): Hit@k, MRR y tamaño del prompt con k = 1, 2, 4 y 6 fragmentos.
2. Prompt (Groq): quitar del prompt RAG la instrucción de rechazo y ver cuántas de las 8 preguntas
   cercanas al dominio (ooc_dificil) pasan a responderse; y qué haría el prompt sin el umbral.
3. Código (Groq): no forzar las secciones 7 y 8 de la política en devoluciones aceptadas.
Con Groq se pausa LLM_PAUSE_S entre llamadas. Sin clave solo corre el experimento 1.
"""
import datetime
import json
import re
import time
from unittest import mock

from evaluation.metrics import embed_docs, hit_rank, load_gold, summarize, top_k
from src import app, rag_chain
from src.chunking import load_chunks
from src.config import K, LLM_PAUSE_S, RELEVANCE_THRESHOLD, RESULTS_DIR
from src.embeddings import E5Embeddings
from src.llm import LLMError, describe, resolve_provider
from src.retriever import retrieve

REFUSAL = "no cuento con las herramientas"
RETURN_CASES = [  # dos devoluciones que el verificador acepta
    "Quiero devolver unos audífonos, los compré hace 10 días, sin usar y con su empaque original",
    "Quiero devolver mi botella reutilizable de acero, la recibí hace 20 días, sin usar y con su empaque original",
]


def experiment_k() -> list[dict]:
    emb = E5Embeddings()
    chunks = load_chunks()
    vecs = embed_docs(chunks, emb)
    questions = load_gold("in")
    max_k = 6
    found = [top_k(chunks, vecs, emb.embed_query(q["pregunta"]), max_k) for q in questions]
    ranks = [hit_rank([d for d, _ in f], q) for f, q in zip(found, questions)]
    rows = []
    for k in (1, 2, 4, 6):
        ranks_k = [r if r is not None and r <= k else None for r in ranks]  # un acierto más allá de k no cuenta
        chars = sum(sum(len(d.page_content) for d, _ in f[:k]) for f in found) / len(found)
        m = summarize(ranks_k, k)
        rows.append({"k": k, "hit@k": m[f"hit@{k}"], "mrr": m["mrr"], "caracteres_por_consulta": chars})
    return rows


def pause(seconds: float) -> None:
    time.sleep(seconds)


def rag_answer(question: str, docs, system: str) -> str:
    chain = rag_chain.build_chain(system, rag_chain.RAG_HUMAN)
    return rag_chain.to_plain_text(chain.invoke({"context": rag_chain.format_context(docs), "question": question}))


def experiment_prompt(pause_s: float) -> dict:
    """ooc_dificil: ¿cuántas se responden con el prompt actual, sin la instrucción de rechazo, y sin umbral?"""
    system_actual = rag_chain.RAG_SYSTEM
    # Se quita SOLO la línea que ordena rechazar cuando el contexto no tiene la respuesta
    system_sin_rechazo = "\n".join(l for l in system_actual.split("\n") if not l.startswith("Si el contexto no contiene"))
    assert system_sin_rechazo != system_actual

    store = app._store()
    rows = []
    for q in load_gold("ooc_dificil"):
        results = retrieve(q["pregunta"], K, store)
        passing = [d for d, s in results if s >= RELEVANCE_THRESHOLD]  # lo que entregaría el chat
        row = {"id": q["id"], "pregunta": q["pregunta"], "top1": round(results[0][1], 3), "pasa_umbral": bool(passing)}
        # (1) actual = umbral + instrucción. Si no pasa el umbral, el chat responde el mensaje fijo sin LLM.
        # (2) sin instrucción de rechazo (con umbral). (3) sin umbral (con instrucción): el LLM ve los 4 fragmentos.
        variants = {"actual": (passing, system_actual), "sin_instruccion_de_rechazo": (passing, system_sin_rechazo),
                    "sin_umbral": ([d for d, _ in results], system_actual)}
        for name, (docs, system) in variants.items():
            if not docs:
                row[name] = {"respuesta": rag_chain.NOT_AVAILABLE, "llm": False}
            elif name == "sin_umbral" and passing:  # mismo contexto y prompt que «actual»: se reutiliza
                row[name] = row["actual"]
            else:
                row[name] = {"respuesta": rag_answer(q["pregunta"], docs, system), "llm": True}
                pause(pause_s)
            row[name]["respondida"] = REFUSAL not in row[name]["respuesta"].lower()
        rows.append(row)
        print(f"{q['id']} top1={row['top1']} pasa={row['pasa_umbral']} respondida: actual={row['actual']['respondida']} "
              f"sin_instruccion={row['sin_instruccion_de_rechazo']['respondida']} sin_umbral={row['sin_umbral']['respondida']}",
              flush=True)
    return {"filas": rows, **{n: sum(r[n]["respondida"] for r in rows)
                              for n in ("actual", "sin_instruccion_de_rechazo", "sin_umbral")}}


def experiment_sections(pause_s: float) -> list[dict]:
    """Devoluciones aceptadas: ¿el LLM da los pasos de la política con y sin las secciones 7 y 8 forzadas?"""
    rows = []
    for text in RETURN_CASES:
        row = {"pregunta": text}
        for name, patch in (("con_secciones_7_y_8", None), ("sin_secciones_7_y_8", lambda ids, store=None: [])):
            if patch is None:
                answer = app.answer_return(text, True)
            else:
                with mock.patch.object(app, "get_chunks", patch):  # desactiva el añadido de politica::7 y ::8
                    answer = app.answer_return(text, True)
            answer = rag_chain.to_plain_text(answer)
            row[name] = {"respuesta": answer,
                         "paso_1_soporte": "soporte@ecomarket.example" in answer,
                         "paso_4_transportadora": "transportadora" in answer.lower(),
                         "reembolso_5_a_10_dias": bool(re.search(r"5 a 10", answer))}
            pause(pause_s)
        rows.append(row)
        print(f"{text[:45]}... " + " | ".join(f"{n}: {sum(v for k, v in row[n].items() if k != 'respuesta')}/3 elementos de la política"
                                              for n in ("con_secciones_7_y_8", "sin_secciones_7_y_8")), flush=True)
    return rows


def main() -> None:
    today = datetime.date.today().isoformat()
    result = {"fecha": today, "k": experiment_k()}
    print("k:", [(r["k"], round(r["hit@k"], 2), round(r["mrr"], 2), round(r["caracteres_por_consulta"])) for r in result["k"]])

    provider, _ = resolve_provider()
    model = describe()
    if provider == "groq":
        result["modelo"] = model
        result["prompt"] = experiment_prompt(LLM_PAUSE_S)
        result["secciones"] = experiment_sections(LLM_PAUSE_S)
    else:
        print("Sin GROQ_API_KEY: solo se ejecuta el experimento de k (los otros llaman al generador de Groq).")

    lines = [f"# Experimentos de modificación — {model if provider == 'groq' else 'solo sin LLM'} — {today}", "",
             "## 1. Número de fragmentos recuperados (k)", "", "29 preguntas 'in', acierto por `chunk_id`, índice en memoria.", "",
             "| k | Hit@k | MRR | Caracteres enviados por consulta |", "|---|---|---|---|"]
    lines += [f"| {r['k']} | {r['hit@k']:.2f} | {r['mrr']:.2f} | {r['caracteres_por_consulta']:.0f} |" for r in result["k"]]
    if "prompt" in result:
        p = result["prompt"]
        lines += ["", "## 2. Prompt: quitar la instrucción de rechazo", "",
                  f"8 preguntas cercanas al dominio (ooc_dificil), umbral {RELEVANCE_THRESHOLD}. «Respondida» = la respuesta no es el mensaje de rechazo.", "",
                  "| Configuración | Preguntas respondidas (de 8) |", "|---|---|",
                  f"| actual (umbral + instrucción de rechazo) | {p['actual']} |",
                  f"| sin la instrucción de rechazo (umbral sí) | {p['sin_instruccion_de_rechazo']} |",
                  f"| sin umbral (instrucción sí) | {p['sin_umbral']} |", "",
                  "| Id | Pregunta | Top-1 | Pasa el umbral | actual | sin instrucción | sin umbral |", "|---|---|---|---|---|---|---|"]
        yn = lambda b: "responde" if b else "rechaza"
        lines += [f"| {r['id']} | {r['pregunta']} | {r['top1']} | {'sí' if r['pasa_umbral'] else 'no'} | {yn(r['actual']['respondida'])} | "
                  f"{yn(r['sin_instruccion_de_rechazo']['respondida'])} | {yn(r['sin_umbral']['respondida'])} |" for r in p["filas"]]
        lines += ["", "### Respuestas cuando el LLM respondió", ""]
        for r in p["filas"]:
            for name in ("actual", "sin_instruccion_de_rechazo", "sin_umbral"):
                if r[name]["llm"] and r[name]["respondida"] and not (name == "sin_umbral" and r["pasa_umbral"]):
                    lines.append(f"- **{r['id']} / {name}** ({r['pregunta']}): {r[name]['respuesta']}")
    if "secciones" in result:
        lines += ["", "## 3. Código: no forzar las secciones 7 y 8 en devoluciones aceptadas", "",
                  "Elementos de la política que debe contener la respuesta: escribir a soporte@ (paso 1), entregar a la transportadora (paso 4) y reembolso en 5 a 10 días.", "",
                  "| Caso | Con secciones 7 y 8 | Sin secciones 7 y 8 |", "|---|---|---|"]
        for r in result["secciones"]:
            cells = [f"{sum(v for k, v in r[n].items() if k != 'respuesta')}/3" for n in ("con_secciones_7_y_8", "sin_secciones_7_y_8")]
            lines.append(f"| {r['pregunta'][:60]}… | {cells[0]} | {cells[1]} |")
        lines += ["", "### Respuestas sin las secciones 7 y 8", ""]
        lines += [f"- {r['pregunta'][:50]}…: {r['sin_secciones_7_y_8']['respuesta']}" for r in result["secciones"]]

    RESULTS_DIR.mkdir(exist_ok=True)
    slug = re.sub(r"[^a-z0-9.-]+", "_", model.lower()) if provider == "groq" else "sin_llm"
    stem = f"modificaciones_{slug}_{today}"
    (RESULTS_DIR / f"{stem}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (RESULTS_DIR / f"{stem}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Escrito results/{stem}.md")


if __name__ == "__main__":
    try:
        main()
    except LLMError as e:
        raise SystemExit(f"Error del generador: {e}")
