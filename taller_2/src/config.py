"""Configuración central: rutas, parámetros de recuperación y modelos.

Todo lo que se pueda querer cambiar al experimentar vive aquí (o en .env).
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Raíz del proyecto = carpeta que contiene src/. Con pathlib funciona igual en Windows y Linux.
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")  # carga las claves si existe .env; si no, no pasa nada


def _use_system_certs() -> None:
    """USE_SYSTEM_CERTS=1: Python verifica los certificados con el almacén del sistema operativo.

    Sirve cuando un antivirus, VPN o proxy intercepta el HTTPS con su propio certificado
    (error 'self signed certificate in certificate chain'). NO desactiva la verificación: solo
    cambia dónde se buscan las autoridades de confianza. Este módulo se importa antes que cualquier
    cliente HTTP (Hugging Face, Groq), por eso se activa aquí."""
    try:
        import truststore  # importación perezosa: solo hace falta si se activa la opción
    except ImportError:
        raise SystemExit("USE_SYSTEM_CERTS=1 requiere el paquete truststore. Instálalo con: pip install truststore")
    truststore.inject_into_ssl()


if os.getenv("USE_SYSTEM_CERTS", "0") == "1":
    _use_system_certs()

DATA_DIR = ROOT / "data"
CHROMA_DIR = ROOT / "chroma_db"
RESULTS_DIR = ROOT / "results"
GOLD_PATH = ROOT / "evaluation" / "gold.json"
RULES_PATH = ROOT / "src" / "reglas.json"

# --- Recuperación ---
COLLECTION_NAME = "ecomarket"
EMBEDDING_MODEL = "intfloat/multilingual-e5-small"
K = 4  # fragmentos por consulta: prompts cortos para CPU y para el límite de tokens de la API
# Puntaje mínimo (similitud coseno = 1 - distancia) para aceptar un fragmento.
# Calibrado con evaluation/calibrate_threshold.py (punto medio entre el peor 'in', 0.837, y el mejor
# 'ooc_facil', 0.807; ver results/threshold.md). La escala depende del modelo E5: recalibrar si cambia.
RELEVANCE_THRESHOLD = 0.822

# --- Fragmentación ---
MAX_CHUNK_CHARS = 600  # si un fragmento lo excede, se divide con el splitter recursivo
CHUNK_OVERLAP = 80

# --- Generador ---
LLM_PROVIDER = (os.getenv("LLM_PROVIDER") or "auto").strip().lower()  # auto | groq | local (vacío = auto)
LLM_MODEL = os.getenv("LLM_MODEL", "").strip()  # vacío = modelo por defecto del proveedor
GROQ_DEFAULT_MODEL = "openai/gpt-oss-20b"
LOCAL_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
LOCAL_MAX_NEW_TOKENS = 200
API_MAX_TOKENS = 1500  # tope de salida por llamada (incluye el razonamiento de gpt-oss); cuida el límite de TPM
API_MAX_RETRIES = 3  # reintentos ante HTTP 429
API_MAX_WAIT_S = 120  # si retry-after pide más (p. ej. cupo diario agotado), no se espera: se informa
LLM_PAUSE_S = float(os.getenv("LLM_PAUSE_S", "20"))

# 1 = el verificador de reglas decide las devoluciones; 0 = decide el LLM (para comparar)
USE_RULES = os.getenv("USE_RULES", "1") == "1"
