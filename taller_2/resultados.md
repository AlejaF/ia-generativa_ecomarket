# Resultados y experimentos — Taller 2

Resultados completos de la evaluación y de los experimentos de modificación. El [README](README.md) trae solo el resumen; las cifras salen de los archivos de `results/` y la justificación de las decisiones está en [fase_1_2.md](fase_1_2.md).

**Procedencia de las corridas.** La evaluación completa con Groq (`run_all`, punta a punta y experimentos de modificación) es del 16/10/2026. El juez de RAGAS y el grupo de control con el modelo local son del 15/10/2026 y no se repitieron: se ejecutaron antes de los últimos ajustes de `rules.py`, que no cambian los casos de devolución evaluados (los cubre `tests/test_parse_return.py`). Los pasos sin LLM dan el mismo resultado en ambas fechas.

## Resultados (ver `results/`)

Corpus: 52 fragmentos (política 8, FAQ 14, catálogo 21, envíos 9; el más largo mide 536 caracteres). Evaluación:
`gold.json` con 29 preguntas dentro del alcance, 6 sin relación y 8 cercanas al dominio.

**Recuperación** (k=4, 29 preguntas; `results/retrieval.md`)

| Grupo | n | Hit@1 | Hit@4 | MRR |
|---|---|---|---|---|
| total | 29 | 0,90 | 0,97 | 0,93 |
| política | 7 | 1,00 | 1,00 | 1,00 |
| FAQ | 14 | 0,86 | 1,00 | 0,92 |
| catálogo | 7 | 1,00 | 1,00 | 1,00 |
| envíos (solo 1 pregunta) | 1 | 0,00 | 0,00 | 0,00 |

El fallo de Hit@4 es Q18 («¿Puedo pagar cuando me entreguen el pedido?»): la sección de medios de pago solo dice
«No se ofrece pago contra entrega» y no se recupera. En la evaluación punta a punta el sistema responde con el mensaje de
«no cuento con las herramientas» aunque la respuesta existe en los documentos.

**Umbral de relevancia** (`results/threshold.md`): puntaje = similitud coseno del mejor fragmento. El `in` más bajo: 0,837;
el `ooc_facil` más alto: 0,807; `ooc_dificil`: 0,798–0,842. Umbral elegido: **0,822** (punto medio).
Con él: 0/29 preguntas `in` rechazadas, 0/6 `ooc_facil` aceptadas y **4/8 `ooc_dificil` aceptadas** (las debe frenar el prompt).

**Embeddings** (`results/embeddings.md`)

| | Sim. paráfrasis | Sim. sin relación | Hit@1 | Hit@4 | MRR |
|---|---|---|---|---|---|
| con prefijos E5 | 0,900 | 0,819 | 0,90 | 0,97 | 0,93 |
| sin prefijos | 0,918 | 0,845 | 0,79 | 0,97 | 0,87 |

Los prefijos mejoran Hit@1 (0,79 → 0,90) y el MRR; Hit@4 no cambia. Con solo 6 pares de paráfrasis, la similitud media es una
comprobación de cordura, no una medida precisa.

**Fragmentación** (`results/chunking_baseline.md`; hipótesis: los fragmentos que mezclan unidades diluyen el significado y meten ruido)

| Estrategia | Fragmentos | Hit@1 | Hit@4 | Hit@4 por azar | MRR | Caracteres enviados por consulta | % del corpus enviado |
|---|---|---|---|---|---|---|---|
| estructura | 52 | 0,90 | 0,97 | 0,12 | 0,93 | 1109 | 8 % |
| tamaño fijo 1000/0 | 15 | 0,86 | 0,97 | 0,38 | 0,90 | 3453 | 27 % |
| tamaño fijo 500/80 | 36 | 0,86 | 0,97 | 0,17 | 0,91 | 1450 | 11 % |

**Advertencia sobre el empate en Hit@4.** Con tamaño fijo 1000/0 el corpus queda en solo 15 fragmentos grandes, y los 4 que se
recuperan cubren el 27 % del texto total: elegir 4 fragmentos *al azar* ya acierta el 38 % de las veces (12 % con la estructura).
Por eso el 0,97 de las tres estrategias no permite decir que den igual; las diferencias informativas son Hit@1, el MRR y el tamaño del
prompt: la estructura envía ~3 veces menos texto que 1000/0 y ~24 % menos que 500/80. La ventaja en Hit@1 es de una pregunta de 29,
así que no es concluyente: la hipótesis (menos ruido en el prompt) se apoya en el tamaño del prompt, no en una mejora clara de recuperación.

**Solapamiento FAQ/envíos** (12 preguntas de envíos, pagos y pedidos)

