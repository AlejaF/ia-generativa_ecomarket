"""Hit@1, Hit@4 y MRR de la recuperación sobre las preguntas 'in' de gold.json (sin LLM)."""
import json
from collections import defaultdict

from evaluation.metrics import hit_rank, load_gold, summarize
from src.config import K, RESULTS_DIR
from src.retriever import retrieve, get_store


def main() -> None:
    store = get_store()
    ranks, by_type, misses = [], defaultdict(list), []
    for q in load_gold("in"):
        docs = [d for d, _ in retrieve(q["pregunta"], K, store)]
        r = hit_rank(docs, q)
        ranks.append(r)
        # El tipo de documento es el de la primera fuente esperada (p. ej. 'faq' en 'faq::FAQ09')
        by_type[q["fuentes_esperadas"][0].split("::")[0]].append(r)
        if r != 1:
            misses.append({"id": q["id"], "pregunta": q["pregunta"], "esperadas": q["fuentes_esperadas"],
                           "posicion": r, "recuperados": [d.metadata["chunk_id"] for d in docs]})

    total = summarize(ranks, K)
    rows = {"total": total, **{t: summarize(rs, K) for t, rs in by_type.items()}}
    lines = [f"# Recuperación (k={K}, {total['n']} preguntas 'in')", "",
             f"| Grupo | n | Hit@1 | Hit@{K} | MRR |", "|---|---|---|---|---|"]
    for name, m in rows.items():
        lines.append(f"| {name} | {m['n']} | {m['hit@1']:.2f} | {m[f'hit@{K}']:.2f} | {m['mrr']:.2f} |")
        print(f"{name:10} n={m['n']:>2} Hit@1={m['hit@1']:.2f} Hit@{K}={m[f'hit@{K}']:.2f} MRR={m['mrr']:.2f}")
    lines += ["", "Grupo = tipo de documento de la primera fuente esperada.", "",
              "## Preguntas sin acierto en la posición 1", ""]
    lines += [f"- {m['id']} «{m['pregunta']}»: esperadas {m['esperadas']}, posición {m['posicion']}, "
              f"recuperados {m['recuperados']}" for m in misses]

    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "retrieval.md").write_text("\n".join(lines), encoding="utf-8")
    (RESULTS_DIR / "retrieval.json").write_text(json.dumps({"metricas": rows, "fallos": misses},
                                                           ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(misses)} preguntas sin acierto en la posición 1. Escrito results/retrieval.md")


if __name__ == "__main__":
    main()
