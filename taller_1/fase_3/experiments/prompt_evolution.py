import importlib.util
import json
import sys
from pathlib import Path

from src.model import LocalLLM


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "pedidos.json"
PROMPTS_DIR = BASE_DIR / "prompts" / "orders"
RESULTS_FILE = BASE_DIR / "experiments" / "results.txt"


def load_orders() -> list[dict]:
    """Carga los pedidos desde pedidos.json."""

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def load_prompt_module(filename: str):
    """Carga dinámicamente un archivo de prompts."""

    file_path = PROMPTS_DIR / filename

    spec = importlib.util.spec_from_file_location(
        filename.replace(".py", ""),
        file_path,
    )

    if spec is None or spec.loader is None:
        raise ImportError(f"No se pudo cargar {file_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    return module


def find_order(
    tracking_number: str,
    orders: list[dict],
) -> dict | None:
    """Busca un pedido por su número de seguimiento."""

    for order in orders:
        if order["tracking_number"] == tracking_number:
            return order

    return None


def main():
    if len(sys.argv) != 2:
        print(
            "Uso: python -m experiments.prompt_evolution "
            "<tracking_number>"
        )
        return

    tracking_number = sys.argv[1]

    orders = load_orders()
    order = find_order(tracking_number, orders)

    if order is None:
        print(f"No se encontró el pedido {tracking_number}.")
        return

    prompt_files = [
        "01_zero_shot.py",
        "02_few_shot.py",
        "03_delimiters.py",
        "04_numbered_steps.py",
        "05_role_and_output.py",
    ]

    llm = LocalLLM()
    results = []

    for filename in prompt_files:
        module = load_prompt_module(filename)

        prompt = module.build_prompt(order)

        messages = [
            {
                "role": "user",
                "content": prompt,
            }
        ]

        response = llm.generate(messages)

        result = (
            "\n"
            + "=" * 60
            + "\n"
            + filename
            + "\n"
            + "=" * 60
            + "\n"
            + response
            + "\n"
        )

        print(result)
        results.append(result)

    with open(RESULTS_FILE, "a", encoding="utf-8") as file:
        file.write("\n")
        file.write("=" * 70 + "\n")
        file.write(
            f"EXPERIMENTO - Pedido: {tracking_number}\n"
        )
        file.write(
            "Modelo: Qwen/Qwen2.5-0.5B-Instruct\n"
        )
        file.write("=" * 70 + "\n")
        file.write("\n".join(results))
        file.write("\n")

    print(f"\nResultados guardados en: {RESULTS_FILE}")


if __name__ == "__main__":
    main()