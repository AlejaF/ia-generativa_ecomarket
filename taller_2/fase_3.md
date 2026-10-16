# Fase 3 — Implementación del RAG con LangChain

Esta fase explica el código de `taller_2/`: qué se adaptó del Taller 1, cómo funciona cada pieza, qué ocurre al
modificarlas y qué límites tiene. Cómo ejecutarlo está en [README.md](README.md); las tablas completas de resultados, en [resultados.md](resultados.md);
la justificación de cada componente (embeddings, base vectorial, fragmentación, generador) está en [fase_1_2.md](fase_1_2.md).

## 1. Qué se adaptó del Taller 1

El Taller 1 era un asistente de EcoMarket con un modelo pequeño local (Qwen2.5-0.5B-Instruct) al que se le entregaba la información
dentro del prompt: el pedido, buscado por número de seguimiento, y la **política de devoluciones completa**. Sus errores eran de dos
tipos: **inventaba** lo que no estaba en el prompt (por ejemplo, un procedimiento de devolución) y **decidía mal** las devoluciones con
reglas (por ejemplo, aceptaba una devolución a los 45 días). El Taller 2 conserva la idea y cambia tres cosas:

| Taller 1 | Taller 2 | Por qué |
|---|---|---|
| La información (pedido y política completa) iba entera en el prompt y solo cubría esos temas | Se recuperan solo los fragmentos relevantes de varios documentos (política, FAQ, catálogo, envíos) y se rechaza lo que no está (RAG) | Meter todo en el prompt no escala a más documentos ni permite decir «no lo sé» |
| El modelo decide si una devolución procede | Un verificador en código decide; el modelo solo redacta | Las reglas se pueden comprobar, y un modelo pequeño las incumple |
| Un modelo local pequeño | Groq (`gpt-oss-20b`) por defecto; el modelo local queda como grupo de control | En CPU, el modelo pequeño es lento y de baja calidad |

Del Taller 1 se reutilizan el formato de respuesta de pedidos (`Estado / Entrega estimada / Mensaje`), los tres casos de
devolución (audífonos, crema abierta, camiseta a los 45 días) y el modelo local, que ahora sirve de comparación.

**Cómo se ajustó el modelo del Taller 1.** El modelo del Taller 1 (`Qwen2.5-0.5B-Instruct`, local, en CPU) se conserva y se le incorpora
el RAG: en lugar de recibir la política completa en el prompt, recibe solo los fragmentos recuperados, y las devoluciones pasan por el
verificador de reglas. Ese flujo corre con el modelo del Taller 1 si se usa `LLM_PROVIDER=local` (o si no hay clave), y su resultado está
medido: sobre las mismas 5 preguntas acierta 0 sin RAG, 1 con RAG y 3 con RAG y reglas. Como su calidad no alcanza para atender clientes,
el generador por defecto es `gpt-oss-20b` en Groq (que acierta 2, 4 y 5 en esas mismas preguntas), y el modelo del Taller 1 queda como
grupo de control: permite separar lo que aportan el RAG y las reglas de lo que aporta el tamaño del modelo. No se importa código de
`taller_1/`, para que el proyecto sea autocontenido; solo se reutiliza el patrón de su clase `LocalLLM` (plantilla de chat, generar,
decodificar solo los tokens nuevos).

### 1.1 Las etapas del flujo y dónde está cada una

El RAG es una secuencia de etapas. Las primeras (cargar, fragmentar, embeber e indexar) se ejecutan una vez con `python -m src.ingest`;
las demás se ejecutan en cada pregunta:

| Etapa | Módulo | Qué hace | Dónde se justifica |
|---|---|---|---|
| Cargar | `chunking.py` | Lee los 4 tipos de documento (`.txt`, `.json`, `.csv`, `.md`), cada uno con su lector. Los pedidos no se cargan aquí: los consulta `orders.py` | [fase_1_2.md](fase_1_2.md) §2.1 |
| Fragmentar | `chunking.py` | Un fragmento por unidad lógica (sección, pregunta-respuesta o producto): 52 fragmentos con encabezado y metadatos | §2.2 de [fase_1_2.md](fase_1_2.md) y [resultados.md](resultados.md) |
| Embeber | `embeddings.py` | `multilingual-e5-small` con prefijos `passage:` / `query:` y vectores normalizados | §1.1 de [fase_1_2.md](fase_1_2.md) |
| Indexar | `ingest.py` | Guarda los vectores y metadatos en Chroma (`chroma_db/`), con distancia coseno e ids deterministas | §1.2 y §2.3 de [fase_1_2.md](fase_1_2.md) |
| Recuperar | `retriever.py`, `config.py` | Busca los 4 fragmentos más cercanos y descarta los que no superan el umbral de 0,822 | §2.3 de este documento |
| Generar | `rag_chain.py`, `llm.py` | Cadena de LangChain `prompt \| llm \| StrOutputParser` con Groq o con el modelo local | §2.4 y §2.7 de este documento |
| Decidir el camino | `router.py`, `app.py`, `rules.py`, `orders.py` | Enrutador, consulta exacta de pedidos y verificador de devoluciones | §2.2, §2.5 y §2.6 de este documento |
| Evaluar | `evaluation/` | `gold.json` con 43 preguntas y métricas (Hit@k, MRR, RAGAS) | [resultados.md](resultados.md) |

