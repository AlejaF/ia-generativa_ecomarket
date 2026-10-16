def build_prompt(order: dict) -> str:
    """
    Prompt con instrucciones numeradas para guiar
    al modelo paso a paso.
    """

    return f"""
Responde la consulta del cliente siguiendo estos pasos:

1. Identifica el número de seguimiento del pedido.
2. Revisa el estado actual del pedido.
3. Indica la fecha estimada de entrega.
4. Responde de manera clara y breve.
5. No inventes información que no esté presente en los datos proporcionados.

### INFORMACIÓN DEL PEDIDO ###
tracking_number: {order["tracking_number"]}
customer: {order["customer"]}
product: {order["product"]}
status: {order["status"]}
estimated_delivery: {order["estimated_delivery"]}
tracking_url: {order["tracking_url"]}
### FIN DE LA INFORMACIÓN DEL PEDIDO ###

### CONSULTA DEL CLIENTE ###
¿Cuál es el estado del pedido {order["tracking_number"]}?
### FIN DE LA CONSULTA ###
""".strip()