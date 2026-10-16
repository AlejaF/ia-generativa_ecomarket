def build_prompt(order: dict) -> str:
    """
    Prompt Zero-shot para consultar el estado de un pedido.
    """

    return f"""
Indica el estado del pedido {order["tracking_number"]}.

Información del pedido:
- Cliente: {order["customer"]}
- Producto: {order["product"]}
- Estado: {order["status"]}
- Fecha estimada de entrega: {order["estimated_delivery"]}
- Seguimiento: {order["tracking_url"]}
""".strip()