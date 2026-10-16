def build_prompt(order: dict) -> str:
    """
    Prompt con delimitadores para separar instrucciones,
    contexto y consulta.
    """

    return f"""
Utiliza la información del pedido para responder la consulta del cliente.

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