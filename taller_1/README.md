# EcoMarket AI Support

Proyecto de asistencia inteligente para atención al cliente de la empresa EcoMarket.

El proyecto explora el uso de modelos de lenguaje (LLM) y técnicas de ingeniería de prompts para resolver dos casos de uso:

- Consulta del estado de pedidos.
- Evaluación de solicitudes de devolución de productos.

## Estructura del proyecto

```text
ecomarket-ai-support/
├── fase_1_2.md
├── fase_3/
│   ├── data/
│   │   └── pedidos.json
│   ├── experiments/
│   │   ├── prompt_evolution.py
│   │   ├── return_experiment.py
│   │   └── results.txt
│   ├── knowledge/
│   │   └── politica_devoluciones.txt
│   ├── prompts/
│   │   ├── orders/
│   │   └── returns/
│   ├── src/
│   │   ├── model.py
│   │   ├── order_status.py
│   │   └── returns.py
│   └── analisis_fase_3.md
├── requirements.txt
└── README.md
```

## Fases del proyecto

### Fases 1 y 2

Las fases iniciales del proyecto se encuentran documentadas en `fase_1_2.md`.

### Fase 3

La Fase 3 corresponde a la aplicación práctica de técnicas de ingeniería de prompts para dos casos de uso:

1. Consulta del estado de pedidos.
2. Evaluación de solicitudes de devolución de productos.

La documentación, metodología, experimentos, resultados, análisis y conclusiones se encuentran en `fase_3/analisis_fase_3.md`.

## Modelo principal

Para la implementación final se utiliza:

**Qwen/Qwen2.5-0.5B-Instruct**

El modelo se ejecuta localmente mediante `Transformers` y CPU.

Durante la Fase 3 también se realizaron experimentos con modelos de mayor tamaño y con una versión cuantizada ejecutada mediante `llama.cpp`. Estos experimentos se conservaron como parte de la comparación y análisis de resultados.

Los archivos de los modelos no se incluyen en el repositorio debido a su tamaño.

## Instalación

Se recomienda utilizar un entorno virtual de Python.

### Crear el entorno virtual

```bash
python -m venv .venv
```

### Instalar las dependencias

```bash
pip install -r requirements.txt
```

## Ejecución

Los comandos relacionados con la Fase 3 deben ejecutarse desde la carpeta `fase_3`.

### Consulta del estado de un pedido

El número de seguimiento se proporciona desde la terminal.

```bash
python -m src.order_status ECM10004
```

El número de seguimiento puede reemplazarse por cualquier pedido disponible en `fase_3/data/pedidos.json`.

### Experimento de evolución de prompts para pedidos

El experimento permite evaluar las diferentes versiones de prompts utilizadas para la consulta del estado de los pedidos.

```bash
python -m experiments.prompt_evolution ECM10004
```

### Experimento de devoluciones

Para ejecutar el experimento de las diferentes versiones de prompts para devoluciones:

```bash
python -m experiments.return_experiment
```

Los resultados generados por los experimentos se almacenan en `fase_3/experiments/results.txt`.

## Datos y conocimiento

### Datos de pedidos

La información utilizada para las consultas de estado de pedidos se encuentra en `fase_3/data/pedidos.json`.

El archivo contiene los pedidos utilizados como base de pruebas para el proyecto.

### Política de devoluciones

La política utilizada como fuente de conocimiento para evaluar las solicitudes de devolución se encuentra en `fase_3/knowledge/politica_devoluciones.txt`.

## Ingeniería de prompts

Los prompts están organizados según el caso de uso:

```text
fase_3/prompts/orders/
fase_3/prompts/returns/
```

La carpeta `orders` contiene las diferentes versiones utilizadas para experimentar con la consulta del estado de pedidos.

La carpeta `returns` conserva las diferentes versiones desarrolladas durante la experimentación de las devoluciones.

Esta organización permite mantener la trazabilidad de la evolución de los prompts y conservar los experimentos realizados.

## Resultados

Los resultados obtenidos durante los experimentos se conservan sin modificar en `fase_3/experiments/results.txt`.

El análisis y comparación de estos resultados se encuentra en `fase_3/analisis_fase_3.md`.

## Reproducibilidad

El proyecto está diseñado para ejecutarse localmente utilizando Python y CPU.

El modelo principal corresponde a `Qwen/Qwen2.5-0.5B-Instruct`.

Los tiempos de ejecución pueden variar dependiendo de los recursos disponibles, especialmente al utilizar modelos de mayor tamaño.

Los archivos de los modelos no se incluyen en el repositorio. El código, los prompts, los datos de prueba, los resultados y la documentación se encuentran disponibles para revisar la metodología y reproducir los experimentos.