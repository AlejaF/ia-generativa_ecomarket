"""Evaluación de la fragmentación: conteos, longitudes y results/chunks.md (sin LLM)."""
import json
from collections import defaultdict

from src.chunking import load_chunks
from src.config import GOLD_PATH, RESULTS_DIR


def check_gold(chunks) -> list[str]:
    """Comprueba que los ids y frases de gold.json existen en los fragmentos generados."""
    by_id = {c.metadata["chunk_id"]: c.page_content for c in chunks}
    problems = []
    for q in json.loads(GOLD_PATH.read_text(encoding="utf-8")):
        if q["tipo"] != "in":
            continue
        missing = [i for i in q["fuentes_esperadas"] if i not in by_id]
        if missing:
            problems.append(f"{q['id']}: ids inexistentes {missing}")
            continue
        text = " ".join(by_id[i] for i in q["fuentes_esperadas"])
        if not any(k in text for k in q["texto_clave"]):
            problems.append(f"{q['id']}: ninguna texto_clave aparece en {q['fuentes_esperadas']}")
    return problems


def main() -> None:
    chunks = load_chunks()
    lengths = defaultdict(list)
    for c in chunks:
        lengths[c.metadata["doc_type"]].append(len(c.page_content))

    lines = ["# Fragmentos (estrategia por estructura)", "",
             "| Documento | Fragmentos | Longitud media | Más corto | Más largo |", "|---|---|---|---|---|"]
    print(f"{'doc':10} {'n':>3} {'media':>6} {'min':>4} {'max':>4}")
    for doc_type, ls in lengths.items():
        mean = sum(ls) / len(ls)
        lines.append(f"| {doc_type} | {len(ls)} | {mean:.0f} | {min(ls)} | {max(ls)} |")
        print(f"{doc_type:10} {len(ls):>3} {mean:>6.0f} {min(ls):>4} {max(ls):>4}")
    lines.append(f"| **total** | **{len(chunks)}** | | | |")
    print(f"total: {len(chunks)} fragmentos")

    problems = check_gold(chunks)
    print("gold.json vs fragmentos:", "OK" if not problems else problems)

    lines += ["", "## Todos los fragmentos", ""]
    for c in chunks:
        lines += [f"### `{c.metadata['chunk_id']}` ({len(c.page_content)} caracteres)", "", "```text",
                  c.page_content, "```", ""]
    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "chunks.md").write_text("\n".join(lines), encoding="utf-8")
    print("Escrito results/chunks.md")


if __name__ == "__main__":
    main()
