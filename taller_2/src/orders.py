"""Consulta exacta de pedidos por número de seguimiento (no se usa búsqueda por similitud)."""
import json
import re

from src.config import DATA_DIR

TRACKING_RE = re.compile(r"\bECM\d{5}\b", re.IGNORECASE)


def extract_tracking(text: str) -> str | None:
    """Primer número de seguimiento que aparezca en el texto, en mayúsculas, o None."""
    m = TRACKING_RE.search(text)
    return m.group(0).upper() if m else None


def find_order(tracking_number: str) -> dict | None:
    """Registro del pedido SIN el campo `customer` (minimización de datos: el LLM no lo necesita)."""
    # Se lee en cada llamada: son 16 registros y así un cambio en el JSON se ve sin reiniciar
    orders = json.loads((DATA_DIR / "pedidos.json").read_text(encoding="utf-8"))
    for order in orders:
        if order["tracking_number"] == tracking_number.upper():
            return {k: v for k, v in order.items() if k != "customer"}
    return None
