"""Verificador de reglas de devolución (sin LLM): comprueba la política con código verificable.

El LLM de 0.5B del Taller 1 aceptaba devoluciones a los 45 días; aquí la decisión no depende
del modelo, que solo redacta el veredicto. El plazo vive en reglas.json (única fuente en código).
"""
import csv
import json
import re
import unicodedata

from src.config import DATA_DIR, RULES_PATH

PLAZO_DIAS = json.loads(RULES_PATH.read_text(encoding="utf-8"))["plazo_dias"]


def check_return(category: str | None, devolvible: str | None, days: int | None,
                 opened: bool | None, packaging: bool | None) -> dict:
    """Evalúa una solicitud de devolución.

    category   categoría del catálogo ('higiene personal', 'alimentos perecederos', ...) o None
    devolvible 'si' | 'solo_sin_abrir' | 'no' (columna del catálogo) o None si no se identificó el producto
    days       días transcurridos desde la entrega, o None
    opened     True si el producto fue usado o abierto, False si está sin usar, None si no se sabe
    packaging  True si conserva el empaque original, False si no, None si no se sabe

    Devuelve {"aceptada": bool | None, "motivos": [...], "faltantes": [...]}; aceptada es None
    cuando faltan datos y ninguna regla ya rechaza la solicitud.
    """
    motivos, faltantes = [], []

    # 1. Reglas que ya se pueden decidir con lo que se sabe. Un solo motivo de rechazo basta,
    #    así que no se piden más datos si ya hay un rechazo seguro.
    if devolvible == "no":
        if category and "perecedero" in category:
            motivos.append("Los productos perecederos no pueden devolverse.")
        else:
            motivos.append("Los productos personalizados no pueden devolverse.")
    if devolvible == "solo_sin_abrir" and opened:
        motivos.append("Los productos de higiene personal que hayan sido abiertos no pueden devolverse.")
    elif opened:
        motivos.append("El producto debe estar sin usar.")
    if packaging is False:
        motivos.append("El producto debe conservar su empaque original.")
    if days is not None and days > PLAZO_DIAS:
        motivos.append(f"Han pasado {days} días desde la entrega y el plazo es de {PLAZO_DIAS} días calendario.")

    if motivos:
        return {"aceptada": False, "motivos": motivos, "faltantes": []}

    # 2. Sin rechazo: si falta algún dato se pide al cliente en vez de adivinar
    if devolvible is None:
        faltantes.append("producto")
    if days is None:
        faltantes.append("días desde la entrega")
    if opened is None:
        faltantes.append("si el producto está sin usar (o sin abrir)")
    if packaging is None:
        faltantes.append("si conserva el empaque original")
    if faltantes:
        return {"aceptada": None, "motivos": [], "faltantes": faltantes}

    return {"aceptada": True,
            "motivos": [f"Cumple las condiciones: dentro de {PLAZO_DIAS} días, sin usar y con empaque original."],
            "faltantes": []}


# ---------------------------------------------------------------------------
# Extracción de los datos de la solicitud desde el texto del cliente (regex simples)
# ---------------------------------------------------------------------------

def _norm(text: str) -> str:
    """Minúsculas y sin tildes, para que 'audífonos' y 'audifonos' coincidan."""
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def find_product(text: str) -> dict | None:
    """Producto del catálogo mencionado en el texto -> {'category', 'devolvible'}, o None.

    Puntúa cada producto por cuántas palabras de su nombre aparecen en el texto (comparando los
    primeros 5 caracteres para tolerar plurales: camiseta/camisetas). Si empatan productos con
    distinta categoría o distinto 'devolvible' (p. ej. 'reutilizable' aparece en varios) es
    ambiguo y se devuelve None para preguntar al cliente. 'camiseta' da dos productos, pero ambos
    son ropa/'si', y eso basta para aplicar las reglas."""
    t = _norm(text)
    text_stems = {w[:5] for w in re.findall(r"[a-z0-9]+", t)}
    with (DATA_DIR / "catalogo.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    scored = []
    for row in rows:
        name = _norm(row["producto"])
        words = [w for w in re.findall(r"[a-z0-9]+", name) if len(w) >= 4]  # sin 'de', 'con', 'set', 'kit'
        score = 100 if name in t else sum(w[:5] in text_stems for w in words)
        if score:
            scored.append((score, row))
    if not scored:
        return None
    best = max(s for s, _ in scored)
    options = {(r["categoria"], r["devolvible"]) for s, r in scored if s == best}
    if len(options) != 1:
        return None
    category, devolvible = options.pop()
    return {"category": category, "devolvible": devolvible}


# Frases que NIEGAN uso o apertura. 'nuevo/nueva' no está: «una crema nueva que abrí» describe el estado de compra, no el actual
NOT_USED_RE = re.compile(r"\b(?:sin (usar|abrir|estrenar)|no (lo |la |los |las )?(he |ha )?(usado|abierto|abri|use|estrenado)"
                         r"|nunca (lo |la |los |las )?(he |ha )?(use|usado|abri|abierto|estrene|estrenado)"
                         r"|ni (usado|abierto|usar|abrir)|sellad|cerrad|intact)")
USED_RE = re.compile(r"usad|\buse\b|estren|gastad")
OPENED_RE = re.compile(r"abiert|\babri\b|\babrio\b")
NO_PACKAGING_RE = re.compile(r"sin (el |su |la )?(empaque|caja|envase|embalaje)"
                             r"|no tengo (el |su |la )?(empaque|caja|envase|embalaje)"
                             r"|no (lo |la )?conserv|perdi (el |la |su )(empaque|caja)|tire (el |la |su )(empaque|caja)")
PACKAGING_RE = re.compile(r"(con|conserv\w*|tengo) (el |su |la |todo el )?(empaque|caja|envase|embalaje)|en su empaque")


def parse_return_request(text: str) -> dict:
    """Datos para check_return. Lo que no se menciona queda en None (luego se le pide al cliente)."""
    t = _norm(text)
    product = find_product(text) or {}
    days = re.search(r"(\d+)\s*dias", t)

    # Primero se QUITAN las frases negativas ('sin usar', 'no lo he usado') y se busca «usado/abierto» en lo que queda:
    # si queda alguno, el producto sí se usó o abrió aunque otra parte del texto lo niegue («sin usar… pero lo abrí»).
    # Solo si no queda ninguno y había una negación, se toma como sin usar.
    negated = bool(NOT_USED_RE.search(t))
    rest = NOT_USED_RE.sub(" ", t)
    opened = None
    if USED_RE.search(rest):
        opened = True
    elif OPENED_RE.search(rest) and product.get("devolvible") == "solo_sin_abrir":
        opened = True  # 'abierto' solo importa en higiene personal; en otros productos la regla es 'sin usar'
    elif negated:
        opened = False

    # Con el empaque pasa lo mismo: las negaciones van primero porque «no tengo la caja» contiene «tengo la caja»
    packaging = None
    if NO_PACKAGING_RE.search(t):
        packaging = False
    elif PACKAGING_RE.search(t):
        packaging = True

    return {"category": product.get("category"), "devolvible": product.get("devolvible"),
            "days": int(days.group(1)) if days else None, "opened": opened, "packaging": packaging}
