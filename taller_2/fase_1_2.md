# Taller Práctico #2

## Implementación de un Sistema RAG para EcoMarket

---

# Contexto y punto de partida

En el Taller 1 el asistente de EcoMarket respondía con un modelo pequeño (`Qwen2.5-0.5B-Instruct`) al que se le entregaba la información en el prompt: el pedido buscado por número de seguimiento y la **política de devoluciones completa**. Los experimentos mostraron dos problemas:

- El modelo aplicaba mal las reglas que combinan varias condiciones (por ejemplo, aceptaba una devolución a los 45 días cuando el plazo es de 30).
- Cuando la información no estaba en el prompt, el modelo tendía a inventarla (por ejemplo, un procedimiento de devolución que la política no contenía).

El objetivo del Taller 2 es que el asistente pueda atender **cualquier tipo de solicitud**: responder con información recuperada de los documentos de EcoMarket cuando existe, y **decir explícitamente que no tiene las herramientas** cuando no existe.

Restricciones de partida: no se dispone de GPU (solo CPU). Los componentes de recuperación (embeddings, base vectorial, reglas) se ejecutan localmente y sin cuentas. El modelo generador, que es el que exige cómputo, usa `openai/gpt-oss-20b` servido por la API de Groq, y el modelo del Taller 1 se conserva como grupo de control para la evaluación (sección 1.3).

---

# Fase 1 — Selección de componentes clave del sistema RAG

## 1.1. Modelo de embeddings

### Opciones evaluadas

| Criterio | `multilingual-e5-small` | `paraphrase-multilingual-MiniLM-L12-v2` | `bge-m3` | `text-embedding-3-small` (OpenAI) |
|---|---|---|---|---|
| Tipo | Código abierto (Hugging Face) | Código abierto (Hugging Face) | Código abierto (Hugging Face) | Propietario (API) |
| Tamaño aproximado | ~118 M parámetros | ~118 M parámetros | ~568 M parámetros | No aplica (servicio) |
| Dimensión del vector | 384 | 384 | 1024 | 1536 |
| Longitud máxima de entrada | 512 tokens | 128 tokens | 8192 tokens | ~8000 tokens |
| Español | Sí (entrenado en ~100 idiomas) | Sí (50+ idiomas) | Sí (100+ idiomas) | Sí |
| Ejecución en CPU | Ligera | Ligera | Pesada para este caso | No se ejecuta localmente |
| Costo de uso | Gratis (solo cómputo local) | Gratis | Gratis | Pago por token |
| Requiere cuenta o internet para consultar | No (tras la descarga inicial) | No | No | Sí |
| Licencia | MIT | Apache 2.0 | MIT | Términos del proveedor |

*Los tamaños y dimensiones son los publicados en las fichas de los modelos; las tarifas de servicios propietarios cambian con el tiempo y deben verificarse antes de una decisión real.*

### Decisión: `intfloat/multilingual-e5-small` (código abierto)

**Justificación:**

1. **Rendimiento para el español.** Es un modelo multilingüe entrenado para recuperación de información, que es exactamente la tarea del sistema: relacionar la pregunta de un cliente con un fragmento de un documento. Un modelo orientado a similitud entre frases (como MiniLM) también funciona, pero está optimizado para comparar oraciones cortas, no para búsqueda de pasajes.
2. **Costo y ejecución en CPU.** Con ~118 M parámetros, indexar los ~52 fragmentos de EcoMarket toma segundos en CPU y cada consulta se vectoriza en una fracción de segundo. No hay costo por uso. `bge-m3` ofrece más capacidad, pero es cerca de cinco veces más grande y esa capacidad no se justifica con un corpus de este tamaño.
3. **Longitud de entrada suficiente.** Admite 512 tokens, y el fragmento más largo del corpus mide 536 caracteres, encabezado incluido (muy por debajo del límite). MiniLM trunca a 128 tokens, lo que podría cortar los fragmentos más largos de la política y de los envíos.
4. **Independencia de servicios externos.** Una vez descargado, funciona sin internet ni claves, y la indexación y la recuperación se pueden reproducir en cualquier equipo. La indexación y la vectorización de la pregunta ocurren en local; solo el generador (sección 1.3) puede usar un servicio externo.
5. **Por qué no un modelo propietario.** Habría mejor calidad potencial y ninguna carga de cómputo local, pero añade costo recurrente, dependencia de un proveedor, necesidad de clave y envío a un tercero de todos los fragmentos y de cada consulta. A diferencia del generador (sección 1.3), donde la API permite una calidad que la CPU no alcanza, aquí un modelo pequeño local ya es suficiente para un corpus pequeño y en español, así que el beneficio no compensa esos costos.

