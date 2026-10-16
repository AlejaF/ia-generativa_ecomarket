def zero_shot_prompt(order_id: str) -> str:
    """
    Prompt inicial para consultar el estado de un pedido.
    """

    return f"""
Indica el estado del pedido {order_id}.
""".strip()