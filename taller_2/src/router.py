"""Enrutador por reglas (no LLM): rápido, predecible y fácil de auditar."""
import re

from src.orders import TRACKING_RE

RETURN_RE = re.compile(r"devol|reembols|reintegr", re.IGNORECASE)


def route(text: str) -> str:
    """'order' | 'return' | 'rag'. El número de pedido tiene prioridad sobre la palabra devolución."""
    if TRACKING_RE.search(text):
        return "order"
    if RETURN_RE.search(text):
        return "return"
    return "rag"
