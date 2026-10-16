"""Prompts y cadenas LCEL (prompt | llm | StrOutputParser) de los tres flujos del chat."""
import re

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from src.llm import get_llm

# Mensaje fijo: se devuelve SIN llamar al LLM cuando ningún fragmento supera el umbral,
# y es también lo que se le ordena decir al LLM si el contexto no trae la respuesta.
NOT_AVAILABLE = ("No cuento con las herramientas para atender esta solicitud. Si lo deseas, "
                 "puedo derivarte con un agente humano: escribe a soporte@ecomarket.example.")

ROLE = ("Eres el asistente de atención al cliente de EcoMarket, una tienda de productos ecológicos. "
        "Respondes en español, tratando al cliente de tú (nunca de usted), de forma clara, amable y breve, "
        "en texto plano: sin Markdown, "
        "sin asteriscos, sin almohadillas y sin negritas.")

RAG_SYSTEM = ROLE + f""" Responde usando ÚNICAMENTE el contexto entregado. No inventes datos, precios, plazos ni procedimientos.
Si el contexto no contiene la respuesta (aunque el tema parezca cercano, como un producto que no aparece), responde exactamente: "{NOT_AVAILABLE}" y no cites fuentes.
Si sí la contiene, al final cita las fuentes que usaste con los ids entre corchetes del contexto, así: (Fuentes: faq::FAQ02, envios::costos-de-envio)."""
RAG_HUMAN = "Contexto:\n{context}\n\nPregunta del cliente: {question}"

ORDER_SYSTEM = ROLE + """ Informa el estado de un pedido usando ÚNICAMENTE los datos del pedido. No inventes información.
Responde con este formato exacto:
Estado: <estado del pedido>
Entrega estimada: <fecha>
Mensaje: <una o dos frases para el cliente; si el pedido está Retrasado, discúlpate y menciona el enlace de seguimiento>"""
ORDER_HUMAN = "Datos del pedido:\n{order}\n\nPregunta del cliente: {question}"

# Con el verificador (USE_RULES=1): el veredicto ya está decidido por código; el LLM solo lo redacta
RETURN_RULES_SYSTEM = ROLE + """ El sistema ya verificó la solicitud de devolución y entregó un veredicto: NO lo cambies ni lo discutas.
Explica el veredicto al cliente con empatía, mencionando SOLO los motivos listados: no afirmes que se incumple ninguna otra condición.
Si la devolución es ACEPTADA, indica los pasos de la sección «PASOS GENERALES» y el reembolso tal como aparecen en la política, sin añadir otros.
Si es RECHAZADA, explica el motivo y no menciones pasos.
No inventes excepciones, condiciones, plazos ni procedimientos que no estén en la política."""
RETURN_RULES_HUMAN = ("Veredicto: {verdict}\nMotivos:\n{reasons}\n\nPolítica de devoluciones:\n{context}\n\n"
                      "Solicitud del cliente: {question}")

# Sin verificador (USE_RULES=0): decide el LLM con los fragmentos, para poder comparar
RETURN_FREE_SYSTEM = ROLE + """ Decide si la devolución que pide el cliente es posible, usando ÚNICAMENTE la política de devoluciones.
Explica la decisión y, si es posible, los pasos. No inventes excepciones, condiciones, plazos ni procedimientos.
Si falta algún dato para decidir, pídelo al cliente."""
RETURN_FREE_HUMAN = "Política de devoluciones:\n{context}\n\nSolicitud del cliente: {question}"


def to_plain_text(text: str) -> str:
    """Quita el Markdown que el modelo pueda añadir aunque se le pida texto plano (la consola no lo renderiza)."""
    text = re.sub(r"^\s*#+\s*", "", text, flags=re.MULTILINE)       # títulos: '## Pasos' -> 'Pasos'
    text = re.sub(r"^(\s*)[*+]\s+", r"\1- ", text, flags=re.MULTILINE)  # viñetas '* x' -> '- x'
    text = re.sub(r"[*_`]{2,}|[*`]", "", text)                      # negritas, cursivas y código
    return text.strip()


def format_context(docs: list[Document]) -> str:
    """Cada fragmento con su chunk_id entre corchetes, para que el modelo pueda citarlo."""
    return "\n\n".join(f"[{d.metadata['chunk_id']}]\n{d.page_content}" for d in docs)


def build_chain(system: str, human: str):
    """La cadena LCEL del taller: prompt | llm | StrOutputParser."""
    prompt = ChatPromptTemplate.from_messages([("system", system), ("human", human)])
    return prompt | get_llm() | StrOutputParser()


def rag_chain():
    return build_chain(RAG_SYSTEM, RAG_HUMAN)


def plain_chain():
    """Sin RAG: el LLM recibe solo la pregunta. Es la línea base de eval_end_to_end (no se usa en el chat)."""
    return build_chain(ROLE, "{question}")


def order_chain():
    return build_chain(ORDER_SYSTEM, ORDER_HUMAN)


def return_chain(use_rules: bool):
    if use_rules:
        return build_chain(RETURN_RULES_SYSTEM, RETURN_RULES_HUMAN)
    return build_chain(RETURN_FREE_SYSTEM, RETURN_FREE_HUMAN)
