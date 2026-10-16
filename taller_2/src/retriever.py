"""Acceso a la base vectorial Chroma y recuperación de fragmentos."""
import logging

from langchain_chroma import Chroma
from langchain_core.documents import Document

from src.config import CHROMA_DIR, COLLECTION_NAME, K, RELEVANCE_THRESHOLD
from src.embeddings import E5Embeddings

# Cuando ningún fragmento supera el umbral es un caso normal (el chat responde con el mensaje fijo);
# LangChain lo registra como advertencia en inglés, que aquí solo confunde.
logging.getLogger("langchain_core.vectorstores.base").setLevel(logging.ERROR)


def get_store(embeddings: E5Embeddings | None = None) -> Chroma:
    # hnsw:space=cosine: la distancia de Chroma es 1 - coseno (por defecto sería L2)
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings or E5Embeddings(),
        persist_directory=str(CHROMA_DIR),
        collection_metadata={"hnsw:space": "cosine"},
    )


def retrieve(question: str, k: int = K, store: Chroma | None = None,
             doc_type: str | None = None) -> list[tuple[Document, float]]:
    """Los k fragmentos más parecidos con su puntaje (similitud coseno, mayor = más relevante).
    NO aplica el umbral: sirve para calibrarlo y para las evaluaciones. `doc_type` limita la
    búsqueda a un tipo de documento (p. ej. 'politica' en el flujo de devoluciones)."""
    store = store or get_store()
    where = {"doc_type": doc_type} if doc_type else None
    return store.similarity_search_with_relevance_scores(question, k=k, filter=where)


def get_chunks(chunk_ids: list[str], store: Chroma | None = None) -> list[Document]:
    """Fragmentos por id exacto (sin búsqueda). Sirve para añadir al prompt secciones que
    siempre hacen falta, como los pasos de la devolución (politica::7)."""
    if not chunk_ids:  # sin ids no hay nada que pedir (y se evita que Chroma trate la lista vacía como «sin filtro»)
        return []
    store = store or get_store()
    found = store.get(ids=chunk_ids)
    return [Document(page_content=text, metadata=meta) for text, meta in zip(found["documents"], found["metadatas"])]


def get_retriever(store: Chroma | None = None):
    """Recuperador nativo de LangChain que sí descarta lo que no supera el umbral (lo usa el chat)."""
    store = store or get_store()
    return store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": K, "score_threshold": RELEVANCE_THRESHOLD},
    )
