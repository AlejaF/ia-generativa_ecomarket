"""Calibra RELEVANCE_THRESHOLD con los puntajes de las preguntas de gold.json (sin LLM).

Se usa el puntaje del MEJOR fragmento de cada pregunta ('top1'): el sistema responde si ese
puntaje alcanza el umbral. Se propone el punto medio entre el peor 'in' y el mejor 'ooc_facil'.
Las 'ooc_dificil' (cercanas al dominio) se esperan como límite: las cubre el prompt, no el umbral.
"""
import json

from evaluation.metrics import load_gold
from src.config import RELEVANCE_THRESHOLD, RESULTS_DIR
from src.retriever import get_store, retrieve

TIPOS = ["in", "ooc_facil", "ooc_dificil"]


def errors_at(threshold: float, top1: dict[str, list[float]]) -> dict:
    return {
        "falsos_rechazados_in": sum(s < threshold for s in top1["in"]),
        "falsos_aceptados_ooc_facil": sum(s >= threshold for s in top1["ooc_facil"]),
        "falsos_aceptados_ooc_dificil": sum(s >= threshold for s in top1["ooc_dificil"]),
    }


def main() -> None:
    store = get_store()
    top1 = {t: [] for t in TIPOS}
    detail = []
    for q in load_gold():
        score = retrieve(q["pregunta"], 1, store)[0][1]
        top1[q["tipo"]].append(score)
        detail.append((q["tipo"], score, q["id"], q["pregunta"]))

    low_in, high_easy = min(top1["in"]), max(top1["ooc_facil"])
    proposed = round((low_in + high_easy) / 2, 3)
    separable = high_easy < low_in  # si no, ningún umbral separa 'in' de 'ooc_facil'

    lines = ["# Calibración del umbral de relevancia", "",
             "Puntaje = similitud coseno del mejor fragmento (1 − distancia de Chroma).", "",
             "| Tipo | n | mínimo | media | máximo |", "|---|---|---|---|---|"]
    for t in TIPOS:
        s = top1[t]
        lines.append(f"| {t} | {len(s)} | {min(s):.3f} | {sum(s) / len(s):.3f} | {max(s):.3f} |")
        print(f"{t:12} n={len(s):>2} min={min(s):.3f} media={sum(s) / len(s):.3f} max={max(s):.3f}")
    print(f"separable in/ooc_facil: {separable}  -> umbral propuesto {proposed}")

    lines += ["", f"Separables (máx. ooc_facil {high_easy:.3f} < mín. in {low_in:.3f}): **{separable}**",
              f"Umbral propuesto (punto medio): **{proposed}**", "",
              "| Umbral | Falsos rechazados (in) | Falsos aceptados (ooc_facil) | Falsos aceptados (ooc_dificil) |",
              "|---|---|---|---|"]
    candidates = sorted({proposed, round(RELEVANCE_THRESHOLD, 3), round(low_in, 3), round(high_easy, 3)})
    for th in candidates:
        e = errors_at(th, top1)
        lines.append(f"| {th} | {e['falsos_rechazados_in']}/{len(top1['in'])} | "
                     f"{e['falsos_aceptados_ooc_facil']}/{len(top1['ooc_facil'])} | "
                     f"{e['falsos_aceptados_ooc_dificil']}/{len(top1['ooc_dificil'])} |")
    lines += ["", "## Puntaje por pregunta (de mayor a menor dentro de cada tipo)", ""]
    for t in TIPOS:
        lines.append(f"**{t}**")
        lines += [f"- {s:.3f} {i}: {p}" for tt, s, i, p in sorted(detail, reverse=True) if tt == t]
        lines.append("")

    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "threshold.md").write_text("\n".join(lines), encoding="utf-8")
    (RESULTS_DIR / "threshold.json").write_text(
        json.dumps({"propuesto": proposed, "separable": separable, "top1": top1}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    print("Escrito results/threshold.md")


if __name__ == "__main__":
    main()
