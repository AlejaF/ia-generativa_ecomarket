"""Generador: get_llm() devuelve un Runnable de LangChain según LLM_PROVIDER.

Entrada: el valor del prompt (PromptValue). Salida: AIMessage (API) o str (local);
ambos los acepta StrOutputParser. Si la API falla NO se cambia de modelo en silencio:
tras los reintentos se lanza LLMError y el chat muestra el mensaje.
"""
import os
import re
import time

from langchain_core.runnables import RunnableLambda

from src.config import (API_MAX_RETRIES, API_MAX_TOKENS, API_MAX_WAIT_S, GROQ_DEFAULT_MODEL, LLM_MODEL,
                        LLM_PROVIDER, LOCAL_MAX_NEW_TOKENS, LOCAL_MODEL)

# Contador de tokens de la sesión (las evaluaciones lo guardan; sirve para vigilar el límite diario)
USAGE = {"calls": 0, "input_tokens": 0, "output_tokens": 0}


class LLMError(RuntimeError):
    """Error del generador con un mensaje pensado para mostrarse al usuario."""


def resolve_provider() -> tuple[str, str]:
    """(proveedor, modelo) efectivos. En 'auto': Groq si hay GROQ_API_KEY, si no el modelo local."""
    provider = LLM_PROVIDER
    if provider not in ("auto", "groq", "local"):
        raise LLMError(f"LLM_PROVIDER='{provider}' no es válido. Usa: auto, groq o local.")
    if provider == "auto":
        provider = "groq" if os.getenv("GROQ_API_KEY") else "local"
    defaults = {"groq": GROQ_DEFAULT_MODEL, "local": LOCAL_MODEL}
    return provider, LLM_MODEL or defaults[provider]


def describe() -> str:
    provider, model = resolve_provider()
    return f"{provider}/{model}"


# ---------- API (Groq) ----------

def _build_chat(model: str, max_retries: int = 0):
    """Modelo de chat de Groq. temperature=0 = decodificación determinista. Por defecto max_retries=0
    porque los reintentos los hacemos nosotros (respetando retry-after); RAGAS usa este modelo
    directamente y pide reintentos al SDK, que también respeta retry-after."""
    if not os.getenv("GROQ_API_KEY"):
        raise LLMError("LLM_PROVIDER=groq pero falta GROQ_API_KEY. Defínela en .env (ver .env.example).")
    from langchain_groq import ChatGroq
    # gpt-oss es un modelo de razonamiento: langchain-groq deja el texto final en .content y el
    # razonamiento aparte (additional_kwargs["reasoning_content"]). Esfuerzo "low" = menos tokens.
    return ChatGroq(model=model, temperature=0, max_tokens=API_MAX_TOKENS, max_retries=max_retries,
                    reasoning_effort="low")


def _retry_after(error: Exception) -> float:
    """Segundos que pide la cabecera retry-after de un 429 (10 s si no viene)."""
    try:
        return float(error.response.headers.get("retry-after"))
    except (AttributeError, TypeError, ValueError):
        return 10.0


def _explain(error: Exception, model: str, status: int | None) -> str:
    if status == 429:
        return (f"Se agotó el límite de uso de Groq (HTTP 429): se agotaron los {API_MAX_RETRIES} "
                f"reintentos o Groq pide esperar más de {API_MAX_WAIT_S} s. "
                "Intenta más tarde o usa LLM_PROVIDER=local.")
    if status == 401:
        return "La clave de API de Groq fue rechazada (HTTP 401). Revisa .env."
    if status in (400, 404) and "model" in str(error).lower():
        return (f"El modelo '{model}' no está disponible en Groq. Fija otro con LLM_MODEL. "
                "Para listar los modelos de tu cuenta: GET https://api.groq.com/openai/v1/models con la "
                "cabecera 'Authorization: Bearer <tu GROQ_API_KEY>'.")
    return f"Falló la llamada a Groq ({type(error).__name__}): {str(error)[:200]}"


def _api_runnable(model: str) -> RunnableLambda:
    chat = _build_chat(model)

    def call(prompt_value):
        for attempt in range(API_MAX_RETRIES + 1):
            try:
                msg = chat.invoke(prompt_value)
            except Exception as e:  # el SDK de Groq lanza varias clases de error; todas traen status_code
                status = getattr(e, "status_code", None)
                wait = _retry_after(e)
                if status == 429 and attempt < API_MAX_RETRIES and wait <= API_MAX_WAIT_S:
                    print(f"[llm] límite de uso (429): espero {wait:.0f} s y reintento ({attempt + 1}/{API_MAX_RETRIES})")
                    time.sleep(wait)
                    continue
                raise LLMError(_explain(e, model, status)) from e
            usage = msg.usage_metadata or {}
            USAGE["calls"] += 1
            USAGE["input_tokens"] += usage.get("input_tokens", 0)
            USAGE["output_tokens"] += usage.get("output_tokens", 0)
            if isinstance(msg.content, str) and "<think>" in msg.content:  # por si el razonamiento llega en línea
                msg.content = re.sub(r"<think>.*?</think>", "", msg.content, flags=re.DOTALL).strip()
            return msg

    return RunnableLambda(call)


# ---------- Local (Qwen2.5-0.5B-Instruct con Transformers) ----------

class LocalLLM:
    """Mismo patrón del Taller 1: plantilla de chat, generar, decodificar solo los tokens nuevos."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.tokenizer = self.model = None  # se cargan en la primera llamada: --solo-recuperacion no los necesita

    def _load(self):
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name)  # CPU, float32

    def __call__(self, prompt_value) -> str:
        if self.model is None:
            self._load()
        roles = {"system": "system", "human": "user", "ai": "assistant"}
        messages = [{"role": roles[m.type], "content": m.content} for m in prompt_value.to_messages()]
        text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer(text, return_tensors="pt")
        output = self.model.generate(**inputs, max_new_tokens=LOCAL_MAX_NEW_TOKENS, do_sample=False)
        new_tokens = output[0][inputs["input_ids"].shape[1]:]  # sin repetir el prompt
        USAGE["calls"] += 1  # así las evaluaciones cuentan también las generaciones del modelo local
        USAGE["input_tokens"] += inputs["input_ids"].shape[1]
        USAGE["output_tokens"] += len(new_tokens)
        return self.tokenizer.decode(new_tokens, skip_special_tokens=True).strip()


def get_llm() -> RunnableLambda:
    provider, model = resolve_provider()
    if provider == "local":
        if LLM_PROVIDER == "auto":
            print(f"[llm] AVISO: no hay GROQ_API_KEY; uso el modelo local ({model}). "
                  "Será lento y de menor calidad.")
        return RunnableLambda(LocalLLM(model))
    return _api_runnable(model)
