"""Falla si las cifras que se repiten entre faqs.json y envios_y_pagos.md (o la política) no coinciden.

Cada entrada: id de la FAQ, dónde se repite el dato y las cifras/frases que deben aparecer en AMBOS textos.
"""
import json
import re

import pytest

from src.config import DATA_DIR

EMAIL = "soporte@ecomarket.example"
OVERLAPS = [
    ("FAQ01", "Métodos y tiempos de envío", ["3 a 5 días hábiles", "1 a 2 días hábiles", "Bogotá, Medellín, Cali y Barranquilla"]),
    ("FAQ01", "Métodos y tiempos de envío", ["hasta 1 día hábil"]),
    ("FAQ02", "Costos de envío", ["$12.000 COP", "$150.000 COP", "$20.000 COP"]),
    ("FAQ03", "Cobertura", ["Colombia"]),
    ("FAQ04", "Estados del pedido", ["ECM", "5 dígitos", "ECM10001"]),
    ("FAQ05", "Estados del pedido", ["En preparación", "En tránsito", "Retrasado", "Entregado"]),
    ("FAQ06", "Pedidos retrasados", ["3 días hábiles", EMAIL]),
    ("FAQ07", "Cancelaciones y cambios de dirección", ["En preparación", "En tránsito"]),
    ("FAQ08", "Cancelaciones y cambios de dirección", ["En preparación", EMAIL]),
    ("FAQ10", "Medios de pago", ["de crédito y débito", "PSE", "Nequi", "al confirmar la compra"]),
    ("FAQ11", "Facturación", ["factura electrónica", "correo con el que se realizó la compra"]),
    ("FAQ14", "Atención al cliente", [EMAIL, "lunes a viernes", "8:00 a. m. a 6:00 p. m.", "24 horas"]),
]


def _sections() -> dict[str, str]:
    text = (DATA_DIR / "envios_y_pagos.md").read_text(encoding="utf-8")
    parts = re.split(r"^## (.+)$", text, flags=re.MULTILINE)
    return dict(zip(parts[1::2], parts[2::2]))


def _faqs() -> dict[str, str]:
    items = json.loads((DATA_DIR / "faqs.json").read_text(encoding="utf-8"))
    return {f["id"]: f["pregunta"] + " " + f["respuesta"] for f in items}


@pytest.mark.parametrize("faq_id,section,tokens", OVERLAPS)
def test_faq_vs_envios(faq_id, section, tokens):
    faq, sec = _faqs()[faq_id], _sections()[section]
    for t in tokens:
        assert t in faq, f"{faq_id} no contiene {t!r}"
        assert t in sec, f"la sección «{section}» no contiene {t!r}"


def test_faq09_vs_politica():
    # FAQ09 repite el plazo y las condiciones de la política
    faq = _faqs()["FAQ09"]
    politica = (DATA_DIR / "politica_devoluciones.txt").read_text(encoding="utf-8")
    for t in ["30 días calendario posteriores a la entrega", "sin usar", "empaque original"]:
        assert t in faq and t in politica, t