**Detalle de uso:** los modelos E5 esperan un prefijo en el texto: `passage: ` para los fragmentos que se indexan y `query: ` para la pregunta del usuario. Omitirlo degrada la recuperación, por lo que se incorpora en el código y se mide su efecto en la evaluación. Los vectores se normalizan para usar similitud coseno.

**Limitaciones:** es un modelo pequeño; puede confundir preguntas muy cercanas semánticamente (por ejemplo, "¿puedo cancelar?" y "¿puedo devolver?") y no distingue bien identificadores exactos como `ECM10004`. Por eso los pedidos no se buscan por similitud (ver sección 2.1).

## 1.2. Base de datos vectorial

### Opciones evaluadas

| Criterio | ChromaDB | Pinecone | Weaviate |
|---|---|---|---|
| Modelo de despliegue | Embebida en el proceso de Python, persistente en disco | Servicio gestionado en la nube | Servidor propio (Docker) o servicio en la nube |
| Código abierto | Sí (Apache 2.0) | No | Sí (BSD-3) |
| Costo | Gratis | Nivel gratuito limitado; pago al crecer | Gratis autoalojada; pago en la nube gestionada |
| Facilidad de uso | Muy alta: `pip install` y una carpeta | Alta, pero requiere cuenta y clave | Media: requiere levantar y configurar un servicio |
| Escalabilidad | Adecuada para miles a pocos millones de vectores en una máquina; no es un clúster | Muy alta, gestionada | Alta; admite clústeres y búsqueda híbrida |
| Filtrado por metadatos | Sí | Sí | Sí |
| Integración con LangChain | Sí (`langchain-chroma`) | Sí | Sí |
| Internet o cuenta | No | Sí | No (autoalojada) |

### Decisión: ChromaDB

**Ventajas para EcoMarket en este taller:**

- **Cero infraestructura:** la base queda en una carpeta local; quien ejecute el proyecto no necesita Docker, cuentas ni claves.
- **Escala acorde al problema:** ~52 fragmentos. Cualquiera de las tres opciones sobra en capacidad; la diferencia está en el costo operativo, y ahí Chroma es la más simple.
- **Metadatos:** permite guardar la fuente, el tipo de documento y la sección de cada fragmento, lo que sirve para citar de dónde viene cada respuesta y para evaluar la recuperación.
- **Reproducibilidad:** la misma base se puede reconstruir con un solo comando.

**Desventajas y límites:**

- No está pensada para alta concurrencia ni para clústeres. Con miles de consultas simultáneas, o un catálogo de millones de productos, habría que migrar.
- Sin búsqueda híbrida (palabras clave más vectores) incorporada, que ayudaría con identificadores exactos y nombres de producto.

**Cuándo migrar (supuesto de crecimiento):** Pinecone sería razonable si EcoMarket prefiere delegar la operación y acepta el costo; Weaviate si necesita control del despliegue y búsqueda híbrida. Gracias a LangChain, el cambio afecta solo a la capa de almacenamiento, no al resto del flujo.

## 1.3. Modelo generador (adaptación del modelo del Taller 1)

En el Taller 1 el modelo se ejecutó en CPU con `Qwen2.5-0.5B-Instruct`, y se probaron `Qwen2.5-1.5B-Instruct` y una versión cuantizada. Los resultados mostraron que el 0.5B aplicaba mal las reglas con varias condiciones (por ejemplo, aceptaba una devolución a los 45 días cuando el plazo es de 30), que el 1.5B mejoró algunos casos pero siguió aceptando solicitudes fuera de plazo, y que su costo en CPU hacía inviable seguir iterando.

