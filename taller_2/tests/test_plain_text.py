import os
import subprocess
import sys

from src.rag_chain import to_plain_text


def test_quita_markdown():
    md = "## Pasos\n**ACEPTADA** y *muy* clara.\n* uno\n  * dos\n- tres\n`código` (Fuentes: faq::FAQ02, envios::costos-de-envio)"
    out = to_plain_text(md)
    assert "*" not in out and "#" not in out and "`" not in out
    assert out.startswith("Pasos\nACEPTADA y muy clara.\n- uno\n  - dos\n- tres")
    assert "faq::FAQ02, envios::costos-de-envio" in out  # los ids con guion bajo o guiones no se tocan


def _run_config(**env):
    """Importa src.config en un proceso limpio con las variables dadas."""
    code = "import sys; sys.modules.update({k: None for k in sys.argv[1:]}); import src.config"
    return subprocess.run([sys.executable, "-c", code, *env.pop("hide", [])],
                          env={**os.environ, **env}, capture_output=True, text=True)


def test_system_certs_apagado_por_defecto_no_importa_truststore():
    r = _run_config(USE_SYSTEM_CERTS="0", hide=["truststore"])  # aunque el paquete falte, no pasa nada
    assert r.returncode == 0


def test_system_certs_sin_paquete_da_mensaje_claro():
    r = _run_config(USE_SYSTEM_CERTS="1", hide=["truststore"])
    assert r.returncode != 0 and "pip install truststore" in r.stderr


def test_system_certs_activado_funciona():
    assert _run_config(USE_SYSTEM_CERTS="1").returncode == 0
