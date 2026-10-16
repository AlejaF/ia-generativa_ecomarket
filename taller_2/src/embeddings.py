"""Embeddings E5 compatibles con LangChain.

Los modelos E5 se entrenaron con prefijos: "passage: " para los textos que se indexan y
"query: " para las preguntas. Sin ellos la recuperación empeora, por eso los añadimos aquí
y no en el resto del código. `use_prefixes=False` sirve para medir ese efecto en la evaluación.
"""
from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer

from src.config import EMBEDDING_MODEL


class E5Embeddings(Embeddings):
    def __init__(self, model_name: str = EMBEDDING_MODEL, use_prefixes: bool = True):
        # `client` (y no `model`): RAGAS lee `.model` esperando el NOMBRE del modelo, como texto
        self.client = SentenceTransformer(model_name, device="cpu")
        self.use_prefixes = use_prefixes

    def _encode(self, texts: list[str]) -> list[list[float]]:
        # normalize_embeddings=True: vectores de norma 1, así el producto punto es el coseno
        vectors = self.client.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return vectors.tolist()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if self.use_prefixes:
            texts = ["passage: " + t for t in texts]
        return self._encode(texts)

    def embed_query(self, text: str) -> list[float]:
        if self.use_prefixes:
            text = "query: " + text
        return self._encode([text])[0]
