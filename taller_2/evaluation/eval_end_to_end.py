"""Evaluación de punta a punta con el LLM: sin RAG / con RAG / con RAG + reglas.

    python -m evaluation.eval_end_to_end            # generador configurado (Groq si hay clave)
    python -m evaluation.eval_end_to_end --local    # grupo de control: subconjunto pequeño con el modelo local

Con Groq se pausa LLM_PAUSE_S segundos entre llamadas (límites de la cuenta: 8.000 tokens/min y
200.000/día) y se registran los tokens. Con el modelo local no se corren todas las preguntas: solo
un subconjunto, y se mide el tiempo de cada generación.
Las marcas «ok» son heurísticas (regex): las respuestas completas están en el reporte para revisarlas.
"""
import os
import sys

if "--local" in sys.argv:  # debe fijarse ANTES de importar src.*, que lee LLM_PROVIDER al importarse
    os.environ["LLM_PROVIDER"] = "local"

import datetime
import json
import re
import time

from src import app, rag_chain
from src.config import LLM_PAUSE_S, RESULTS_DIR
from src.llm import USAGE, LLMError, describe
from src.router import route

NEGATIVE = re.compile(r"rechaz|no (se )?(puede|puedo|podemos|es posible|procede|cumple|aceptamos)|lo siento|lamento|fuera del plazo", re.I)
POSITIVE = re.compile(r"acept|aprobad|es posible|puedes devolver|procede|claro|podemos ayudarte|s[ií],? puedes", re.I)


ASKS_DATA = re.compile(r"sin más información|por favor,? (dime|indícame|cuéntame)|necesito (que|saber|más)|¿cuánto tiempo", re.I)


VALID = re.compile(r"(?<!no )es v[aá]lida", re.I)  # «es válida», pero no «no es válida»


def verdict_of(answer: str) -> str:
    """Heurística: 'pide_datos' si pregunta en vez de decidir; 'rechazada' si dice «rechaz…» o hay una marca
    negativa; 'aceptada' si solo hay positivas. Un «es válida» sin «rechaz» cuenta como aceptación aunque más
    adelante mencione condiciones en abstracto («si no cumple con estas condiciones…»)."""
    if ASKS_DATA.search(answer):
        return "pide_datos"
    if "rechaz" in answer.lower():
        return "rechazada"
    if VALID.search(answer):
        return "aceptada"
    if NEGATIVE.search(answer):
        return "rechazada"
    return "aceptada" if POSITIVE.search(answer) else "indeterminado"


def refuses(answer: str) -> bool:
    return "no cuento con las herramientas" in answer.lower()


# (id, tipo, pregunta, comprobación heurística de la respuesta, descripción de lo esperado)
CASES = [
    ("Q08", "rag", "¿Cuánto cuesta el envío estándar?", lambda a: "12.000" in a, "menciona $12.000"),
    ("Q14", "rag", "¿Puedo cancelar mi compra si el pedido ya salió?", lambda a: bool(re.search(r"preparaci", a, re.I)), "solo en preparación"),
    ("Q18", "rag", "¿Puedo pagar cuando me entreguen el pedido?", lambda a: bool(re.search(r"no se ofrece|no (ofrecemos|aceptamos|es posible|se puede)|sin pago contra", a, re.I)),
     "no hay pago contra entrega"),
    ("Q28", "rag", "¿Puedo devolver la taza que tiene mi nombre grabado?", lambda a: verdict_of(a) == "rechazada", "no (personalizado)"),
    ("F03", "ooc", "¿Quién ganó el último mundial de fútbol?", refuses, "mensaje de rechazo"),
    ("D01", "ooc", "¿Venden computadores portátiles?", refuses, "mensaje de rechazo"),
    ("D04", "ooc", "¿Los electrónicos tienen garantía de dos años?", refuses, "mensaje de rechazo"),
    ("R1", "return", "Quiero devolver unos audífonos, los compré hace 10 días, sin usar y con su empaque original",
     lambda a: verdict_of(a) == "aceptada" and "soporte@ecomarket.example" in a,
     "aceptada y con los pasos de la política (escribir a soporte@…)"),
    ("R2", "return", "Quiero devolver mi crema de cuidado personal, está abierta, la recibí hace 5 días",
     lambda a: verdict_of(a) == "rechazada", "rechazada (higiene abierta)"),
    ("R3", "return", "Quiero devolver una camiseta que recibí hace 45 días, sin usar y con su empaque",
     lambda a: verdict_of(a) == "rechazada", "rechazada (45 días)"),
    ("P1", "order", "¿Dónde está mi pedido ECM10004?", lambda a: "Retrasado" in a and "2026-09-28" in a, "Retrasado, 2026-09-28"),
]
LOCAL_SUBSET = {"Q08", "D01", "R1", "R2", "R3"}  # 3 devoluciones, 1 de RAG y 1 fuera de contexto cercana


