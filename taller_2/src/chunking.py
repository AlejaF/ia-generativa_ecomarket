"""Fragmentación por estructura: un fragmento por unidad lógica de cada documento.

Cada fragmento empieza con un encabezado contextual y conserva LITERAL el texto original
(solo se añaden encabezado y conectores), porque gold.json busca frases literales.
"""
import csv
import json
import re
import unicodedata

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import CHUNK_OVERLAP, DATA_DIR, MAX_CHUNK_CHARS


def _read(name: str) -> str:
    # Normaliza saltos de línea de Windows para que los regex funcionen igual en todas partes
    return (DATA_DIR / name).read_text(encoding="utf-8").replace("\r\n", "\n")


def slugify(text: str) -> str:
    """'Métodos y tiempos de envío' -> 'metodos-y-tiempos-de-envio' (formato de chunk_id en gold.json)."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _make(source: str, doc_type: str, section_or_id: str, header: str, body: str) -> Document:
    return Document(
        page_content=f"{header}\n{body.strip()}",
        metadata={
            "source": source,
            "doc_type": doc_type,
            "section_or_id": section_or_id,
            "chunk_id": f"{doc_type}::{section_or_id}",
        },
    )


def _politica() -> list[Document]:
    text = _read("politica_devoluciones.txt")
    # Un título de sección es "N. " seguido SOLO de mayúsculas; así no se confunde con los
    # pasos numerados de la sección 7 ("1. Escribir a soporte...").
    heading = re.compile(r"^(\d+)\. ([A-ZÁÉÍÓÚÜÑ ]+)$", re.MULTILINE)
    matches = list(heading.finditer(text))
    docs = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        header = f"Política de devoluciones — {m.group(1)}. {m.group(2)}"
        docs.append(_make("politica_devoluciones.txt", "politica", m.group(1), header, text[m.end():end]))
    return docs


def _faq() -> list[Document]:
    items = json.loads(_read("faqs.json"))
    return [
        _make("faqs.json", "faq", f["id"], f"Preguntas frecuentes — {f['id']} ({f['categoria']})",
              f"Pregunta: {f['pregunta']} Respuesta: {f['respuesta']}")
        for f in items
    ]


# El código del CSV se traduce a una oración: los embeddings entienden mejor lenguaje natural
DEVOLVIBLE = {
    "si": "Se puede devolver dentro del plazo si cumple las condiciones generales.",
    "solo_sin_abrir": "Solo se puede devolver si no ha sido abierto.",
    "no": "No se puede devolver.",
}


def _catalogo() -> list[Document]:
    docs = []
    with (DATA_DIR / "catalogo.csv").open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            precio = f"${int(r['precio_cop']):,}".replace(",", ".")  # 59900 -> $59.900
            body = (f"Producto: {r['producto']}. Categoría: {r['categoria']}. Material: {r['material']}. "
                    f"Descripción: {r['descripcion']} Precio: {precio} COP. {DEVOLVIBLE[r['devolvible']]}")
            docs.append(_make("catalogo.csv", "catalogo", r["sku"], f"Catálogo — {r['sku']}", body))
    return docs


def _envios() -> list[Document]:
    text = _read("envios_y_pagos.md")
    parts = re.split(r"^## (.+)$", text, flags=re.MULTILINE)  # [intro, título, cuerpo, título, cuerpo...]
    return [
        _make("envios_y_pagos.md", "envios", slugify(title), f"Envíos, pagos y atención — {title}", body)
        for title, body in zip(parts[1::2], parts[2::2])
    ]


def _split_if_long(doc: Document) -> list[Document]:
    """Respaldo: si un fragmento excede MAX_CHUNK_CHARS lo divide en trozos con solapamiento.
    Hoy ninguno lo necesita; existe para cuando se amplíen los documentos."""
    if len(doc.page_content) <= MAX_CHUNK_CHARS:
        return [doc]
    header, _, body = doc.page_content.partition("\n")
    splitter = RecursiveCharacterTextSplitter(chunk_size=MAX_CHUNK_CHARS, chunk_overlap=CHUNK_OVERLAP)
    pieces = []
    for n, piece in enumerate(splitter.split_text(body), start=1):
        meta = dict(doc.metadata, chunk_id=doc.metadata["chunk_id"] + (f"#{n}" if n > 1 else ""))
        pieces.append(Document(page_content=f"{header}\n{piece}", metadata=meta))
    return pieces


def load_chunks() -> list[Document]:
    docs = _politica() + _faq() + _catalogo() + _envios()
    return [piece for d in docs for piece in _split_if_long(d)]
