"""Funciones compartidas por las evaluaciones de recuperación."""
import json

import numpy as np

from src.config import GOLD_PATH


def load_gold(tipo: str | None = None) -> list[dict]:
    gold = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
    return [q for q in gold if tipo is None or q["tipo"] == tipo]


def hit_rank(retrieved: list, q: dict, by_text: bool = False) -> int | None:
    """Posición (1 = primera) del primer fragmento correcto entre los recuperados, o None.

    Por defecto compara chunk_id. Con by_text=True busca alguna texto_clave en el texto
    recuperado, lo que permite comparar fragmentaciones con ids distintos."""
    for pos, doc in enumerate(retrieved, start=1):
        if by_text:
            if any(k in doc.page_content for k in q["texto_clave"]):
                return pos
        elif doc.metadata["chunk_id"] in q["fuentes_esperadas"]:
            return pos
    return None


def summarize(ranks: list[int | None], k: int = 4) -> dict:
    """Hit@1, Hit@k y MRR a partir de las posiciones del primer acierto."""
    n = len(ranks)
    return {
        "n": n,
        "hit@1": sum(r == 1 for r in ranks) / n,
        f"hit@{k}": sum(r is not None and r <= k for r in ranks) / n,
        "mrr": sum(1 / r for r in ranks if r) / n,
    }


# ---------- Índice en memoria (para comparar variantes sin tocar chroma_db/) ----------

def embed_docs(docs: list, embeddings) -> np.ndarray:
    """Matriz (n_docs, dim) de vectores normalizados, de modo que producto punto = coseno."""
    return np.array(embeddings.embed_documents([d.page_content for d in docs]))


def top_k(docs: list, doc_vecs: np.ndarray, query_vec: list[float], k: int = 4) -> list[tuple]:
    """Los k documentos más cercanos a la consulta, con su puntaje coseno."""
    scores = doc_vecs @ np.array(query_vec)
    return [(docs[i], float(scores[i])) for i in np.argsort(-scores)[:k]]