| Opción | Calidad esperada | Costo computacional local | Requisito y costo |
|---|---|---|---|
| `Qwen2.5-0.5B-Instruct` (local, modelo del Taller 1) | Baja: aplicó mal las reglas de devolución | Moderado en CPU | Ninguno. Se conserva como grupo de control |
| `Qwen2.5-1.5B-Instruct` (local) | Mejoró algunos casos, pero siguió fallando el plazo | Alto en CPU | Ninguno |
| Llama 3.1 8B y Llama 3.3 70B (Groq) | No evaluada | Ninguno | Figuran en el catálogo de Groq como "Enterprise, contactar a ventas": no están disponibles para una cuenta estándar. Descartados |
| **`openai/gpt-oss-20b` (Groq)** | Mayor; modelo de razonamiento de pesos abiertos | Ninguno (se ejecuta en el proveedor) | Cuenta y clave; límites de uso; en el plan de pago, $0.075 por millón de tokens de entrada y $0.30 de salida |
| `openai/gpt-oss-120b` (Groq) | Mayor aún, con más latencia | Ninguno | Igual; $0.15 de entrada y $0.60 de salida |
| Otros modelos propietarios por API | Alta | Ninguno | Cuenta y clave de pago, y envío de los datos a un tercero. No se evaluaron: no se dispone de cuenta ni clave |

*Precios y modelos tomados de la documentación de Groq en octubre de 2026; cambian con frecuencia y deben confirmarse en la cuenta del proveedor.*

**Decisión:** usar por defecto `openai/gpt-oss-20b` servido por Groq, y conservar el modelo del Taller 1 como **grupo de control**: se ejecuta en local y sirve para comparar qué parte de la mejora se debe al RAG y a las reglas y qué parte al tamaño del modelo. No se presenta como respaldo, porque su calidad no alcanza para atender clientes. El modelo se configura con la variable `LLM_MODEL`, y el proveedor con `LLM_PROVIDER`. En modo `auto` el sistema usa Groq si hay clave de Groq y el modelo local si no la hay (modo demostrativo, de baja calidad), de modo que el código siempre puede ejecutarse; también se puede forzar con `LLM_PROVIDER=local`. Gracias a LangChain, el generador se aísla en un solo módulo y cambiar de proveedor no modifica el resto del sistema. `gpt-oss-120b` queda como alternativa si la calidad de respuesta del 20B resultara insuficiente.

**Justificación:**

- **El cuello de botella del Taller 1 era la capacidad de cómputo.** La API la traslada al proveedor sin cambiar la arquitectura del sistema.
- **Pesos abiertos.** `gpt-oss` se publica con licencia Apache 2.0 según su fabricante, coherente con la preferencia por código abierto defendida en el Taller 1. Los modelos Llama, que habrían sido otra opción de pesos abiertos, no están disponibles en una cuenta estándar de Groq.
- **Costo y velocidad.** Entre los dos modelos `gpt-oss`, el 20B es el más económico y el más rápido, y para un caso de atención con contexto corto es una elección razonable antes de pasar a uno mayor.
- **Evaluación.** Permite usar métricas de RAGAS que requieren un modelo juez capaz, algo inviable con un 0.5B.
- **El modelo del Taller 1 como grupo de control, no como respaldo.** Con un subconjunto de consultas se compara el mismo flujo (sin RAG, con RAG, con RAG y reglas) usando el modelo local y el de Groq. En la evaluación, sobre las mismas 5 preguntas (costo de envío, un producto que no se vende y tres devoluciones), los aciertos fueron: Groq 2/5 sin RAG, 4/5 con RAG y 5/5 con RAG y reglas; modelo local 0/5, 1/5 y 3/5. Con RAG y sin reglas, el local no acertó ninguna de las tres devoluciones y no usó el mensaje de rechazo ante «¿Venden computadores portátiles?». Son marcas heurísticas revisadas a mano sobre una muestra muy pequeña, que indican dirección y no magnitud; esa diferencia es la razón para no usar el modelo local como respaldo.

**Costos y limitaciones:**