def measure(fn, *args) -> dict:
    """Ejecuta una respuesta y mide tiempo, llamadas al LLM y tokens (de Groq; el local no los reporta)."""
    before = dict(USAGE)
    start = time.time()
    try:
        answer, error = fn(*args), None
    except LLMError as e:
        answer, error = "", str(e)
    return {"answer": answer, "error": error, "seconds": round(time.time() - start, 1),
            "llm_calls": USAGE["calls"] - before["calls"],
            "tokens_in": USAGE["input_tokens"] - before["input_tokens"],
            "tokens_out": USAGE["output_tokens"] - before["output_tokens"]}


def no_rag(question: str) -> str:
    return rag_chain.to_plain_text(rag_chain.plain_chain().invoke({"question": question}))


def main() -> None:
    local = "--local" in sys.argv
    model = describe()
    pause = 0 if local else LLM_PAUSE_S
    cases = [c for c in CASES if not local or c[0] in LOCAL_SUBSET]
    print(f"Generador: {model} | {len(cases)} preguntas | pausa {pause:.0f} s")

    warmup = None
    if local:  # la primera generación incluye cargar el modelo: se mide aparte
        warmup = measure(no_rag, "Hola")
        print(f"carga del modelo + primera generación: {warmup['seconds']} s")

    rows = []
    for i, (cid, kind, question, check, expected) in enumerate(cases):
        conditions = {"sin_rag": measure(no_rag, question),
                      "con_rag": measure(app.respond, question, False)}
        if route(question) == "return":  # solo en el flujo de devolución cambia algo al activar el verificador
            conditions["con_rag_reglas"] = measure(app.respond, question, True)
        else:
            conditions["con_rag_reglas"] = {**conditions["con_rag"], "reutilizada": True}
        for r in conditions.values():
            r["ok"] = bool(r["answer"]) and bool(check(r["answer"]))
        rows.append({"id": cid, "tipo": kind, "pregunta": question, "esperado": expected, "condiciones": conditions})
        summary = " ".join(f"{k}={'ok' if v['ok'] else 'NO'}({v['seconds']}s)" for k, v in conditions.items())
        print(f"{cid:3} {summary}")
        if pause and i < len(cases) - 1 and any(v["llm_calls"] for v in conditions.values()):
            time.sleep(pause)  # respeta el límite de tokens por minuto de la cuenta

    write_report(model, datetime.date.today().isoformat(), pause, warmup, rows, dict(USAGE), local)


