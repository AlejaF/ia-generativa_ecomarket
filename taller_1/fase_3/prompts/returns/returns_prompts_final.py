def build_return_prompt(
    policy: str,
    product: dict,
) -> str:
    """
    Construye el prompt final para evaluar una solicitud de devolución.
    """

    product_info = f"""
Producto: {product["product"]}
Categoría: {product["category"]}
Días desde la entrega: {product["days_since_delivery"]}
Condición: {product["condition"]}
Empaque original: {"Sí" if product["original_packaging"] else "No"}
""".strip()

    return f"""
Eres un agente de atención al cliente de EcoMarket.

Utiliza únicamente la siguiente política de devoluciones y los datos
proporcionados del producto. No inventes información.

POLÍTICA DE DEVOLUCIONES:
{policy}

DATOS DEL CASO:
{product_info}

Determina si la devolución cumple la política.

Evalúa las condiciones de la política antes de tomar una decisión.
No asumas que una condición se cumple si los datos no lo indican.

Responde exactamente con este formato:

Estado: [Aceptada / No aceptada]
Motivo: [explicación breve basada únicamente en la política]
""".strip()