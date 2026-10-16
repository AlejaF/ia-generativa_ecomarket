"""Evaluación de los embeddings (sin LLM, sin API):
1. ¿Las paráfrasis se parecen más entre sí que las preguntas sin relación?
2. Efecto de los prefijos E5 ('query: ' / 'passage: ') en la recuperación.
"""
import json

import numpy as np

from evaluation.metrics import embed_docs, hit_rank, load_gold, summarize, top_k
from src.chunking import load_chunks
from src.config import K, RESULTS_DIR
from src.embeddings import E5Embeddings

# Pares de paráfrasis escritos para esta evaluación (mismo significado, palabras distintas)
PARAPHRASES = [
    ("¿Cuánto cuesta el envío?", "¿Qué precio tiene el despacho de mi compra?"),
    ("¿Puedo devolver un producto?", "¿Aceptan devoluciones de artículos?"),
    ("¿Qué medios de pago aceptan?", "¿Con qué formas de pago puedo comprar?"),
    ("¿Cómo rastreo mi pedido?", "¿Dónde puedo ver el seguimiento de mi compra?"),
    ("¿Hacen envíos al exterior?", "¿Envían a otros países?"),
    ("¿A qué hora atiende el servicio al cliente?", "¿Cuál es el horario de atención?"),
]


def paraphrase_gap(emb: E5Embeddings) -> tuple[float, float]:
    """Similitud media de las paráfrasis y de pares sin relación (A_i con la paráfrasis del par siguiente)."""
    a = np.array([emb.embed_query(p[0]) for p in PARAPHRASES])
    b = np.array([emb.embed_query(p[1]) for p in PARAPHRASES])
    related = (a * b).sum(axis=1).mean()
    unrelated = (a * np.roll(b, -1, axis=0)).sum(axis=1).mean()
    return float(related), float(unrelated)


def retrieval_metrics(emb: E5Embeddings, chunks, vecs=None) -> dict:
    vecs = embed_docs(chunks, emb) if vecs is None else vecs
    ranks, top1 = [], []
    for q in load_gold("in"):
        found = top_k(chunks, vecs, emb.embed_query(q["pregunta"]), K)
        ranks.append(hit_rank([d for d, _ in found], q))
        top1.append(found[0][1])
    return {**summarize(ranks, K), "puntaje_top1_medio": float(np.mean(top1))}


def relevancy_scale(emb: E5Embeddings) -> dict:
    """Escala de la métrica Response Relevancy de RAGAS con estos embeddings.

    RAGAS compara la pregunta original con `embed_query` (prefijo 'query: ') y las preguntas que genera el
    LLM a partir de la respuesta con `embed_documents` (prefijo 'passage: '): mezcla los dos prefijos.
    Aquí se mide el techo (la misma pregunta), las paráfrasis y el suelo (preguntas sin relación) en ese modo
    mezclado y en el simétrico (query vs query)."""
    from evaluation.eval_ragas import JUDGE_IDS  # las 10 preguntas que juzga RAGAS

    emb.use_prefixes = True
    q = lambda t: np.array(emb.embed_query(t))             # 'query: ...'
    p = lambda t: np.array(emb.embed_documents([t])[0])    # 'passage: ...'
    gold = {x["id"]: x["pregunta"] for x in load_gold()}
    judged = [gold[i] for i in JUDGE_IDS]
    easy = [x["pregunta"] for x in load_gold("ooc_facil")]
    a, b = [x[0] for x in PARAPHRASES], [x[1] for x in PARAPHRASES]

    def cross(xs, ys, second):  # similitud media entre todas las parejas distintas
        return float(np.mean([q(x) @ second(y) for x in xs for y in ys if x != y]))

    out = {}
    for name, second in (("mezclado (como RAGAS)", p), ("simétrico (query vs query)", q)):
        out[name] = {
            "misma pregunta (techo)": float(np.mean([q(x) @ second(x) for x in judged])),
            "paráfrasis": float(np.mean([q(x) @ second(y) for x, y in zip(a, b)])),
            "suelo, mismo dominio": cross(judged, judged, second),
            "suelo, fuera de dominio": cross(judged, easy, second),
        }
    return out


def main() -> None:
    chunks = load_chunks()
    emb = E5Embeddings(use_prefixes=True)
    results = {}
    for name, prefixes in (("con prefijos", True), ("sin prefijos", False)):
        emb.use_prefixes = prefixes  # el mismo modelo, con y sin prefijos
        related, unrelated = paraphrase_gap(emb)
        results[name] = {"paráfrasis": related, "sin relación": unrelated, "brecha": related - unrelated,
                         **retrieval_metrics(emb, chunks)}

    lines = ["# Embeddings (multilingual-e5-small)", "",
             f"Paráfrasis: {len(PARAPHRASES)} pares escritos a mano. 'Sin relación' = cada pregunta con la "
             "paráfrasis de otro par. Recuperación: 29 preguntas 'in', k=4, índice en memoria.", "",
             f"| Configuración | Sim. paráfrasis | Sim. sin relación | Brecha | Hit@1 | Hit@{K} | MRR | Puntaje top-1 medio |",
             "|---|---|---|---|---|---|---|---|"]
    for name, r in results.items():
        lines.append(f"| {name} | {r['paráfrasis']:.3f} | {r['sin relación']:.3f} | {r['brecha']:.3f} | "
                     f"{r['hit@1']:.2f} | {r[f'hit@{K}']:.2f} | {r['mrr']:.2f} | {r['puntaje_top1_medio']:.3f} |")
        print(f"{name:13} paráfrasis={r['paráfrasis']:.3f} sin relación={r['sin relación']:.3f} "
              f"Hit@1={r['hit@1']:.2f} Hit@{K}={r[f'hit@{K}']:.2f} MRR={r['mrr']:.2f}")
    scale = relevancy_scale(emb)
    results["escala_response_relevancy"] = scale
    lines += ["", "## Escala de Response Relevancy (RAGAS) con estos embeddings", "",
              "RAGAS compara la pregunta original (`query:`) con las preguntas generadas desde la respuesta (`passage:`). "
              "Similitud coseno media de las 10 preguntas evaluadas:", "",
              "| Modo | Misma pregunta (techo) | Paráfrasis | Suelo, mismo dominio | Suelo, fuera de dominio |", "|---|---|---|---|---|"]
    for name, v in scale.items():
        lines.append(f"| {name} | {v['misma pregunta (techo)']:.3f} | {v['paráfrasis']:.3f} | "
                     f"{v['suelo, mismo dominio']:.3f} | {v['suelo, fuera de dominio']:.3f} |")
        print(f"escala RR {name:27} techo={v['misma pregunta (techo)']:.3f} paráfrasis={v['paráfrasis']:.3f} "
              f"suelo dominio={v['suelo, mismo dominio']:.3f} fuera={v['suelo, fuera de dominio']:.3f}")
    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "embeddings.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (RESULTS_DIR / "embeddings.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Escrito results/embeddings.md")


if __name__ == "__main__":
    main()
