# Ablación de la fragmentación

Hipótesis: los fragmentos que mezclan varias unidades diluyen el significado y meten ruido en el prompt.
29 preguntas 'in', k=4, mismos embeddings. Acierto por `texto_clave`. Cada estrategia se aplica por documento. En tamaño fijo, faq y catálogo se parten desde su texto en lenguaje natural (una línea por registro).

| Estrategia | Fragmentos | Hit@1 | Hit@4 | Hit@4 por azar | MRR | Caracteres enviados por consulta | % del corpus enviado |
|---|---|---|---|---|---|---|---|
| estructura | 52 | 0.90 | 0.97 | 0.12 | 0.93 | 1109 | 8 % |
| tamaño fijo 1000/0 | 15 | 0.86 | 0.97 | 0.38 | 0.90 | 3453 | 27 % |
| tamaño fijo 500/80 | 36 | 0.86 | 0.97 | 0.17 | 0.91 | 1450 | 11 % |

**Cómo leer Hit@4:** «por azar» es la probabilidad de acertar eligiendo 4 fragmentos al azar (misma definición de acierto). Con pocos fragmentos grandes el azar ya acierta mucho, así que el empate en Hit@4 entre estrategias dice poco; las diferencias informativas son Hit@1, MRR y el tamaño del prompt.

# Solapamiento FAQ / envíos

Se quitan las FAQ01–08, 10, 11 y 14 (sus datos están repetidos en envios_y_pagos.md). 12 preguntas de envíos, pagos y pedidos.

**Definición de acierto:** una pregunta acierta si alguna `texto_clave` literal aparece en los fragmentos recuperados (no se exige un `chunk_id`, así que el índice (b) no se penaliza por no tener las FAQ). Columna «con fuente válida»: preguntas para las que el índice contiene al menos un fragmento con la respuesta.

| Índice | Fragmentos | Hit@1 | Hit@4 | Hit@4 por azar | MRR | Caracteres enviados | Preguntas con fuente válida |
|---|---|---|---|---|---|---|---|
| (a) todo | 52 | 0.75 | 0.92 | 0.14 | 0.82 | 1160 | 12/12 |
| (b) sin FAQ duplicadas | 41 | 0.75 | 0.92 | 0.10 | 0.83 | 1227 | 12/12 |

Consultas con una FAQ y la sección que la repite juntas en el top 4 (índice completo):

- preguntas de envíos/pagos/pedidos: 12/12
- las 29 preguntas 'in': 13/29

Sesgos conocidos: (1) las 12 preguntas se eligieron justamente por tener fuente duplicada, así que el experimento responde solo para ese tipo de pregunta; (2) quitar las FAQ libera cupos del top 4 y las FAQ, redactadas como preguntas, se parecen más a la consulta del cliente, pero en estos datos ese efecto no se tradujo en diferencias de Hit.

Nota: FAQ09 también repite el plazo y las condiciones de la política (gold.json acepta ambas fuentes en Q01 y Q07); no entra en este experimento.
