def build_prompt(order: dict) -> str:
    """
    Prompt Few-shot para consultar el estado de un pedido.
    """

    return f"""
Ejemplo 1:
Pregunta: ¿Dónde está mi pedido?
Respuesta: Tu pedido está en camino y será entregado en la fecha estimada indicada.

Ejemplo 2:
Pregunta: ¿Cuál es el estado de mi pedido?
Respuesta: Tu pedido presenta un retraso. Te recomendamos revisar la fecha estimada de entrega.

Ahora responde la siguiente consulta utilizando el mismo estilo:

Información del pedido:
- Cliente: {order["customer"]}
- Producto: {order["product"]}
- Estado: {order["status"]}
- Fecha estimada de entrega: {order["estimated_delivery"]}

Pregunta:
¿Cuál es el estado del pedido {order["tracking_number"]}?
""".strip()