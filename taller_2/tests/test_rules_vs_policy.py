"""Falla si el plazo de reglas.json deja de coincidir con los días del texto de la política."""
import re

from src.config import DATA_DIR
from src.rules import PLAZO_DIAS, check_return


def test_plazo_coincide_con_politica():
    text = (DATA_DIR / "politica_devoluciones.txt").read_text(encoding="utf-8")
    # "30 días calendario posteriores a la entrega" (no confundir con "5 a 10 días hábiles" del reembolso)
    plazos = {int(n) for n in re.findall(r"(\d+)\s+días\s+(?:calendario\s+)?posteriores", text)}
    assert plazos == {PLAZO_DIAS}


def test_casos_del_taller_1():
    # audífonos (electrónica, devolvible), 10 días, sin usar, con empaque -> aceptada
    assert check_return("electrónica", "si", 10, False, True)["aceptada"] is True
    # crema abierta (higiene personal, solo sin abrir) -> rechazada
    assert check_return("higiene personal", "solo_sin_abrir", 5, True, True)["aceptada"] is False
    # camiseta a los 45 días -> rechazada por plazo
    r = check_return("ropa", "si", 45, False, True)
    assert r["aceptada"] is False and "45" in r["motivos"][0]


def test_productos_no_devolvibles():
    assert check_return("alimentos perecederos", "no", 1, False, True)["aceptada"] is False
    assert check_return("hogar", "no", 1, False, True)["aceptada"] is False  # personalizado


def test_faltan_datos_se_piden():
    r = check_return("ropa", "si", None, None, None)
    assert r["aceptada"] is None and len(r["faltantes"]) == 3
    assert check_return(None, None, 10, False, True)["faltantes"] == ["producto"]


def test_rechazo_seguro_no_pide_datos():
    r = check_return("ropa", "si", 45, None, None)
    assert r["aceptada"] is False and r["faltantes"] == []