def write_report(model: str, today: str, pause: float, warmup: dict | None, rows: list, usage: dict, local: bool) -> None:
    """Escribe results/end_to_end_<modelo>_<fecha>.md/.json a partir de las filas (nuevas o reevaluadas)."""
    slug = re.sub(r"[^a-z0-9.-]+", "_", model.lower())
    totals = {c: sum(r["condiciones"][c]["ok"] for r in rows) for c in ("sin_rag", "con_rag", "con_rag_reglas")}
    returns = [r for r in rows if route(r["pregunta"]) == "return"]  # incluye Q28, que también pasa por el verificador
    lines = [f"# Evaluación de punta a punta — {model} — {today}", "",
             ("Grupo de control con el modelo local: subconjunto pequeño, sin pausas. " if local else
              f"Pausa de {pause:.0f} s entre preguntas. ") + "Las marcas ok son heurísticas (regex); revisa las respuestas.", ""]
    if warmup:
        lines += [f"Carga del modelo + primera generación: {warmup['seconds']} s.", ""]
    lines += [f"## Aciertos heurísticos ({len(rows)} preguntas)", "", "| Condición | Aciertos |", "|---|---|"]
    lines += [f"| {c} | {n}/{len(rows)} |" for c, n in totals.items()]
    lines += ["", f"Solo devoluciones ({len(returns)}):", ""]
    lines += [f"- {c}: {sum(r['condiciones'][c]['ok'] for r in returns)}/{len(returns)}" for c in totals]
    lines += ["", "En las preguntas que no son devoluciones, «con_rag_reglas» reutiliza «con_rag» (el verificador no interviene).",
              "", "## Detalle", "", "| Id | Condición | ok | Segundos | Llamadas LLM | Tokens (ent./sal.) |", "|---|---|---|---|---|---|"]
    for r in rows:
        for c, v in r["condiciones"].items():
            tokens = f"{v['tokens_in']}/{v['tokens_out']}"
            lines.append(f"| {r['id']} | {c}{' (reutilizada)' if v.get('reutilizada') else ''} | "
                         f"{'sí' if v['ok'] else 'no'} | {v['seconds']} | {v['llm_calls']} | {tokens} |")
    lines += ["", "## Respuestas", ""]
    for r in rows:
        lines += [f"### {r['id']} — {r['pregunta']}", f"Esperado: {r['esperado']}", ""]
        for c, v in r["condiciones"].items():
            text = v["answer"] or f"[sin respuesta] {v['error']}"
            lines += [f"**{c}**", "", "```text", text, "```", ""]
    gens = [v["seconds"] for r in rows for k, v in r["condiciones"].items() if v["llm_calls"] and not v.get("reutilizada")]
    if local and gens:
        lines += [f"Tiempo por generación con el modelo local: mediana {sorted(gens)[len(gens) // 2]} s, "
                  f"mín. {min(gens)} s, máx. {max(gens)} s ({len(gens)} generaciones).", ""]
        print(f"tiempo por generación (local): mediana {sorted(gens)[len(gens) // 2]} s, mín {min(gens)} s, máx {max(gens)} s")
    if not local:
        lines.append(f"Tokens de la sesión: entrada {usage['input_tokens']}, salida {usage['output_tokens']}, llamadas {usage['calls']}.")
        print(f"tokens de la sesión: entrada {usage['input_tokens']}, salida {usage['output_tokens']}, llamadas {usage['calls']}")

    RESULTS_DIR.mkdir(exist_ok=True)
    stem = f"end_to_end_{slug}_{today}"
    (RESULTS_DIR / f"{stem}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (RESULTS_DIR / f"{stem}.json").write_text(json.dumps(
        {"modelo": model, "fecha": today, "pausa_s": pause, "carga_modelo": warmup, "preguntas": rows,
         "usage": usage}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"aciertos: {totals} -> results/{stem}.md")


def reevaluate(path: str) -> None:
    """Recalcula las marcas «ok» de un .json guardado con las comprobaciones actuales, SIN generar nada.
    Uso: python -m evaluation.eval_end_to_end --reevaluar results/end_to_end_<modelo>_<fecha>.json"""
    data = json.loads(open(path, encoding="utf-8").read())
    checks = {c[0]: c[3] for c in CASES}
    changes = []
    for row in data["preguntas"]:
        for name, v in row["condiciones"].items():
            ok = bool(v["answer"]) and bool(checks[row["id"]](v["answer"]))
            if ok != v.get("ok"):
                changes.append(f"{row['id']}/{name}: {'ok' if v.get('ok') else 'NO'} -> {'ok' if ok else 'NO'}")
            v["ok"] = ok
    print("marcas que cambian:", changes or "ninguna")
    write_report(data["modelo"], data["fecha"], data["pausa_s"], data.get("carga_modelo"), data["preguntas"],
                 data["usage"], data["modelo"].startswith("local/"))


if __name__ == "__main__":
    if "--reevaluar" in sys.argv:
        reevaluate(sys.argv[sys.argv.index("--reevaluar") + 1])
    else:
        main()