- **Privacidad:** con la API, la pregunta del cliente y los fragmentos recuperados salen al proveedor; los embeddings y la base vectorial permanecen en local. Según la documentación de Groq, no retiene los datos de inferencia por defecto, aunque puede registrarlos hasta 30 días para monitoreo de abusos, y ofrece una opción de retención cero; la documentación consultada no aclara si usa los datos para entrenar. En una operación real habría que revisar el contrato y minimizar los datos enviados.
- **Límites de uso:** la documentación de Groq publica para los modelos `gpt-oss` límites de 30 solicitudes por minuto, 1.000 por día, 8.000 tokens por minuto y 200.000 por día. Estos valores se verificaron en la consola de la cuenta usada para el proyecto (Settings → Limits), donde `openai/gpt-oss-20b` y `openai/gpt-oss-120b` muestran exactamente esas cifras. Los límites son por cuenta y pueden cambiar. El sistema espera lo que indica la cabecera `retry-after` ante un error 429, reintenta un número limitado de veces y pausa entre llamadas en la evaluación. Las evaluaciones de fragmentos, embeddings y recuperación no llaman a la API.
- **Costo:** el uso del proyecto está pensado dentro del plan gratuito. Con los precios publicados del plan de pago, una consulta típica (alrededor de 1.500 tokens de entrada y hasta 1.000 de salida, una estimación propia no medida) costaría una fracción de centavo de dólar. Como referencia medida, según la consola de la cuenta, el día de más actividad del desarrollo (220 solicitudes y unos 139.000 tokens, con la evaluación completa, RAGAS con juez y numerosas pruebas) equivale a alrededor de dos centavos de dólar con esos precios.
- **Dependencia externa:** si el servicio no está disponible o se agota el cupo, el sistema reintenta con espera y, si sigue fallando, informa al usuario del problema en lugar de responder con un modelo distinto sin avisar. No hay un modelo de respaldo automático: el local es demasiado débil para atender clientes y cambiar a él degradaría la calidad sin que el usuario lo note. Se puede usar a propósito con `LLM_PROVIDER=local` (modo demostrativo o comparación), con menor calidad y mayor latencia. Las reglas de devolución siguen aplicándose en ambos casos.
- **Reproducibilidad:** quien ejecute el proyecto con API necesita su propia clave, que se guarda en un archivo `.env` fuera del repositorio. Los resultados de la ejecución con API se guardan en `results/`, indicando modelo y fecha, para poder revisarlos sin ejecutarlos.
- **Las reglas siguen fuera del modelo** (sección 1.6). Con un modelo más capaz, la comparación con y sin verificador muestra cuánto del error del Taller 1 se debía al tamaño del modelo.

## 1.4. Cómo impacta cada componente en la eficacia del sistema

| Componente | Si falla... | Mitigación en el diseño |
|---|---|---|
| Embeddings | La recuperación trae fragmentos irrelevantes y el modelo responde con información equivocada | Modelo orientado a recuperación, prefijos E5, evaluación con preguntas de referencia |
| Base vectorial | Búsquedas lentas o inconsistentes; pérdida del índice | Persistencia en disco, ids deterministas, reindexación con un comando |
| Fragmentación | Reglas cortadas a la mitad o fragmentos sin contexto | Fragmentación según la estructura de cada documento (sección 2.2) |
| Umbral de relevancia | El sistema responde cuando no debería, o rechaza preguntas válidas | Umbral calibrado con preguntas dentro y fuera del alcance |
| Modelo generador | Redacta mal o ignora el contexto | Prompt restrictivo, decodificación determinista, reglas fuera del modelo (sección 1.6) |
| API del generador | Límites de uso, caída del servicio o clave ausente | Espera según `retry-after`, reintentos limitados, pausas en la evaluación; si persiste el fallo, se informa al usuario (sin cambio silencioso de modelo) |

## 1.5. Visión general de la arquitectura

```text
                    Pregunta del cliente
                            │
                            ▼
                  ┌────────────────────┐
                  │ Enrutador (reglas) │
                  └─────────┬──────────┘
        ┌───────────────────┼─────────────────────┐
        ▼                   ▼                     ▼
 Número de pedido      Devolución              Otra consulta
 (ECM + 5 dígitos)     (devol., reembolso)     (envíos, catálogo,
        │                   │                   políticas, FAQ)
        ▼                   ▼                     │
 Búsqueda exacta     Verificador de reglas        │
 en pedidos.json     + RAG (política)             │
        │                   │                     ▼
        │                   │            Recuperación en ChromaDB
        │                   │            (embeddings E5 + umbral)
        │                   │                     │
        │                   │          ┌──────────┴──────────┐
        │                   │          ▼                     ▼
        │                   │   Hay contexto           Sin contexto relevante
        │                   │          │                     │
        └───────────┬───────┴──────────┘                     ▼
                    ▼                              "No cuento con las herramientas
              Modelo generador                      para atender esta solicitud"
      (Groq; local solo en modo demostrativo)                     + escalamiento a agente humano
                    │
                    ▼
            Respuesta al cliente
```

El enrutador se basa en reglas simples (no en el modelo), lo que lo hace rápido, predecible y fácil de auditar. Los pedidos se consultan de forma exacta porque son datos transaccionales que cambian y cuyo identificador debe coincidir literalmente; una búsqueda por similitud no es una herramienta adecuada para eso.

## 1.6. Decisiones que no dependen del modelo generador

