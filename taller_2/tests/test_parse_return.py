"""Extracción de datos de la solicitud de devolución (regex) y veredicto del verificador, con frases límite."""
import pytest

from src.rules import check_return, parse_return_request


def verdict(text: str) -> dict:
    return check_return(**parse_return_request(text))


# ---------- Frases límite que antes se aceptaban (o se quedaban sin rechazar) por error ----------

def test_crema_nueva_que_abri_se_rechaza():
    # «nueva» describe cómo se compró, no su estado actual; «abrí» en higiene personal es motivo de rechazo
    data = parse_return_request("Quiero devolver una crema nueva que abrí hace 5 días")
    assert data["opened"] is True
    assert verdict("Quiero devolver una crema nueva que abrí hace 5 días")["aceptada"] is False


def test_audifonos_nuevos_que_ya_use_se_rechazan():
    text = "Quiero devolver unos audífonos nuevos que ya usé"
    assert parse_return_request(text)["opened"] is True
    assert verdict(text)["aceptada"] is False


def test_no_tengo_la_caja_es_empaque_perdido():
    text = "Quiero devolver unos audífonos, no los he usado y no tengo la caja"
    data = parse_return_request(text)
    assert data["opened"] is False and data["packaging"] is False
    assert verdict(text)["aceptada"] is False


@pytest.mark.parametrize("text", [
    "Quiero devolver unos audífonos, los recibí hace 10 días, nunca los he usado y tengo la caja",
    "Quiero devolver unos audífonos, los recibí hace 10 días, no los he usado ni abierto y tengo la caja",
])
def test_nunca_he_usado_y_ni_abierto_se_aceptan(text):
    # «nunca … he usado» y «ni abierto» también niegan el uso
    assert parse_return_request(text)["opened"] is False
    assert verdict(text)["aceptada"] is True


def test_uno_usado_no_es_no_usado():
    # "uno usado" no debe leerse como "no usado"
    text = "Quiero devolver uno usado, audífonos, hace 10 días, con la caja"
    assert parse_return_request(text)["opened"] is True
    assert verdict(text)["aceptada"] is False


@pytest.mark.xfail(reason="limitación conocida: la regex no entiende 'casi no'")
def test_casi_no_los_use():
    text = "Quiero devolver unos audífonos, hace 10 días, casi no los usé y tengo la caja"
    assert verdict(text)["aceptada"] is False


def test_negacion_y_uso_en_la_misma_frase_gana_el_uso():
    # «sin usar» se descarta del texto y queda «abrí»: la crema sí se abrió
    assert parse_return_request("Mi crema estaba sin usar pero la abrí ayer")["opened"] is True


# ---------- Los casos de la evaluación no cambian ----------

CASOS = [  # (texto, aceptada esperada)
    ("Quiero devolver unos audífonos, los compré hace 10 días, sin usar y con su empaque original", True),                # R1
    ("Quiero devolver mi crema de cuidado personal, está abierta, la recibí hace 5 días", False),                         # R2
    ("Quiero devolver una camiseta que recibí hace 45 días, sin usar y con su empaque", False),                          # R3
    ("¿Puedo devolver la taza que tiene mi nombre grabado?", False),                                                     # Q28
]


@pytest.mark.parametrize("text,esperada", CASOS)
def test_casos_de_la_evaluacion(text, esperada):
    assert verdict(text)["aceptada"] is esperada


def test_datos_extraidos_de_r1():
    assert parse_return_request(CASOS[0][0]) == {
        "category": "electrónica", "devolvible": "si", "days": 10, "opened": False, "packaging": True}


# ---------- Datos que no se pueden extraer se piden, no se adivinan ----------

def test_hace_un_mes_no_da_dias():
    text = "Quiero devolver unos audífonos, los compré hace un mes, sin usar y con su empaque"
    assert parse_return_request(text)["days"] is None
    result = verdict(text)
    assert result["aceptada"] is None and result["faltantes"] == ["días desde la entrega"]
