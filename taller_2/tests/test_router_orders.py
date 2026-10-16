from src.orders import extract_tracking, find_order
from src.router import route


def test_route():
    assert route("¿Dónde está mi pedido ecm10004?") == "order"
    assert route("Quiero devolver unos audífonos") == "return"
    assert route("Necesito un reembolso") == "return"
    assert route("ECM10001: quiero la devolución") == "order"  # el pedido tiene prioridad
    assert route("¿Cuánto cuesta el envío?") == "rag"


def test_orders():
    assert extract_tracking("mi pedido ecm10004 no llega") == "ECM10004"
    assert extract_tracking("sin número") is None
    order = find_order("ECM10001")
    assert order["product"] == "Botella reutilizable de acero" and "customer" not in order
    assert find_order("ECM99999") is None