El Taller 1 mostró que un modelo, aun con instrucciones claras, puede equivocarse en la decisión y rellenar con información inventada. Por eso tres decisiones se toman con reglas verificables y no con el modelo:

1. **Rechazo por umbral de relevancia.** Si ningún fragmento recuperado supera el umbral, el sistema responde con un mensaje fijo ("no cuento con las herramientas para atender esta solicitud") y ofrece escalar a un agente humano, sin llamar al modelo.
2. **Consulta directa de pedidos** por número de seguimiento (sección 2.1).
3. **Verificador de reglas de devolución.** Comprueba las condiciones de la política (plazo de 30 días, producto sin usar, empaque original, y exclusión de perecederos, higiene personal abierta y personalizados) y entrega un veredicto con sus motivos. El modelo solo redacta la respuesta al cliente apoyándose en ese veredicto y en los fragmentos de la política recuperados. Si faltan datos (por ejemplo, los días desde la entrega), el sistema los pide en lugar de suponerlos. Cuando la devolución se acepta, el sistema añade siempre al contexto las secciones 7 (pasos) y 8 (reembolso) de la política, para que el modelo no invente el procedimiento, y se le exige mencionar solo los motivos que entregó el verificador.

**Transparencia.** El verificador es un interruptor (`USE_RULES`), no un reemplazo del RAG. Con él apagado, el modelo decide con los fragmentos recuperados, como en el Taller 1 pero con recuperación. La evaluación reporta ambos modos por separado, de modo que los aciertos del verificador no se atribuyen al modelo ni al RAG.

**Costo de mantenimiento.** Las reglas existen dos veces: en el texto de la política y en el código. Para reducir el riesgo de que se contradigan, el plazo vive en un único archivo de configuración y una prueba automática falla si ese valor deja de coincidir con el número de días del texto de la política. Aun así, si la política cambia de estructura habrá que revisar el código. Además, el verificador solo funciona cuando puede extraer los datos de la solicitud del cliente, y esa extracción (expresiones regulares) puede interpretar mal frases ambiguas: se corrigieron varios casos que producían decisiones indebidas y se añadieron pruebas con frases límite, pero la lista de frases problemáticas no es exhaustiva.

---

# Fase 2 — Creación de la base de conocimiento de documentos

## 2.1. Identificación de documentos

| Documento | Formato | Contenido | Por qué es crucial |
|---|---|---|---|
| Política de devoluciones | `.txt` | Plazo, condiciones, productos devolvibles y no devolvibles, pasos y reembolso | Es la fuente de las respuestas sobre devoluciones; un error aquí tiene consecuencias económicas |
| Preguntas frecuentes | `.json` | 14 pares pregunta-respuesta sobre envíos, pedidos, pagos, productos y atención | Cubre el grueso de las consultas repetitivas (~80 % según el Taller 1) |
| Catálogo de productos | `.csv` | 21 productos con categoría, material, descripción, precio y si son devolvibles | Permite responder sobre productos y relacionarlos con la política |
| Envíos, pagos y atención | `.md` | Cobertura, tiempos, costos, significado de los estados, cancelaciones, pagos, horarios | Información operativa que los clientes consultan a diario |
| Pedidos | `.json` | 16 pedidos con estado, fecha estimada y enlace de seguimiento | **No se indexa**: se consulta por número de seguimiento (ver abajo) |

Los cuatro primeros forman la base vectorial (4 tipos de documento, 4 formatos distintos). `pedidos.json` queda como fuente estructurada, que se consulta por coincidencia exacta del número de seguimiento. Al modelo no se le envía el campo `customer`, por el principio de minimización de datos del Taller 1.

**¿Por qué `pedidos.json` no se indexa, si RAG permite mantener la información actualizada?** RAG evita reentrenar el modelo: para actualizar el conocimiento basta con reindexar el documento que cambió. Eso funciona muy bien con documentos que cambian de vez en cuando (una política, un precio, un horario). Con los pedidos el caso es distinto:

- *Frecuencia de cambio:* el estado de un pedido puede cambiar varias veces al día. Una copia en el índice vectorial quedaría desactualizada entre reindexaciones, y habría que volver a vectorizar el registro cada vez que cambie un estado. Una consulta directa a la fuente siempre devuelve el estado actual.
- *Tipo de acceso:* el pedido se busca por un identificador exacto, no por significado. Los embeddings no distinguen bien `ECM10004` de `ECM10005`. Un filtro por metadato lo resolvería, pero entonces el almacén vectorial funcionaría como una base de datos más lenta, sin aportar búsqueda semántica.
- *Datos personales:* indexar los pedidos copiaría datos de clientes a un segundo almacén, en tensión con la minimización de datos defendida en el Taller 1.

