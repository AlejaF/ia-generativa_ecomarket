import json
import sys
from pathlib import Path

from prompts.orders.order_status_prompts import zero_shot_prompt
from src.model import LocalLLM


BASE_DIR = Path(__file__).resolve().parent.parent
ORDERS_FILE = BASE_DIR / "data" / "pedidos.json"


def load_orders() -> list[dict]:
    """Carga los pedidos desde pedidos.json."""

    with open(ORDERS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


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
            "Uso: python -m src.order_status <tracking_number>"
        )
        return

    tracking_number = sys.argv[1]

    orders = load_orders()
    order = find_order(tracking_number, orders)

    if order is None:
        print(
            f"No se encontró el pedido {tracking_number}."
        )
        return

    prompt = zero_shot_prompt(order)

    messages = [
        {
            "role": "user",
            "content": prompt,
        }
    ]

    llm = LocalLLM()
    response = llm.generate(messages)

    print("\n=== ZERO-SHOT ===\n")
    print(response)


if __name__ == "__main__":
    main()