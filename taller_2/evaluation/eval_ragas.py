"""Métricas RAGAS (versión fijada en requirements.txt).

    python -m evaluation.eval_ragas                 # (a) métricas por ids de fragmentos: sin LLM, sin API
    python -m evaluation.eval_ragas --ragas-juez    # (b) además Faithfulness y Response Relevancy con juez (Groq)

(b) pasa a RAGAS EXPLÍCITAMENTE el modelo de Groq (envuelto para LangChain) y los embeddings E5 locales:
no se usan los valores por defecto de la librería ni otras claves de API. Limitación: el mismo
modelo genera las respuestas y las juzga, lo que puede favorecerlas.
"""
import os

os.environ.setdefault("RAGAS_DO_NOT_TRACK", "true")  # RAGAS enviaría telemetría anónima por defecto

import argparse
import datetime
import json
import re
import time
from collections import defaultdict

import numpy as np

from evaluation.metrics import load_gold
from src.config import GROQ_DEFAULT_MODEL, K, LLM_MODEL, LLM_PAUSE_S, RESULTS_DIR
from src.retriever import retrieve

JUDGE_IDS = ["Q05", "Q08", "Q10", "Q13", "Q14", "Q17", "Q19", "Q20", "Q22", "Q26"]  # 10 preguntas de RAG


def ids_metrics() -> dict:
    """(a) Precisión y exhaustividad del contexto basadas en ids (sin LLM)."""
    from ragas.dataset_schema import SingleTurnSample
    from ragas.metrics import IDBasedContextPrecision, IDBasedContextRecall

    precision, recall = IDBasedContextPrecision(), IDBasedContextRecall()
    per_question, by_type = [], defaultdict(list)
    for q in load_gold("in"):
        sample = SingleTurnSample(
            retrieved_context_ids=[d.metadata["chunk_id"] for d, _ in retrieve(q["pregunta"], K)],
            reference_context_ids=q["fuentes_esperadas"])
        p, r = precision.single_turn_score(sample), recall.single_turn_score(sample)
        per_question.append({"id": q["id"], "precision": p, "recall": r})
        by_type[q["fuentes_esperadas"][0].split("::")[0]].append((p, r))
    summary = {"total": (np.mean([x["precision"] for x in per_question]), np.mean([x["recall"] for x in per_question]))}
    summary.update({t: (np.mean([p for p, _ in v]), np.mean([r for _, r in v])) for t, v in by_type.items()})
    return {"resumen": {k: {"precision": float(p), "recall": float(r)} for k, (p, r) in summary.items()},
            "por_pregunta": per_question}


def judge_metrics(pause: float) -> dict | None:
    """(b) Faithfulness y Response Relevancy con Groq como juez. Devuelve None si no hay clave de Groq."""
    from src.llm import USAGE, describe, resolve_provider
    provider, model = resolve_provider()
    if provider != "groq":
        print("--ragas-juez necesita GROQ_API_KEY (proveedor groq); no se ejecuta con el modelo local.")
        return None

    from ragas import evaluate
    from ragas.dataset_schema import EvaluationDataset, SingleTurnSample
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import Faithfulness, ResponseRelevancy
    from ragas.run_config import RunConfig

    from src import app, rag_chain
    from src.embeddings import E5Embeddings
    from src.llm import _build_chat

    # Modelos explícitos: Groq (con reintentos del SDK ante 429) y E5 local. Nada de valores por defecto.
    judge = LangchainLLMWrapper(_build_chat(model, max_retries=3))
    embeddings = LangchainEmbeddingsWrapper(E5Embeddings())
    # strictness=1: por defecto RAGAS pide 3 preguntas por respuesta con n=3 y Groq solo admite n=1 (error 400).
    # Con 1 el puntaje de Response Relevancy es más ruidoso (promedia una sola pregunta generada).
    metrics = [Faithfulness(llm=judge), ResponseRelevancy(llm=judge, embeddings=embeddings, strictness=1)]
    run_config = RunConfig(max_workers=1, timeout=180, max_retries=3)  # 1 a la vez: el límite es de tokens/min

    questions = [q for q in load_gold("in") if q["id"] in JUDGE_IDS]
    rows = []
    for i, q in enumerate(questions):
        docs = app._retriever().invoke(q["pregunta"])
        answer = app.answer_rag(q["pregunta"])
        # RAGAS juzga el texto de la respuesta: se quita la cita de fuentes, que no es una afirmación
        clean = re.sub(r"\(Fuentes?:[^)]*\)", "", rag_chain.to_plain_text(answer)).strip()
        sample = SingleTurnSample(user_input=q["pregunta"], response=clean,
                                  retrieved_contexts=[d.page_content for d in docs])
        result = evaluate(EvaluationDataset(samples=[sample]), metrics=metrics, llm=judge, embeddings=embeddings,
                          run_config=run_config, show_progress=False, raise_exceptions=False)
        scores = result.scores[0]
        rows.append({"id": q["id"], "pregunta": q["pregunta"], "respuesta": clean,
                     "faithfulness": scores.get("faithfulness"), "response_relevancy": scores.get("answer_relevancy")})
        print(f"{q['id']} faithfulness={scores.get('faithfulness')} relevancy={scores.get('answer_relevancy')}")
        if i < len(questions) - 1:
            time.sleep(pause)  # ~4.000 tokens por pregunta: con 8.000 tokens/min hace falta espaciar
    mean = lambda key: float(np.nanmean([r[key] if r[key] is not None else np.nan for r in rows]))
    return {"modelo": describe(), "fecha": datetime.date.today().isoformat(), "pausa_s": pause, "filas": rows,
            "faithfulness_media": mean("faithfulness"), "response_relevancy_media": mean("response_relevancy"),
            "tokens_llm_del_chat": {"entrada": USAGE["input_tokens"], "salida": USAGE["output_tokens"]}}