Indexarlos es técnicamente posible (un documento por pedido, con el número de seguimiento como metadato), y en este taller, con un JSON estático, ambas opciones darían el mismo resultado. Se prefiere la consulta directa porque es la que sigue siendo correcta cuando los datos cambian en producción, y coincide con la arquitectura del Taller 1: datos estructurados por consulta y documentos por RAG.

**Calidad de los documentos.** La calidad de las respuestas está limitada por la calidad de los documentos:

- *Consistencia:* las cifras (plazos, costos, horarios) deben coincidir entre documentos. Se verificó automáticamente que los valores repetidos en las FAQ y en el documento de envíos son idénticos.
- *Completitud:* en el Taller 1, la política decía que el agente debía "explicar los pasos" sin incluirlos, y el modelo inventó un procedimiento. Se añadieron a la política los pasos y el reembolso para que la respuesta correcta exista en la base.
- *Solapamiento intencional:* algunos datos aparecen en dos documentos (por ejemplo, costos de envío en las FAQ y en el documento de envíos; y el plazo de 30 días de la FAQ09 con la política de devoluciones). La razón para repetirlos era la cobertura: las FAQ están redactadas como preguntas y se parecen más a las consultas de los usuarios. Tiene costos: dos fragmentos casi idénticos ocupan dos de los cuatro cupos del top 4, y si un dato cambia hay que actualizar ambas fuentes. El experimento de la sección 2.4 (con y sin las 11 FAQ duplicadas, 12 preguntas de envíos, pagos y pedidos) **no mostró ningún beneficio medible**: Hit@1 0,75 y Hit@4 0,92 en ambos índices, y las dos fuentes aparecieron juntas en el top 4 en las 12 preguntas. Tampoco se ahorra texto al quitarlas: el contexto enviado pasa de 1.160 a 1.227 caracteres por consulta, porque las secciones de envíos son más largas que las FAQ que las repiten, así que el costo real de la duplicación es el mantenimiento y no el tamaño del prompt. Con tan pocas preguntas la medición no es concluyente, pero tampoco respalda la redundancia; en producción convendría una única fuente de verdad. Aquí se mantiene el solapamiento como decisión de prudencia (otras redacciones de pregunta podrían favorecer a la FAQ), con un chequeo automático de consistencia de las cifras repetidas.
- *Datos simulados:* los documentos son ficticios; lo no incluido en la política original del Taller 1 (precios, plazos de envío, medios de pago, horarios, tiempos de reembolso) fue definido para este ejercicio.

## 2.2. Estrategias de segmentación (chunking) evaluadas

| Estrategia | Cómo funciona | Ventajas | Problemas en este caso |
|---|---|---|---|
| Tamaño fijo | Corta cada N caracteres, con solapamiento | Simple y uniforme | Ignora la estructura: puede separar "No se aceptan devoluciones de:" de su lista, partir una fila del catálogo o cortar una tabla |
| Por párrafos | Un fragmento por bloque separado por líneas en blanco | Respeta ideas completas | Los párrafos varían mucho de tamaño; en la política, un encabezado y su lista pueden quedar separados |
| Recursiva | Intenta separar por saltos de sección, luego de párrafo, de línea y de frase, hasta alcanzar el tamaño objetivo | Se adapta al texto y evita cortes bruscos | Sigue sin conocer la estructura propia de un CSV o de un JSON |
| Por estructura del documento | Un fragmento por unidad lógica: sección, registro, par pregunta-respuesta | Cada fragmento es autocontenido y coincide con una unidad de significado | Requiere una regla distinta por tipo de documento |

### Decisión: segmentación por estructura, con segmentación recursiva como respaldo

Los documentos de EcoMarket ya tienen unidades lógicas pequeñas y bien delimitadas, y la mejor fragmentación es la que las respeta. Se aplica una regla por tipo:

| Documento | Unidad del fragmento | Fragmentos | Más largo |
|---|---|---|---|
| Política (`.txt`) | Una sección numerada (1 a 8) | 8 | 536 caracteres |
| FAQ (`.json`) | Un par pregunta-respuesta | 14 | 396 caracteres |
| Catálogo (`.csv`) | Un producto (una fila) | 21 | 296 caracteres |
| Envíos y pagos (`.md`) | Una sección `##` | 9 | 521 caracteres |
| **Total** | | **52** | |

