from pathlib import Path

from src.model import LocalLLM


BASE_DIR = Path(__file__).resolve().parent.parent
POLICY_FILE = BASE_DIR / "knowledge" / "politica_devoluciones.txt"


def load_policy() -> str:
    """Carga la política de devoluciones."""

    with open(POLICY_FILE, "r", encoding="utf-8") as file:
        return file.read()


def get_prompt_builder(prompt_version: str):
    """Obtiene la función correspondiente a una versión del prompt."""

    if prompt_version == "v1":
        from prompts.returns.returns_prompts import build_return_prompt

    elif prompt_version == "v2":
        from prompts.returns.returns_prompts_v2 import build_return_prompt

    elif prompt_version == "v3":
        from prompts.returns.returns_prompts_v3 import build_return_prompt

    elif prompt_version == "final":
        from prompts.returns.returns_prompts_final import build_return_prompt

    else:
        raise ValueError(
            f"Versión de prompt no válida: {prompt_version}"
        )

    return build_return_prompt


def ask_about_return(
    product: dict,
    prompt_version: str = "final",
    llm: LocalLLM | None = None,
) -> str:

    policy = load_policy()

    build_return_prompt = get_prompt_builder(prompt_version)

    prompt = build_return_prompt(
        policy=policy,
        product=product,
    )

    messages = [
        {
            "role": "user",
            "content": prompt,
        }
    ]

    if llm is None:
        llm = LocalLLM()

    return llm.generate(messages)