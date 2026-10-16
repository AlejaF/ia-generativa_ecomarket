"""Ablación de la fragmentación y experimento de solapamiento FAQ/envíos (sin LLM, sin API).

Hipótesis declarada: los fragmentos que mezclan varias unidades (reglas, productos) diluyen el
significado y meten ruido en el prompt. Se compara la fragmentación por estructura con tamaño fijo,
aplicando cada estrategia POR DOCUMENTO, con los mismos embeddings y el mismo k.
El acierto se mide con `texto_clave` (los ids cambian entre fragmentaciones).
"""
import json
from collections import defaultdict
from math import comb

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from evaluation.metrics import embed_docs, hit_rank, load_gold, summarize, top_k
from src.chunking import load_chunks
from src.config import DATA_DIR, K, RESULTS_DIR
from src.embeddings import E5Embeddings

# FAQ cuyos datos están repetidos en envios_y_pagos.md, con la sección que los repite
FAQ_TO_ENVIOS = {
    "faq::FAQ01": "envios::metodos-y-tiempos-de-envio", "faq::FAQ02": "envios::costos-de-envio",
    "faq::FAQ03": "envios::cobertura", "faq::FAQ04": "envios::estados-del-pedido",
    "faq::FAQ05": "envios::estados-del-pedido", "faq::FAQ06": "envios::pedidos-retrasados",
    "faq::FAQ07": "envios::cancelaciones-y-cambios-de-direccion",
    "faq::FAQ08": "envios::cancelaciones-y-cambios-de-direccion", "faq::FAQ10": "envios::medios-de-pago",
    "faq::FAQ11": "envios::facturacion", "faq::FAQ14": "envios::atencion-al-cliente",
}


# ---------- Textos por documento para las estrategias de tamaño fijo ----------

def document_texts() -> dict[str, str]:
    """Un texto por documento. politica y envios: el archivo tal cual. faq y catalogo: una línea de
    lenguaje natural por registro (el JSON/CSV crudo no sería una base justa para embeddings)."""
    by_type = defaultdict(list)
    for c in load_chunks():
        by_type[c.metadata["doc_type"]].append(c.page_content.split("\n", 1)[1])  # cuerpo sin el encabezado
    return {
        "politica": (DATA_DIR / "politica_devoluciones.txt").read_text(encoding="utf-8").replace("\r\n", "\n"),
        "envios": (DATA_DIR / "envios_y_pagos.md").read_text(encoding="utf-8").replace("\r\n", "\n"),
        "faq": "\n\n".join(by_type["faq"]),
        "catalogo": "\n\n".join(by_type["catalogo"]),
    }


def fixed_size_chunks(size: int, overlap: int) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=size, chunk_overlap=overlap)
    return [Document(page_content=piece, metadata={"chunk_id": f"{doc}#{i}", "doc_type": doc})
            for doc, text in document_texts().items() for i, piece in enumerate(splitter.split_text(text))]


# ---------- Evaluación de una configuración de índice ----------

def random_hit(n_chunks: int, n_relevant: int, k: int) -> float:
    """Probabilidad de que k fragmentos elegidos AL AZAR incluyan alguno de los n_relevant (sin reposición).
    Es el suelo contra el que se lee Hit@k: con pocos fragmentos grandes, el azar ya acierta mucho."""
    if n_relevant == 0:
        return 0.0
    return 1 - comb(n_chunks - n_relevant, k) / comb(n_chunks, k) if n_chunks - n_relevant >= k else 1.0


def evaluate_index(chunks, emb, questions) -> dict:
    vecs = embed_docs(chunks, emb)
    ranks, sent_chars, tops, chance, answerable = [], [], [], [], 0
    for q in questions:
        found = [d for d, _ in top_k(chunks, vecs, emb.embed_query(q["pregunta"]), K)]
        tops.append(found)
        ranks.append(hit_rank(found, q, by_text=True))
        sent_chars.append(sum(len(d.page_content) for d in found))
        relevant = sum(any(k in c.page_content for k in q["texto_clave"]) for c in chunks)  # fragmentos con la respuesta
        chance.append(random_hit(len(chunks), relevant, K))
        answerable += relevant > 0  # ¿existe en el índice algún fragmento con la respuesta? (si no, el índice sesga el resultado)
    corpus_chars = sum(len(c.page_content) for c in chunks)
    avg_sent = sum(sent_chars) / len(sent_chars)
    return {"fragmentos": len(chunks), **summarize(ranks, K),
            f"hit@{K}_por_azar": sum(chance) / len(chance),
            "caracteres_enviados_por_consulta": avg_sent,
            "pct_del_corpus_enviado": 100 * avg_sent / corpus_chars,
            "preguntas_con_fuente_valida": answerable}, tops