*Cifras medidas con `evaluation/eval_chunks.py` sobre los documentos reales; la longitud incluye el encabezado contextual.*

Reglas adicionales:

- **Encabezado contextual.** Cada fragmento comienza con el nombre del documento y de la sección (por ejemplo, "Política de devoluciones — 3. Productos que no pueden devolverse"). Un fragmento aislado como "Productos perecederos." no tiene sentido sin saber a qué se refiere; con el encabezado, sí.
- **Catálogo en lenguaje natural.** Cada fila se convierte en una frase ("Producto: Taza personalizada con grabado. Categoría: hogar. … No se puede devolver."), y el código `devolvible` se traduce a una oración, porque el modelo de embeddings representa mejor texto natural que valores como `solo_sin_abrir`.
- **Respaldo recursivo.** Si algún fragmento excediera ~600 caracteres (por ejemplo, tras ampliar un documento), se divide con segmentación recursiva (separadores: párrafo, línea, frase) y un solapamiento de ~80 caracteres. Hoy ningún fragmento lo requiere, y el solapamiento no se aplica entre fragmentos que ya son unidades completas.
- **Metadatos.** Cada fragmento guarda `source` (archivo), `doc_type`, `section` o `id`, y un identificador estable (por ejemplo `politica::3`, `faq::FAQ07`, `catalogo::ECO-020`, `envios::cobertura`).

**Por qué importa este paso.** Si la regla de "no se aceptan devoluciones de higiene personal abierta" queda separada de su lista, la recuperación puede traer solo uno de los dos trozos y el modelo responderá con información incompleta. El tamaño también influye: fragmentos demasiado grandes diluyen el significado en el vector y llenan el prompt de ruido (costoso en CPU); fragmentos demasiado pequeños pierden contexto. Los fragmentos de este corpus (≤ 536 caracteres) son suficientemente pequeños para mantener un prompt corto y suficientemente completos para entenderse solos.

## 2.3. Indexación

```text
Documentos (.txt, .json, .csv, .md)
        │
        ▼
 1. Carga y limpieza  ──► normaliza saltos de línea y espacios
        │
        ▼
 2. Fragmentación     ──► 52 fragmentos con encabezado contextual
        │
        ▼
 3. Metadatos         ──► source, doc_type, section/id, chunk_id
        │
        ▼
 4. Embeddings        ──► "passage: " + texto → modelo E5 → vector de 384 dimensiones (normalizado)
        │
        ▼
 5. Carga en ChromaDB ──► colección con distancia coseno, ids deterministas, persistida en disco
```

- **Ids deterministas:** reindexar sobreescribe en lugar de duplicar; el índice se puede reconstruir en cualquier momento con un solo comando.
- **Actualización:** cuando cambia un documento, se vuelve a ejecutar la indexación. Es la ventaja de RAG frente al ajuste fino: no hay que reentrenar nada.
- **Recuperación (parámetros iniciales):** se recuperan los 4 fragmentos más similares a la pregunta (con el prefijo `query: `) con el recuperador de LangChain por umbral de similitud (`similarity_score_threshold`), que descarta los que no lo superan. El umbral se calibra con preguntas de prueba dentro y fuera del alcance, no se fija a ojo ni se toma de otro proyecto, porque la escala de los puntajes depende del modelo de embeddings.
- **Solicitudes fuera de alcance:** si ningún fragmento supera el umbral, el sistema responde con un mensaje fijo ("no cuento con las herramientas para atender esta solicitud") y ofrece escalar a un agente humano, sin depender de que el modelo generador recuerde rehusarse. Esto cubre preguntas sin relación (por ejemplo, de cultura general) y se complementa con una instrucción en el prompt para los casos cercanos al dominio que no están en los documentos (por ejemplo, "¿venden computadores?"). La evaluación mostró cuánto aporta cada capa: con `gpt-oss-20b`, el prompt rechaza las 8 preguntas cercanas al dominio tanto con umbral como sin él, y sin la instrucción de rechazo responde 4 de ellas con afirmaciones que los documentos no sostienen. Es decir, para este generador el umbral ahorra llamadas a la API pero no mejora la exactitud; su valor es proteger a generadores más débiles (con el modelo local la única pregunta probada, D01, no se rechazó) y no depender de una sola capa.

## 2.4. Cómo se evaluará esta fase

