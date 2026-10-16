from pathlib import Path

from src.model import LocalLLM
from src.returns import ask_about_return


BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_FILE = BASE_DIR / "experiments" / "results.txt"

MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

PROMPT_VERSIONS = ["v1", "v2", "v3", "final"]

TEST_CASES = [
    {
        "name": "Caso 1 - Producto dentro de las condiciones",
        "product": {
            "product": "Audífonos inalámbricos",
            "category": "electronica",
            "days_since_delivery": 10,
            "condition": "sin usar",
            "original_packaging": True,
        },
    },
    {
        "name": "Caso 2 - Producto no retornable",
        "product": {
            "product": "Crema de cuidado personal",
            "category": "higiene personal",
            "days_since_delivery": 5,
            "condition": "abierto",
            "original_packaging": True,
        },
    },
    {
        "name": "Caso 3 - Solicitud fuera del plazo",
        "product": {
            "product": "Camiseta reutilizable",
            "category": "ropa",
            "days_since_delivery": 45,
            "condition": "sin usar",
            "original_packaging": True,
        },
    },
]


def main():
    print("=" * 70)
    print("EXPERIMENTO - DEVOLUCIONES")
    print(f"Modelo: {MODEL_NAME}")
    print("=" * 70)

    print("\nCargando modelo...")
    llm = LocalLLM()
    print("Modelo cargado correctamente.\n")

    for prompt_version in PROMPT_VERSIONS:

        print("\n" + "#" * 70)
        print(f"VERSIÓN DEL PROMPT: {prompt_version}")
        print("#" * 70)

        results = []

        for case in TEST_CASES:

            print("\n" + "=" * 60)
            print(case["name"])
            print("=" * 60)

            response = ask_about_return(
                case["product"],
                prompt_version=prompt_version,
                llm=llm,
            )

            print(response)

            result = (
                "\n"
                + "=" * 60
                + "\n"
                + case["name"]
                + "\n"
                + "=" * 60
                + "\n"
                + "Producto:\n"
                + str(case["product"])
                + "\n\n"
                + "Respuesta del modelo:\n"
                + response
                + "\n"
            )

            results.append(result)

        with open(RESULTS_FILE, "a", encoding="utf-8") as file:
            file.write("\n")
            file.write("=" * 70 + "\n")
            file.write("EXPERIMENTO - Devoluciones\n")
            file.write(f"Modelo: {MODEL_NAME}\n")
            file.write(f"Versión del prompt: {prompt_version}\n")
            file.write("=" * 70 + "\n")
            file.write("\n".join(results))
            file.write("\n")

    print("\n" + "=" * 70)
    print(f"Resultados guardados en: {RESULTS_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    main()