## 2. Cómo funciona el código

### 2.1 El recorrido de una pregunta

```
Pregunta -> router.py (regex)
   |-- contiene ECM + 5 dígitos -> pedido    : búsqueda exacta en pedidos.json -> LLM redacta
   |-- contiene devol/reembols/reintegr -> devolución
   |        |-- sin datos de un caso concreto -> se trata como pregunta de política (RAG)
   |        |-- con datos: verificador (rules.py) decide -> LLM redacta con la política
   `-- cualquier otra -> RAG: recuperación + umbral -> LLM responde con el contexto
```


### 2.2 `router.py`: decidir el camino

Dos expresiones regulares y un orden de prioridad (pedido, devolución, otro). No llama a ningún modelo: es instantáneo,
predecible y se puede auditar leyendo unas pocas líneas. Su costo es que solo reconoce las palabras previstas.

### 2.3 Recuperación y umbral (`retriever.py`, `config.py`)

1. La pregunta se convierte en un vector con el modelo de embeddings E5 (con el prefijo `query: `).
2. Chroma devuelve los `K = 4` fragmentos más parecidos (similitud coseno) de los 52 que se indexaron.
3. Solo pasan los que superan `RELEVANCE_THRESHOLD = 0,822`. Si ninguno pasa, `answer_rag` devuelve el mensaje fijo
   `NOT_AVAILABLE` **sin llamar al LLM**.

El umbral se calibró con las 43 preguntas de `gold.json` (29 dentro del alcance, 6 sin relación, 8 cercanas): las preguntas dentro
del alcance puntúan desde 0,837 y las de cultura general hasta 0,807, así que 0,822 queda entre ambos grupos. El margen es de
0,03: es estrecho. Las 8 preguntas cercanas al dominio no intervienen en el cálculo: ningún umbral las separa de las válidas sin
rechazar preguntas dentro del alcance (D06 puntúa 0,842, más que el `in` más bajo, 0,837), así que las cubre el prompt.

### 2.4 `rag_chain.py`: la cadena de LangChain

El corazón del taller son dos líneas:

```python
prompt = ChatPromptTemplate.from_messages([("system", system), ("human", human)])
return prompt | get_llm() | StrOutputParser()
```

Es una cadena LCEL (LangChain Expression Language): el `|` conecta tres piezas, y la salida de cada una es la entrada de la siguiente.

| Pieza | Qué recibe | Qué entrega |
|---|---|---|
| `ChatPromptTemplate` | un diccionario, por ejemplo `{"context": ..., "question": ...}` | los mensajes `system` + `human` con los huecos rellenos |
| `get_llm()` | esos mensajes | la respuesta del modelo (Groq o local) |
| `StrOutputParser` | la respuesta del modelo | solo el texto, como `str` |

Se usa así: `cadena.invoke({"context": ..., "question": ...})`.

`build_chain(system, human)` construye la misma estructura con distintos prompts, y de ahí salen las cinco cadenas:

| Cadena | Para qué | Prompt |
|---|---|---|
| `rag_chain` | preguntas generales | `RAG_SYSTEM`: responde SOLO con el contexto, cita los ids y, si no está, dice el mensaje fijo |
| `order_chain` | pedidos | `ORDER_SYSTEM`: formato fijo, sin inventar |
| `return_chain(True)` | devoluciones con verificador | `RETURN_RULES_SYSTEM`: el veredicto ya está decidido, no lo cambies |
| `return_chain(False)` | devoluciones sin verificador | `RETURN_FREE_SYSTEM`: decide el modelo (solo para comparar) |
| `plain_chain` | línea base sin RAG | solo `ROLE` y la pregunta; no se usa en el chat |

Detalles que importan:

- `format_context` antepone a cada fragmento su `chunk_id` entre corchetes. Así el modelo puede citar la fuente y nosotros
  comprobar de dónde salió cada dato.
- `NOT_AVAILABLE` se usa en dos sitios: es lo que devuelve el código cuando el umbral rechaza, y es lo que se le ordena decir al modelo
  si el contexto no contiene la respuesta. La misma frase en ambos casos hace que el comportamiento sea uniforme.
- El prompt pide texto plano, pero los modelos a veces añaden Markdown; `to_plain_text` lo limpia porque la consola no lo muestra.
- La decodificación es determinista (`temperature=0` en Groq, `do_sample=False` en el modelo local): la misma pregunta casi siempre da
  la misma respuesta, lo que hace la evaluación repetible. En Groq no hay garantía absoluta, porque el servidor puede variar levemente.

### 2.5 `app.py`: los tres flujos

- **`answer_order`**: extrae el número, busca el pedido en `pedidos.json` (búsqueda exacta, los pedidos no se indexan) y pasa al
  modelo solo los campos necesarios: **el nombre del cliente nunca llega al modelo**. Si el número no existe, responde sin LLM.
- **`answer_rag`**: recupera con umbral; si no hay fragmentos, mensaje fijo; si hay, ejecuta la cadena RAG.
- **`answer_return`**: es el flujo más cuidado.
  1. Extrae del texto producto, días, estado y empaque (regex en `rules.py`).
  2. Si no hay ningún dato, es una pregunta de política («¿cuántos días tengo?») y va al RAG normal.
  3. Si hay datos, recupera solo de la política (sin umbral, porque el enrutador ya decidió el tema).
  4. `check_return` devuelve `aceptada` (sí, no o `None`), los motivos y los datos faltantes. Si faltan datos, **se piden**, no se adivinan.
  5. Si el veredicto es «aceptada», el código añade siempre las secciones 7 (pasos) y 8 (reembolso) de la política, aunque no estén
     en el top 4, porque sin ellas el modelo inventa los pasos.
  6. El modelo redacta con el veredicto y los motivos: **el código decide, el modelo explica**.

`lru_cache` crea una sola vez el almacén, el recuperador y cada cadena, porque cargar el modelo de embeddings es lo costoso.
`--solo-recuperacion` muestra fragmentos, puntajes y veredicto sin cargar ningún LLM: sirve para depurar la recuperación sin gastar cuota.

### 2.6 `rules.py`: el verificador de devoluciones

Tiene dos partes separadas:

- **`parse_return_request(texto)`** extrae del mensaje del cliente producto, días, si está usado o abierto, y si conserva el empaque,
  con expresiones regulares. Lo que no se menciona queda en `None`. El producto se busca en `catalogo.csv` contando cuántas palabras
  de su nombre aparecen; si dos productos empatan con distinta categoría, devuelve `None` y se pregunta.
- **`check_return(...)`** aplica la política con `if` simples: producto no devolvible, higiene abierta, producto usado, sin empaque,
  más de `PLAZO_DIAS` días (el plazo se lee de `reglas.json`). Si ya hay un motivo de rechazo, rechaza sin pedir más datos; si no hay
  rechazo y faltan datos, devuelve `aceptada=None` y la lista de faltantes; si todo cumple, acepta.

La decisión es código determinista y comprobable; **el punto débil es la extracción**: una expresión regular puede interpretar mal una
frase ambigua, y entonces el veredicto se calcula sobre datos equivocados. Por eso, ante la duda, el diseño prefiere dejar el dato en
`None` y preguntar, y se prueba con frases límite (ver `tests/`).

### 2.7 `llm.py`: el generador

`get_llm()` devuelve un `RunnableLambda`, que es lo que permite colocarlo en medio de la cadena con `|`.

- **Groq** (`ChatGroq`, `gpt-oss-20b`): `temperature=0` y `reasoning_effort="low"` (es un modelo de razonamiento; ese esfuerzo bajo gasta
  menos tokens). El razonamiento queda aparte del texto final. Si Groq responde 429 (límite de uso), el código espera el tiempo que indica
  la cabecera `retry-after` y reintenta hasta 3 veces; si no se resuelve, lanza `LLMError` con un mensaje claro y **no cambia de modelo
  en silencio**.
- **Local** (`Qwen2.5-0.5B-Instruct`): el mismo patrón del Taller 1 (plantilla de chat, generar, decodificar solo los tokens nuevos),
  en CPU y sin muestreo.
- Un contador (`USAGE`) suma llamadas y tokens, para vigilar el límite diario de la API.
- `LLM_PROVIDER=auto` usa Groq si hay `GROQ_API_KEY` y, si no, el modelo local con un aviso.

### 2.8 Dónde vive cada decisión

| Quiero cambiar… | Archivo | Qué se espera ver |
|---|---|---|
| cuántos fragmentos se recuperan | `K` en `src/config.py` | más contexto y más tokens por consulta |
| el umbral de relevancia | `RELEVANCE_THRESHOLD` en `src/config.py` | más rechazos si sube; más respuestas dudosas si baja |
| usar o no el verificador | `USE_RULES` (variable de entorno o `.env`) | sin él, decide el modelo |
| lo que le pedimos al modelo | `RAG_SYSTEM` etc. en `src/rag_chain.py` | cambia cómo rechaza, cita o redacta |
| qué se añade en devoluciones aceptadas | `answer_return` en `src/app.py` | cambia si salen los pasos y el reembolso |
| el plazo de devolución | `src/reglas.json` | un test falla si no coincide con la política |

## 3. Experimentos de modificación (resultados reales, ver resultados.md)

| Cambio | Qué se observó |
|---|---|
| `K` de 1 a 4 a 6 (n = 29, sin LLM) | Hit@k 0,90 → 0,97 → 0,97; con k = 6 hay 53 % más de texto sin mejora |
| Quitar del prompt la instrucción de rechazo (n = 8 preguntas cercanas al dominio) | respondidas: 0 con el prompt actual, 4 sin la instrucción; las 4 son afirmaciones que los documentos no sostienen («no tiene tienda física en Bogotá») |
| Quitar el umbral conservando el prompt | también 0 respondidas: con `gpt-oss-20b` el umbral ahorra llamadas pero no mejora la exactitud |
| No añadir las secciones 7 y 8 en devoluciones aceptadas (n = 2, ilustrativo) | la respuesta incluye 1 de 3 elementos de la política en vez de 3; inventa «formulario de devolución» y «factura» |
| Quitar el verificador (11 preguntas, Groq) | devoluciones correctas 2/4 → 4/4 con verificador; en el modelo local 0/3 → 2/3 |
| Quitar RAG (11 preguntas, Groq) | aciertos 2/11 sin RAG, 8/11 con RAG, 10/11 con RAG + reglas |
| Cambiar el generador, mismas 5 preguntas (sin RAG / con RAG / con RAG + reglas) | Groq 2/5, 4/5, 5/5; modelo local 0/5, 1/5, 3/5: RAG y reglas suman ~3 aciertos con ambos modelos, y el modelo grande suma entre 2 y 3 aciertos más en cada condición |
| Quitar los prefijos E5 | Hit@1 0,90 → 0,79 |

Lectura general: cada pieza evita un tipo distinto de error. El RAG aporta los datos; el prompt impide inventar cuando el dato
no está; el umbral evita llamadas inútiles y protege a modelos débiles; el verificador aplica las reglas con código comprobable (siempre que los datos se extraigan bien); las secciones 7 y 8
evitan pasos inventados. Las cifras salen de muestras pequeñas (entre 2 y 29 preguntas): indican dirección, no magnitud.

## 4. Limitaciones y supuestos

- **Documentos y preguntas simulados.** Los documentos son ficticios y las 43 preguntas de `gold.json` no son suficientes para profundizar en las evaluaciones, así que las cifras son optimistas. Las comprobaciones de las respuestas completas usan expresiones regulares
  revisadas a mano y sirven para comparar condiciones, no como medida precisa.
- **Umbral con poco margen.** Se calibró con las mismas preguntas con las que se evalúa y la separación es de 0,03. Con otros
  documentos u otro modelo de embeddings hay que recalibrar.
- **Fallo conocido de recuperación.** «¿Puedo pagar cuando me entreguen el pedido?» (Q18) no recupera la sección correcta y el
  sistema responde con el rechazo seguro aunque el dato existe.
- **El verificador solo entiende lo que sus regex extraen** (producto, días, estado, empaque), y una frase ambigua mal interpretada
  produce un veredicto equivocado (la lógica es correcta, la extracción puede fallar). Frases como «hace un mes» no se reconocen y
  se pide el dato. La conversación no tiene memoria: los datos de la devolución deben ir en un solo mensaje. Si la política cambia de estructura, hay que revisar el código.
- **Las secciones 7 y 8 se añaden por una regla fija** ligada a la estructura de la política, no por recuperación.
- **Generador y evaluación.** El mismo modelo genera y, en RAGAS, juzga; Faithfulness 1,00 describe solo 10 preguntas fáciles, y Response
  Relevancy tiene una escala muy comprimida con E5. Con el modelo local solo se probó una pregunta cercana al dominio.
- **Dependencia externa.** Con Groq, la pregunta y los fragmentos salen a un tercero (los embeddings y la base vectorial no) y hay límites
  de cuota; si la API falla, el sistema informa el error y no cambia de modelo en silencio.
- **No se evaluó** la alternativa de meter todos los documentos (los 52 fragmentos suman 13.740 caracteres) en el prompt, viable en este corpus pero no escalable.
- **Supuestos:** solo CPU; la persona ejecuta con su propia clave de Groq o sin clave (modelo local, lento y de baja calidad);
  los pedidos se consultan por número exacto; las claves viven solo en `.env`, que no se sube al repositorio.