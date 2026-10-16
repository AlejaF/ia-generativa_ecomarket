"""Ejecuta toda la evaluación y guarda un resumen con el modelo y la fecha en results/.

    python -m evaluation.run_all                 # pasos sin LLM + pasos con el generador configurado
    python -m evaluation.run_all --sin-llm       # solo los pasos que no llaman a ningún LLM ni a la API
    python -m evaluation.run_all --con-local     # además, el subconjunto de control con el modelo local
    python -m evaluation.run_all --ragas-juez    # además, las métricas RAGAS con juez (solo con Groq)

Sin LLM (1–4, 6, 7a): fragmentos, embeddings, recuperación, umbral, ablación y RAGAS por ids.
Con el generador configurado: 5 (punta a punta) y, con Groq y --ragas-juez, 7b. Si no hay clave,
5 corre solo el subconjunto pequeño con el modelo local (modo demostrativo, lento).
Cada paso corre en su propio proceso, así un fallo no detiene el resto.
"""
import argparse
import datetime
import os
import re
import subprocess
import sys
import time

from src.config import RESULTS_DIR, ROOT
from src.llm import LLMError, describe, resolve_provider

NO_LLM_STEPS = [
    ("1  fragmentos", ["-m", "evaluation.eval_chunks"]),
    ("2  embeddings", ["-m", "evaluation.eval_embeddings"]),
    ("3  recuperación", ["-m", "evaluation.eval_retrieval"]),
    ("4  umbral", ["-m", "evaluation.calibrate_threshold"]),
    ("6  fragmentación y solapamiento", ["-m", "evaluation.eval_chunking_baseline"]),
    ("7a RAGAS por ids", ["-m", "evaluation.eval_ragas"]),
]
NOISE = re.compile(r"warn|symlink|Loading weights|HF_|developer mode|order to activate|^\s*$", re.I)


def run_step(name: str, args: list[str]) -> dict:
    print(f"\n== {name} ==", flush=True)
    start = time.time()
    proc = subprocess.run([sys.executable, "-W", "ignore", *args], cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    lines = [l for l in (proc.stdout + proc.stderr).splitlines() if not NOISE.search(l)]
    result = {"paso": name, "ok": proc.returncode == 0, "segundos": round(time.time() - start, 1), "salida": lines}
    print("\n".join(lines[-12:]) if proc.returncode else "\n".join(lines), flush=True)
    print(f"-> {'ok' if result['ok'] else 'FALLÓ'} ({result['segundos']} s)", flush=True)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sin-llm", action="store_true")
    parser.add_argument("--con-local", action="store_true")
    parser.add_argument("--ragas-juez", action="store_true")
    args = parser.parse_args()

    try:
        provider, _ = resolve_provider()
        model = describe()
    except LLMError as e:
        raise SystemExit(str(e))
    results = [run_step(name, a) for name, a in NO_LLM_STEPS]

    if not args.sin_llm:
        if provider == "groq":
            results.append(run_step("5  punta a punta (Groq)", ["-m", "evaluation.eval_end_to_end"]))
            results.append(run_step("8  experimentos de modificación (Groq)", ["-m", "evaluation.eval_modificaciones"]))
            if args.ragas_juez:
                results.append(run_step("7b RAGAS con juez (Groq)", ["-m", "evaluation.eval_ragas", "--ragas-juez"]))
            if args.con_local:
                results.append(run_step("5  grupo de control (modelo local)", ["-m", "evaluation.eval_end_to_end", "--local"]))
        else:
            print("\nSin GROQ_API_KEY: modo demostrativo. Se corre solo el subconjunto pequeño con el modelo local "
                  "(lento); 7b no se ejecuta.")
            results.append(run_step("5  grupo de control (modelo local)", ["-m", "evaluation.eval_end_to_end", "--local"]))

    today = datetime.date.today().isoformat()
    lines = [f"# Ejecución completa — {model} — {today}", "", "| Paso | Resultado | Segundos |", "|---|---|---|"]
    lines += [f"| {r['paso']} | {'ok' if r['ok'] else 'FALLÓ'} | {r['segundos']} |" for r in results]
    for r in results:
        lines += ["", f"## {r['paso']}", "", "```text", *r["salida"], "```"]
    slug = re.sub(r"[^a-z0-9.-]+", "_", model.lower())
    RESULTS_DIR.mkdir(exist_ok=True)
    path = RESULTS_DIR / f"run_all_{slug}_{today}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    failed = [r["paso"] for r in results if not r["ok"]]
    print(f"\nResumen en results/{path.name}" + (f" | pasos con fallo: {failed}" if failed else " | todos los pasos ok"))


if __name__ == "__main__":
    main()
