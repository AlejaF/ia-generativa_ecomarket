"""Reintentos ante HTTP 429 y selección de proveedor, SIN llamar a ninguna API (todo simulado)."""
import pytest
from langchain_core.messages import AIMessage

from src import llm
from src.llm import LLMError


class FakeHTTPError(Exception):
    """Imita los errores del SDK de Groq: status_code y response.headers."""

    def __init__(self, status_code, retry_after=None, text=""):
        super().__init__(text or f"error {status_code}")
        self.status_code = status_code
        headers = {"retry-after": str(retry_after)} if retry_after is not None else {}
        self.response = type("R", (), {"headers": headers})()


class FakeChat:
    """Falla con los errores dados, en orden, y luego responde bien."""

    def __init__(self, errors):
        self.errors, self.calls = list(errors), 0

    def invoke(self, prompt_value):
        self.calls += 1
        if self.errors:
            raise self.errors.pop(0)
        return AIMessage(content="respuesta", usage_metadata={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15})


@pytest.fixture
def sleeps(monkeypatch):
    """Evita esperar de verdad y registra cuántos segundos se habría esperado."""
    waited = []
    monkeypatch.setattr(llm.time, "sleep", waited.append)
    return waited


def make(monkeypatch, errors):
    chat = FakeChat(errors)
    monkeypatch.setattr(llm, "_build_chat", lambda model: chat)
    return chat, llm._api_runnable("openai/gpt-oss-20b")


def test_429_espera_retry_after_y_reintenta(monkeypatch, sleeps):
    chat, runnable = make(monkeypatch, [FakeHTTPError(429, retry_after=7), FakeHTTPError(429, retry_after=3)])
    before = dict(llm.USAGE)
    assert runnable.invoke("hola").content == "respuesta"
    assert sleeps == [7.0, 3.0]  # esperó exactamente lo que pidió la cabecera
    assert chat.calls == 3
    assert llm.USAGE["input_tokens"] - before["input_tokens"] == 10  # y registró los tokens


def test_429_sin_cabecera_espera_10s(monkeypatch, sleeps):
    _, runnable = make(monkeypatch, [FakeHTTPError(429)])
    runnable.invoke("hola")
    assert sleeps == [10.0]


def test_429_agota_los_reintentos(monkeypatch, sleeps):
    chat, runnable = make(monkeypatch, [FakeHTTPError(429, retry_after=1)] * 10)
    with pytest.raises(LLMError, match="429"):
        runnable.invoke("hola")
    assert chat.calls == llm.API_MAX_RETRIES + 1  # 1 intento + 3 reintentos
    assert len(sleeps) == llm.API_MAX_RETRIES


def test_429_con_espera_excesiva_no_espera(monkeypatch, sleeps):
    # p. ej. cupo diario agotado: retry-after de horas; esperar no tiene sentido, se informa
    chat, runnable = make(monkeypatch, [FakeHTTPError(429, retry_after=3600)])
    with pytest.raises(LLMError, match="429"):
        runnable.invoke("hola")
    assert sleeps == [] and chat.calls == 1


def test_otros_errores_no_se_reintentan(monkeypatch, sleeps):
    chat, runnable = make(monkeypatch, [FakeHTTPError(401)])
    with pytest.raises(LLMError, match="401"):
        runnable.invoke("hola")
    assert chat.calls == 1 and sleeps == []


def test_modelo_inexistente_explica_como_listar(monkeypatch, sleeps):
    _, runnable = make(monkeypatch, [FakeHTTPError(404, text="The model `x` does not exist")])
    with pytest.raises(LLMError, match="api.groq.com/openai/v1/models"):
        runnable.invoke("hola")


# ---------- Selección de proveedor ('auto': Groq si hay clave, si no local) ----------

@pytest.fixture
def provider_env(monkeypatch):
    def set_env(provider="auto", model="", groq=None):
        monkeypatch.setattr(llm, "LLM_PROVIDER", provider)
        monkeypatch.setattr(llm, "LLM_MODEL", model)
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        if groq:
            monkeypatch.setenv("GROQ_API_KEY", groq)
    return set_env


def test_auto_usa_groq_si_hay_clave_y_si_no_local(provider_env):
    provider_env(groq="x")
    assert llm.resolve_provider() == ("groq", llm.GROQ_DEFAULT_MODEL)
    provider_env()
    assert llm.resolve_provider() == ("local", llm.LOCAL_MODEL)


def test_llm_model_fija_el_modelo_del_proveedor(provider_env):
    provider_env("groq", model="openai/gpt-oss-120b", groq="x")
    assert llm.resolve_provider() == ("groq", "openai/gpt-oss-120b")
    provider_env("local", model="otro-modelo-local")
    assert llm.resolve_provider() == ("local", "otro-modelo-local")


@pytest.mark.parametrize("valor", ["otro", "gpt"])
def test_proveedor_no_valido_da_error_claro(provider_env, valor):
    provider_env(valor)
    with pytest.raises(LLMError, match="auto, groq o local"):
        llm.resolve_provider()
    with pytest.raises(LLMError, match="auto, groq o local"):
        llm.get_llm()


def test_groq_explicito_sin_clave_falla_claro(provider_env):
    provider_env("groq")
    with pytest.raises(LLMError, match="GROQ_API_KEY"):
        llm.get_llm()
