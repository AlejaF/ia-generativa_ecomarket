# EcoMarket — IA Generativa

Talleres de IA generativa aplicados a la atención al cliente de EcoMarket, una tienda de e-commerce ficticia. Cada taller está en su
propia carpeta y se ejecuta desde ella.

| Taller | Carpeta | Tema |
|---|---|---|
| Taller 1 | [`taller_1/`](taller_1/) | Ingeniería de prompts con un modelo local pequeño: consulta de pedidos y evaluación de devoluciones |
| Taller 2 | [`taller_2/`](taller_2/) | Sistema RAG con LangChain para atender cualquier solicitud o decir que no tiene las herramientas |

## Taller 1

Documentación en [`taller_1/fase_1_2.md`](taller_1/fase_1_2.md) y [`taller_1/fase_3/analisis_fase_3.md`](taller_1/fase_3/analisis_fase_3.md);
instrucciones de ejecución en [`taller_1/README.md`](taller_1/README.md) (los comandos de la Fase 3 se ejecutan desde `taller_1/fase_3`).

## Taller 2 — dónde está cada parte

| Parte del taller | Dónde |
|---|---|
| Fase 1: selección de componentes (embeddings y base de datos vectorial) | [`taller_2/fase_1_2.md`](taller_2/fase_1_2.md), sección «Fase 1» |
| Fase 2: base de conocimiento (documentos, chunking e indexación) | [`taller_2/fase_1_2.md`](taller_2/fase_1_2.md), sección «Fase 2» |
| Fase 3: explicación del código, experimentos y limitaciones | [`taller_2/fase_3.md`](taller_2/fase_3.md) |
| Fase 3: código | [`taller_2/src/`](taller_2/src/) |
| Cómo ejecutarlo (con clave de Groq propia o sin clave) | [`taller_2/README.md`](taller_2/README.md) |
| Resultados de la evaluación y experimentos de modificación | [`taller_2/resultados.md`](taller_2/resultados.md) y [`taller_2/results/`](taller_2/results/) |

Resumen para ejecutarlo (detalles, requisitos y alternativas en [`taller_2/README.md`](taller_2/README.md)):

```powershell
cd taller_2
pip install -r requirements.txt
python -m src.ingest
python -m src.app
```