La calidad de la base de conocimiento se verifica en cuatro capas, tres de las cuales no requieren el modelo generador. Este plan se ejecutó: los resultados reales están en [resultados.md](resultados.md) y en la carpeta `results/`; la implementación y los experimentos de modificación se explican en [fase_3.md](fase_3.md).

Para las capas 3 y 4 se usa un conjunto de referencia de 43 preguntas: 29 dentro del alcance (devoluciones 9, productos 7, pedidos 5, envíos 4, pagos 3, atención 1), cada una con los fragmentos donde está la respuesta y una frase literal de los documentos; 6 sin relación con EcoMarket (cultura general); y 8 cercanas al dominio cuya respuesta no está en los documentos (por ejemplo, si venden computadores portátiles o si tienen aplicación móvil). Se comprobó automáticamente que los identificadores de los fragmentos y las frases existen en los documentos y que ninguna de las preguntas fuera de contexto está respondida en ellos.

1. **Fragmentos:** estadísticas por documento y un reporte con el texto de todos los fragmentos para revisarlos a mano (que ninguno corte una regla y que cada uno se entienda por sí solo). Además se contrasta la hipótesis de que los fragmentos que mezclan varias unidades diluyen el significado y llenan el prompt de ruido: se compara la fragmentación por estructura con fragmentación de tamaño fijo (1000 y 500 caracteres), aplicada a cada documento por separado, midiendo la recuperación (Hit@k, MRR) y el tamaño del contexto enviado al modelo. En un corpus tan pequeño la diferencia puede ser modesta; se reporta el resultado observado. También se mide el efecto del solapamiento entre las FAQ y el documento de envíos: se compara indexar todo contra indexar sin las FAQ cuyos datos están repetidos, y se cuenta en cuántas consultas ambos duplicados ocupan juntos el top 4.
2. **Embeddings:** comprobar que preguntas parafraseadas se parecen entre sí más que preguntas sin relación, y medir el efecto de usar o no los prefijos `query:` y `passage:`.
3. **Recuperación:** conjunto de preguntas de referencia con el fragmento esperado, medido con Hit@k y MRR y con las métricas de precisión y exhaustividad del contexto basadas en ids de la librería RAGAS, que no requieren un modelo juez.
4. **Fuera de contexto y respuesta completa:** preguntas sin relación con EcoMarket, preguntas cercanas al dominio que no están en los documentos, y comparación de las respuestas con y sin RAG. Con el generador por API, RAGAS añade métricas de fidelidad (qué parte de la respuesta está respaldada por el contexto) y relevancia de la respuesta, evaluadas por un modelo juez sobre un subconjunto de preguntas; si el juez es el mismo modelo que genera, se declara como limitación.

---

# Supuestos y limitaciones de estas fases

- No se dispone de GPU: los componentes de recuperación se ejecutan en CPU y el generador usa una API; el modelo local del Taller 1 se conserva como grupo de control y para ejecutar sin clave en modo demostrativo, con calidad baja.
- El uso de una API implica envío de texto a un tercero, límites de uso que cambian y necesidad de una clave para quien ejecute el proyecto (sección 1.3).
- La base de conocimiento es pequeña y simulada; las conclusiones sobre recuperación no se extrapolan sin más a un catálogo real de miles de productos.
- ChromaDB local es adecuada para este taller, no para una operación con alta concurrencia.
- El rendimiento de `multilingual-e5-small` se evalúa sobre las preguntas de referencia del taller; no se comparó de forma exhaustiva con los otros modelos de la tabla salvo donde se indique en la evaluación.
- Las métricas de fidelidad de RAGAS dependen de un modelo juez; si es el mismo que genera las respuestas, puede favorecer sus propias salidas. Se aplican a un subconjunto de preguntas por los límites de uso de la API.
- El verificador de reglas duplica en código lo que dice la política (sección 1.6). Para limitar el riesgo, el plazo está en un único archivo (`reglas.json`) y un test comprueba que coincide con el texto de la política. Solo opera cuando la solicitud trae los datos necesarios; si no, el sistema los pide.
- Los precios y modelos de la API provienen de la documentación consultada en octubre de 2026, y los límites de uso se verificaron en la consola de la cuenta del proyecto (30 solicitudes por minuto, 1.000 por día, 8.000 tokens por minuto y 200.000 por día para `gpt-oss`). Todos pueden cambiar y los límites dependen de la cuenta de cada usuario; por eso el sistema gestiona los errores 429 con espera y reintento.