def main() -> None:
    emb = E5Embeddings()
    questions = load_gold("in")
    structure = load_chunks()

    # ---- 1. Estrategias de fragmentación ----
    strategies = {"estructura": structure, "tamaño fijo 1000/0": fixed_size_chunks(1000, 0),
                  "tamaño fijo 500/80": fixed_size_chunks(500, 80)}
    frag = {}
    for name, chunks in strategies.items():
        frag[name], _ = evaluate_index(chunks, emb, questions)
        r = frag[name]
        print(f"{name:20} n={r['fragmentos']:>3} Hit@1={r['hit@1']:.2f} Hit@{K}={r[f'hit@{K}']:.2f} "
              f"MRR={r['mrr']:.2f} chars/consulta={r['caracteres_enviados_por_consulta']:.0f}")

    # ---- 2. Solapamiento FAQ / envíos ----
    dup_faq = set(FAQ_TO_ENVIOS)  # FAQ01–08, 10, 11, 14
    no_dup = [c for c in structure if c.metadata["chunk_id"] not in dup_faq]
    subset = [q for q in questions if q["tema"] in ("envios", "pagos", "pedidos")]
    overlap = {}
    for name, chunks in (("(a) todo", structure), ("(b) sin FAQ duplicadas", no_dup)):
        overlap[name], tops = evaluate_index(chunks, emb, subset)
    # ¿En cuántas consultas aparecen una FAQ y la sección que la repite juntas en el top 4? (índice completo)
    _, tops_all = evaluate_index(structure, emb, questions)
    _, tops_sub = evaluate_index(structure, emb, subset)

    def both_in_top(tops_list) -> int:
        n = 0
        for found in tops_list:
            ids = {d.metadata["chunk_id"] for d in found}
            n += any(faq in ids and env in ids for faq, env in FAQ_TO_ENVIOS.items())
        return n

    together = {"preguntas de envíos/pagos/pedidos": f"{both_in_top(tops_sub)}/{len(subset)}",
                "las 29 preguntas 'in'": f"{both_in_top(tops_all)}/{len(questions)}"}

    # ---- Reporte ----
    lines = ["# Ablación de la fragmentación", "",
             "Hipótesis: los fragmentos que mezclan varias unidades diluyen el significado y meten ruido en el prompt.",
             f"29 preguntas 'in', k={K}, mismos embeddings. Acierto por `texto_clave`. Cada estrategia se aplica por documento. "
             "En tamaño fijo, faq y catálogo se parten desde su texto en lenguaje natural (una línea por registro).", "",
             f"| Estrategia | Fragmentos | Hit@1 | Hit@{K} | Hit@{K} por azar | MRR | Caracteres enviados por consulta | % del corpus enviado |",
             "|---|---|---|---|---|---|---|---|"]
    for name, r in frag.items():
        lines.append(f"| {name} | {r['fragmentos']} | {r['hit@1']:.2f} | {r[f'hit@{K}']:.2f} | {r[f'hit@{K}_por_azar']:.2f} | "
                     f"{r['mrr']:.2f} | {r['caracteres_enviados_por_consulta']:.0f} | {r['pct_del_corpus_enviado']:.0f} % |")
    lines += ["", f"**Cómo leer Hit@{K}:** «por azar» es la probabilidad de acertar eligiendo {K} fragmentos al azar (misma definición de "
              "acierto). Con pocos fragmentos grandes el azar ya acierta mucho, así que el empate en Hit@4 entre estrategias dice poco; "
              "las diferencias informativas son Hit@1, MRR y el tamaño del prompt.",
              "", "# Solapamiento FAQ / envíos", "",
              f"Se quitan las FAQ01–08, 10, 11 y 14 (sus datos están repetidos en envios_y_pagos.md). "
              f"{len(subset)} preguntas de envíos, pagos y pedidos.", "",
              "**Definición de acierto:** una pregunta acierta si alguna `texto_clave` literal aparece en los fragmentos recuperados "
              "(no se exige un `chunk_id`, así que el índice (b) no se penaliza por no tener las FAQ). "
              "Columna «con fuente válida»: preguntas para las que el índice contiene al menos un fragmento con la respuesta.", "",
              f"| Índice | Fragmentos | Hit@1 | Hit@{K} | Hit@{K} por azar | MRR | Caracteres enviados | Preguntas con fuente válida |",
              "|---|---|---|---|---|---|---|---|"]
    for name, r in overlap.items():
        lines.append(f"| {name} | {r['fragmentos']} | {r['hit@1']:.2f} | {r[f'hit@{K}']:.2f} | {r[f'hit@{K}_por_azar']:.2f} | "
                     f"{r['mrr']:.2f} | {r['caracteres_enviados_por_consulta']:.0f} | "
                     f"{r['preguntas_con_fuente_valida']}/{len(subset)} |")
    lines += ["", "Consultas con una FAQ y la sección que la repite juntas en el top 4 (índice completo):", ""]
    lines += [f"- {k}: {v}" for k, v in together.items()]
    lines += ["", "Sesgos conocidos: (1) las 12 preguntas se eligieron justamente por tener fuente duplicada, así que el experimento "
              "responde solo para ese tipo de pregunta; (2) quitar las FAQ libera cupos del top 4 y las FAQ, redactadas como preguntas, "
              "se parecen más a la consulta del cliente, pero en estos datos ese efecto no se tradujo en diferencias de Hit.",
              "", "Nota: FAQ09 también repite el plazo y las condiciones de la política (gold.json acepta ambas fuentes "
              "en Q01 y Q07); no entra en este experimento."]

    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "chunking_baseline.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (RESULTS_DIR / "chunking_baseline.json").write_text(
        json.dumps({"fragmentacion": frag, "solapamiento": overlap, "duplicados_juntos": together},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    for name, r in overlap.items():
        print(f"solapamiento {name:24} Hit@1={r['hit@1']:.2f} Hit@{K}={r[f'hit@{K}']:.2f} MRR={r['mrr']:.2f}")
    print("duplicados juntos en el top 4:", together)
    print("Escrito results/chunking_baseline.md")


if __name__ == "__main__":
    main()
