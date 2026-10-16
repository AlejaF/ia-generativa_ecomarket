# Embeddings (multilingual-e5-small)

Paráfrasis: 6 pares escritos a mano. 'Sin relación' = cada pregunta con la paráfrasis de otro par. Recuperación: 29 preguntas 'in', k=4, índice en memoria.

| Configuración | Sim. paráfrasis | Sim. sin relación | Brecha | Hit@1 | Hit@4 | MRR | Puntaje top-1 medio |
|---|---|---|---|---|---|---|---|
| con prefijos | 0.900 | 0.819 | 0.081 | 0.90 | 0.97 | 0.93 | 0.887 |
| sin prefijos | 0.918 | 0.845 | 0.073 | 0.79 | 0.97 | 0.87 | 0.897 |

## Escala de Response Relevancy (RAGAS) con estos embeddings

RAGAS compara la pregunta original (`query:`) con las preguntas generadas desde la respuesta (`passage:`). Similitud coseno media de las 10 preguntas evaluadas:

| Modo | Misma pregunta (techo) | Paráfrasis | Suelo, mismo dominio | Suelo, fuera de dominio |
|---|---|---|---|---|
| mezclado (como RAGAS) | 0.946 | 0.885 | 0.811 | 0.772 |
| simétrico (query vs query) | 1.000 | 0.900 | 0.815 | 0.767 |