def write_ids(res: dict) -> None:
    lines = [f"# RAGAS — métricas por ids de fragmentos (k={K}, sin LLM)", "",
             "| Grupo | Precisión del contexto | Exhaustividad del contexto |", "|---|---|---|"]
    lines += [f"| {g} | {v['precision']:.2f} | {v['recall']:.2f} |" for g, v in res["resumen"].items()]
    lines += ["", "Cómo leerlo: cada pregunta tiene 1 o 2 fragmentos de referencia y se recuperan 4, así que la precisión "
              "máxima posible es 0,25 (una referencia) o 0,5 (dos): un valor bajo no indica mala recuperación. Cuando "
              "hay dos fuentes válidas por la redundancia FAQ/envíos (p. ej. `faq::FAQ02` y `envios::costos-de-envio`), "
              "la exhaustividad por ids exige recuperar ambas, mientras que Hit@4 acepta cualquiera; por eso la "
              "exhaustividad es menor que Hit@4.", ""]
    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "ragas_ids.md").write_text("\n".join(lines), encoding="utf-8")
    (RESULTS_DIR / "ragas_ids.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")


def write_judge(res: dict) -> None:
    slug = re.sub(r"[^a-z0-9.-]+", "_", res["modelo"].lower())
    lines = [f"# RAGAS — LLM juez — {res['modelo']} — {res['fecha']}", "",
             "Juez = el mismo modelo que genera las respuestas (limitación: puede favorecerlas). "
             "LLM y embeddings pasados explícitamente a RAGAS (Groq + E5 local).", "",
             f"Faithfulness media: **{res['faithfulness_media']:.2f}** | Response Relevancy media: "
             f"**{res['response_relevancy_media']:.2f}** ({len(res['filas'])} preguntas)", "",
             "| Id | Faithfulness | Response Relevancy |", "|---|---|---|"]
    fmt = lambda x: "n/d" if x is None or x != x else f"{x:.2f}"
    lines += [f"| {r['id']} | {fmt(r['faithfulness'])} | {fmt(r['response_relevancy'])} |" for r in res["filas"]]
    lines += ["", "## Respuestas juzgadas", ""] + [f"- **{r['id']}** {r['pregunta']}\n  {r['respuesta']}" for r in res["filas"]]
    stem = f"ragas_juez_{slug}_{res['fecha']}"
    (RESULTS_DIR / f"{stem}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (RESULTS_DIR / f"{stem}.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Escrito results/{stem}.md")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ragas-juez", action="store_true", help="añade Faithfulness y Response Relevancy (usa la API de Groq)")
    parser.add_argument("--pausa", type=float, default=max(LLM_PAUSE_S, 45.0), help="segundos entre preguntas del juez")
    args = parser.parse_args()

    ids = ids_metrics()
    write_ids(ids)
    t = ids["resumen"]["total"]
    print(f"RAGAS por ids (k={K}, 29 preguntas): precisión={t['precision']:.2f} exhaustividad={t['recall']:.2f} -> results/ragas_ids.md")
    if args.ragas_juez:
        judged = judge_metrics(args.pausa)
        if judged:
            write_judge(judged)


if __name__ == "__main__":
    main()