| Índice | Fragmentos | Hit@1 | Hit@4 | MRR | Preguntas con fuente válida |
|---|---|---|---|---|---|
| (a) todo | 52 | 0,75 | 0,92 | 0,82 | 12/12 |
| (b) sin las 11 FAQ duplicadas | 41 | 0,75 | 0,92 | 0,83 | 12/12 |

*Cómo se definió el acierto en (b):* una pregunta acierta si alguna frase literal (`texto_clave`) del `gold.json` aparece en los
fragmentos recuperados; no se exige un `chunk_id`. Se comprobó que las 12 preguntas conservan en (b) un fragmento con la respuesta
(la sección de envíos), de modo que ninguna exigía una FAQ eliminada. Sesgos que sí quedan: las 12 preguntas se eligieron por tener fuente
duplicada (el resultado vale solo para ese tipo de pregunta) y son pocas.

La FAQ y la sección que la repite aparecen **juntas en el top 4 en las 12 preguntas** (en 13 de las 29 en total): ocupan dos de los
cuatro cupos. Quitar las FAQ duplicadas **no mostró ningún beneficio medible de mantenerlas** (Hit@1 y Hit@4 idénticos, MRR +0,01 sin
ellas). Con tan pocas preguntas la medición no es concluyente, pero tampoco respalda la redundancia: en producción convendría una única
fuente de verdad. Aquí se mantienen por prudencia (otras redacciones de pregunta podrían favorecer a la FAQ, algo que este experimento no
midió), con el test de consistencia de las cifras repetidas; no se mantienen "por cobertura medida".
**Quitar las FAQ duplicadas tampoco acorta el prompt:** los caracteres enviados por consulta pasan de 1160 a 1227, porque las secciones de
`envios_y_pagos.md` que quedan son más largas que las FAQ que se eliminan.
FAQ09 también repite el plazo y las condiciones de la política y no entra en este experimento.

**RAGAS** (versión 0.4.3)

| Métrica | Resultado |
|---|---|
| Precisión del contexto por ids (sin LLM, 29 preguntas) | 0,34 |
| Exhaustividad del contexto por ids (sin LLM) | 0,90 |
| Faithfulness (juez Groq, 10 preguntas) | 1,00 |
| Response Relevancy (juez Groq, 10 preguntas) | 0,89 (escala comprimida: ver más abajo cómo leerla) |

La precisión por ids es baja por construcción (1–2 fragmentos de referencia y 4 recuperados: máximo 0,25–0,5). Faithfulness = 1,00 en
las 10 preguntas indica respuestas apoyadas en el contexto, pero es un techo que discrimina poco y **el mismo modelo genera y juzga**.
Response Relevancy se calculó con `strictness=1` porque Groq no admite `n>1`, por lo que es más ruidosa.
**Las 10 preguntas juzgadas (Q05, Q08, Q10, Q13, Q14, Q17, Q19, Q20, Q22, Q26) son todas factuales y sencillas**: una cifra, un horario, un
procedimiento corto, un material. No incluyen devoluciones con reglas, preguntas fuera de contexto ni preguntas que combinen documentos, así que el 1,00
de Faithfulness describe el caso sencillo.

**Cómo leer el 0,89 de Response Relevancy: es compatible con relevancia alta (nivel de paráfrasis), pero la escala está comprimida y
discrimina poco.** Esta métrica es la similitud coseno media entre la pregunta original
y las preguntas que el LLM genera a partir de la respuesta, y con E5 todas las similitudes son altas (dos textos sin relación ya dan
~0,82; `results/embeddings.md`). Medido con las mismas 10 preguntas:

| Referencia | Similitud |
|---|---|
| la misma pregunta consigo misma (techo con el modo de RAGAS) | 0,946 |
| paráfrasis | 0,885 |
| **Response Relevancy medida** | **0,89** |
| preguntas sin relación, del mismo dominio | 0,811 |
| preguntas sin relación, de cultura general | 0,772 |

El 0,89 es el nivel de una paráfrasis, unos 0,08 sobre el suelo del mismo dominio y 0,12 sobre el de fuera de dominio, dentro de un
rango útil de solo ~0,14 (0,81–0,95). La escala está comprimida: diferencias de 0,02–0,05 entre respuestas son ruido, y la métrica
sirve para detectar respuestas fuera de tema, no para medir cuánta calidad tiene una respuesta. Por eso el 0,89 no se presenta como
una nota de «buena relevancia», sino como coherente con respuestas sobre el tema de la pregunta.

**Además, RAGAS mezcla prefijos**: compara la pregunta original con `embed_query` (`query:`) y las generadas con
`embed_documents` (`passage:`), por lo que la misma pregunta no llega a 1,0 (0,946; en modo simétrico sería 1,000 y las paráfrasis 0,900
en vez de 0,885). El efecto es de ~0,015 y no cambia la lectura; no se repitió el juez con un adaptador simétrico.

**Punta a punta con Groq** (`gpt-oss-20b`, 11 preguntas; `results/end_to_end_groq_openai_gpt-oss-20b_2026-10-16.md`)

| Condición | Aciertos (11) | Solo devoluciones (4) |
|---|---|---|
| sin RAG | 2 | 2 |
| con RAG | 8 | 2 |
| con RAG + reglas | 10 | 4 |

Sin RAG el modelo inventa (pago contra entrega, garantía de dos años, estado del pedido, plazo de 14 días para tazas personalizadas).
**La línea base «sin RAG» es débil por construcción:** el modelo no conoce EcoMarket, así que inventar es inevitable. Esta comparación mide
el valor de darle contexto al modelo, no el de RAG frente a una alternativa mejor (por ejemplo, meter todos los documentos en el prompt,
algo viable aquí porque los 52 fragmentos suman 13.740 caracteres, aunque no escalaría a un catálogo real; esa alternativa no se evaluó).
El verificador cambia el resultado en dos casos: la taza personalizada (sin reglas el modelo pide más datos en vez de rechazar) y los
audífonos (sin reglas acepta, pero inventa un paso que la política no tiene). Las comprobaciones son heurísticas (regex) sobre 11
preguntas: sirven para ver la diferencia entre condiciones; las respuestas completas están en el archivo.
Consumo de la corrida: 24 llamadas, 8.566 tokens de entrada y 2.010 de salida (límite de la cuenta: 8.000/min y 200.000/día), con
pausa de 20 s entre preguntas.

Dos filas de la tabla se leen con cuidado:

- **Q18 («¿Puedo pagar cuando me entreguen el pedido?») cuenta «no» en las tres condiciones, pero no es lo mismo.** Sin RAG el modelo
  afirma algo falso: «Claro, puedes pagar en el momento de la entrega» (EcoMarket no ofrece pago contra entrega). Con RAG, la sección
  correcta no se recupera y el sistema responde el rechazo seguro («no cuento con las herramientas…»), que es una respuesta insuficiente
  pero no engañosa. Hay un fallo de cobertura en un caso y desinformación en el otro, y la marca binaria los iguala.
- **P1 (pedido ECM10004): la fila «con_rag» no es RAG.** El enrutador la manda al flujo de pedidos (búsqueda exacta en `pedidos.json` y
  el LLM solo redacta). La comparación con «sin RAG» (que inventó «está en tránsito y llegará en 2-3 días») está en tener o no los datos del
  pedido, y no entre recuperación semántica y su ausencia.

**Grupo de control con el modelo local** (`Qwen2.5-0.5B-Instruct`, 5 preguntas; `results/end_to_end_local_*.md`)

| Condición | Aciertos (5) | Solo devoluciones (3) |
|---|---|---|
| sin RAG | 0 | 0 |
| con RAG | 1 | 0 |
| con RAG + reglas | 3 | 2 |

**Las mismas 5 preguntas (Q08, D01, R1, R2, R3) en Groq y en local** (calculado desde los `.json` guardados, sin generar):

| Condición | Groq `gpt-oss-20b` (5) | Local `Qwen2.5-0.5B` (5) |
|---|---|---|
| sin RAG | 2 | 0 |
| con RAG | 4 | 1 |
| con RAG + reglas | 5 | 3 |

Es una muestra pequeña (5 preguntas, una corrida).

Con RAG y sin reglas, el modelo local no acierta ninguna de las 3 devoluciones: declara «válida» tanto la devolución de la **crema abierta**
(la política rechaza higiene personal abierta) como la de la **camiseta a los 45 días**, y en los audífonos no da los pasos de la política.
**El verificador corrige dos casos, la crema y la camiseta** (con reglas ambos pasan a «rechazada»); la tercera devolución (audífonos) sigue
fallando: el modelo ignora el veredicto «aceptada» y los pasos de la política, y repite las condiciones generales.

Ante «¿Venden computadores portátiles?» el local no usa el mensaje de rechazo (responde
que no los venden y recomienda otras tiendas). Son los mismos errores del modelo pequeño del Taller 1.

Nota sobre la heurística: la primera versión contó como acierto la respuesta de la crema («es válida… si no cumple con estas condiciones…»)
porque leyó esa frase condicional como rechazo. Al revisarla, se corrigió y se **reevaluó desde los `.json` guardados, sin volver a
generar nada** (`--reevaluar`): la única marca que cambió fue esa; las cifras de Groq (2/8/10 de 11) no cambiaron.


## Experimentos de modificación

Tres cambios deliberados al sistema, para ver qué pieza hace qué (`python -m evaluation.eval_modificaciones`;
resultados completos en `results/modificaciones_groq_openai_gpt-oss-20b_2026-10-16.md`).

**1. Cambiar k, el número de fragmentos recuperados** (`K` en `src/config.py`; **n = 29** preguntas, sin LLM)

| k | Hit@k | MRR | Caracteres enviados por consulta |
|---|---|---|---|
| 1 | 0,90 | 0,90 | 291 |
| 2 | 0,93 | 0,91 | 536 |
| 4 (actual) | 0,97 | 0,93 | 1109 |
| 6 | 0,97 | 0,93 | 1696 |

Pasar de k=1 a k=4 sube Hit@k de 0,90 a 0,97 a cambio de ~3,8 veces más texto en el prompt; k=6 no mejora nada (0,97) y añade un 53 % más
de texto. k=2 es un punto intermedio (0,93 con la mitad del texto de k=4). Se mantiene k=4 porque es donde la curva se aplana, no porque
sea óptimo: con 29 preguntas, 0,93 frente a 0,97 es una diferencia de una pregunta.

**2. Cambiar el prompt: quitar la instrucción de rechazo** (se elimina de `RAG_SYSTEM` en `src/rag_chain.py` la línea «Si el contexto no
contiene la respuesta… responde exactamente…»; **n = 8** preguntas cercanas al dominio (`ooc_dificil`), `gpt-oss-20b`, una
generación por pregunta y configuración, 12 llamadas en total)

| Configuración | Preguntas respondidas (de 8) |
|---|---|
| actual (umbral + instrucción de rechazo) | 0 |
| sin la instrucción de rechazo (umbral sí) | 4 |
| sin umbral (instrucción sí) | 0 |

Sin la instrucción, las 4 preguntas que superan el umbral (venden computadores, tienda física en Bogotá, pago en cuotas, ropa para niños)
pasan de rechazarse a responderse, siempre con un «No, …» del estilo «EcoMarket no tiene tienda física en Bogotá» o «no ofrece la opción de
pagar en cuotas». Son afirmaciones que los documentos no sostienen. Las otras 4 siguen
rechazadas porque no superan el umbral.

**Conclusión: con `gpt-oss-20b` el prompt rechaza las 8 preguntas con o sin umbral**, así que el umbral ahorra llamadas (4 de las 8 ni
llegan al modelo) pero **no mejora la exactitud en este caso**. Lo que impide las respuestas inventadas es la instrucción del prompt.
Alcance: solo estas 8 preguntas y este modelo; no se probó el prompt sin umbral en las 6 preguntas de cultura general. Sobre el
modelo local: **solo se probó con una pregunta**, «¿Venden computadores portátiles?» (D01, en el grupo de control), donde la instrucción
no bastó (el modelo respondió que no los venden en vez de usar el mensaje de rechazo); no se probó con las otras 7, así que es un indicio
de que el umbral podría ser la protección que queda con ese modelo, no una conclusión.

**3. Cambiar el código: no añadir las secciones 7 y 8 en devoluciones aceptadas** (quitar el `get_chunks(["politica::7", "politica::8"])` de
`answer_return` en `src/app.py`; **n = 2** devoluciones distintas aceptadas por el verificador, una generación por caso y variante, sin repeticiones. El «1/3» sale de dos casos independientes que dieron el mismo resultado)

Elementos de la política que debe contener la respuesta: escribir a `soporte@ecomarket.example`, entregar a la transportadora y reembolso en 5 a 10 días.

| | Con secciones 7 y 8 (actual) | Sin secciones 7 y 8 |
|---|---|---|
| Audífonos, 10 días | 3/3 | 1/3 |
| Botella de acero, 20 días | 3/3 | 1/3 |

Sin esas secciones el modelo recibe solo fragmentos de condiciones y plazos y rellena los pasos con procedimientos que la política no contiene
(«Incluye el formulario de devolución y la factura de compra», «Adjunta el formulario de devolución que recibiste al hacer la compra»). El
reembolso sí sale bien porque en estos dos casos `politica::8` entra por sí sola en el top 4, mientras que `politica::7` (los pasos) no. Es el mismo defecto que el Taller 1 atribuía al modelo pequeño, aquí con un modelo
mucho más capaz: el contexto que falta se rellena inventando, sea cual sea el modelo.
