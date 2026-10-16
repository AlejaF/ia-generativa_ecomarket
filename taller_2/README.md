# Taller 2 — RAG para EcoMarket

Chatbot de atención al cliente que responde con información recuperada de los documentos de EcoMarket
(RAG con LangChain) o dice que no tiene las herramientas para atender la solicitud.

Parte del Taller 1: su modelo local (`Qwen2.5-0.5B-Instruct`) funciona con RAG en el modo sin clave; por calidad, el generador
por defecto es `gpt-oss-20b` en Groq y el modelo del Taller 1 queda como grupo de control (ver [fase_3.md](fase_3.md), sección 1).

- [fase_1_2.md](fase_1_2.md): justificación de cada componente (embeddings, base vectorial, generador, fragmentación).
- [fase_3.md](fase_3.md): explicación del código (qué se adaptó del Taller 1, cómo funciona cada pieza, qué pasa al modificarla).
- [resultados.md](resultados.md): resultados completos de la evaluación y experimentos de modificación.

```
Pregunta -> enrutador por reglas -> pedido     : búsqueda exacta en pedidos.json -> LLM redacta
                                 -> devolución : verificador de reglas (+ política recuperada) -> LLM redacta
                                 -> otra       : recuperación en Chroma + umbral -> LLM responde con el contexto
                                                 (si ningún fragmento supera el umbral: mensaje fijo, sin LLM)
```

## Cómo ejecutarlo

Requisitos: Python 3.10, solo CPU (no hace falta GPU). Los comandos se ejecutan desde esta carpeta (`taller_2/`).

```powershell
pip install -r requirements.txt
python -m src.ingest                       # construye chroma_db/ (52 fragmentos)
python -m src.app                          # chat
python -m src.app --solo-recuperacion      # fragmentos, puntajes y veredicto, sin cargar ningún LLM
python -m evaluation.run_all               # toda la evaluación (resumen en results/)
python -m evaluation.eval_modificaciones   # experimentos de modificación (k, prompt, secciones 7 y 8)
python -m pytest tests
```

`run_all` llama a Groq en los pasos 5 y 8; su última ejecución completa tardó unos 21 minutos (hay una pausa de 20 s entre
preguntas). No incluye por defecto dos partes más lentas, que se ejecutan por separado (o añadiendo `--ragas-juez` y `--con-local`
a `run_all`):

```powershell
python -m evaluation.eval_ragas --ragas-juez      # RAGAS con juez: 10 preguntas, pausa de 45 s entre ellas (≈10 min); requiere GROQ_API_KEY
python -m evaluation.eval_end_to_end --local      # grupo de control con el modelo local: 5 preguntas, 13 generaciones (≈15-20 min en CPU)
python -m evaluation.eval_end_to_end --reevaluar results/end_to_end_<modelo>_<fecha>.json   # recalcula las marcas «ok» de un .json guardado, sin generar
```

Los tiempos de estos dos comandos son **aproximados**: se estimaron a partir de las ejecuciones realizadas y varían con la máquina y la
red. `--ragas-juez` es la parte que más tokens consume y no se midió por separado, así que conviene ejecutarla solo con cupo
disponible en tu cuenta.

El modelo de embeddings `intfloat/multilingual-e5-small` (~0.5 GB) se descarga de Hugging Face la primera vez y se usa siempre, con o
sin clave. Embeddings, Chroma, enrutador, verificador y umbral corren siempre en local y sin clave.

### Con clave de Groq (recomendado)

1. Crea una cuenta en <https://console.groq.com> y genera una clave en *API Keys*.
2. Copia `.env.example` a `.env` (`Copy-Item .env.example .env` en PowerShell; `cp .env.example .env` en otros terminales) y pega la clave
   en `GROQ_API_KEY=`.
3. Ejecuta `python -m src.app`. El generador por defecto es `openai/gpt-oss-20b` (alternativa: `LLM_MODEL=openai/gpt-oss-120b`).

El archivo `.env` está en `.gitignore`; la clave nunca debe subirse al repositorio. Si el ID del modelo falla, el chat lo dice y explica
cómo listar los modelos de tu cuenta (`GET https://api.groq.com/openai/v1/models` con `Authorization: Bearer <tu clave>`).

### Sin clave: modo demostrativo con el modelo local

Sin `GROQ_API_KEY` (o con `LLM_PROVIDER=local`) se usa `Qwen/Qwen2.5-0.5B-Instruct` en CPU; la primera vez descarga ~1 GB.
**El modelo local no es un respaldo.** Su calidad no sirve para atender clientes (ver [resultados.md](resultados.md)): existe como
**grupo de control** de la evaluación (mide cuánto aportan RAG y reglas con el modelo pequeño del Taller 1) y para poder ejecutar el
proyecto sin cuenta. Se demora bastante (decenas de segundos por respuesta).

| | Con clave de Groq | Sin clave (modelo local) |
|---|---|---|
| Recuperación, umbral, enrutador, verificador, pedidos | sí | sí |
| `--solo-recuperacion`, pasos 1–4, 6 y 7a de la evaluación, tests | sí | sí |
| Respuestas redactadas | `gpt-oss-20b`, segundos | Qwen 0.5B, lento y de baja calidad |
| Evaluación punta a punta (paso 5) | las 11 preguntas | solo un subconjunto de 5 preguntas |
| RAGAS con juez (7b) | sí (`--ragas-juez`) | no |

`LLM_PROVIDER` solo admite `auto` (defecto: Groq si hay clave, si no el local), `groq` y `local`; otro valor da un error claro.
**Si la API falla en ejecución no hay cambio automático al modelo local:** tras 3 reintentos (esperando lo que indique la cabecera
`retry-after` en un 429) el chat muestra el error y el usuario decide. Las reglas de devolución (`USE_RULES=1`) se aplican con cualquier
generador.

### Problemas de certificados (`CERTIFICATE_VERIFY_FAILED`)

Si un antivirus, VPN o proxy intercepta el HTTPS, las descargas o la API pueden fallar con *self signed certificate in certificate
chain*. Pon `USE_SYSTEM_CERTS=1` en `.env`: Python verificará los certificados con el almacén del sistema operativo (paquete
`truststore`). No desactiva la verificación. Por defecto está apagado.

## Estructura

```
src/          config, embeddings (E5), chunking, ingest, retriever, rules (+ reglas.json), orders, router, llm, rag_chain, app
data/         documentos simulados (política, FAQ, catálogo, envíos y pagos, pedidos)
evaluation/   gold.json (43 preguntas) y los scripts eval_*.py, calibrate_threshold.py, run_all.py
tests/        plazo de reglas.json vs política, consistencia FAQ/envíos, reintentos 429, enrutador, texto plano,
              extracción de devoluciones (test_parse_return.py), fragmentos (test_get_chunks.py)
results/      salidas de la evaluación (.md/.json); las de Groq llevan el modelo y la fecha en el nombre
fase_1_2.md   justificación de los componentes
fase_3.md     explicación del código y experimentos
resultados.md resultados completos de la evaluación y experimentos de modificación
```

## Resultados principales

Corpus: 52 fragmentos. Evaluación con `gold.json`: 29 preguntas dentro del alcance, 6 sin relación y 8 cercanas al dominio.

| Qué se midió | Resultado |
|---|---|
| Recuperación (k=4, 29 preguntas) | Hit@1 0,90 · Hit@4 0,97 · MRR 0,93 |
| Prefijos de E5 (`query:` / `passage:`) | Hit@1 pasa de 0,79 a 0,90 |
| Fragmentación por estructura frente a tamaño fijo 1000/0 | Hit@4 igual (0,97); la estructura envía ~3 veces menos texto por consulta (1109 frente a 3453 caracteres) |
| Umbral de relevancia | 0,822 (calibrado con las mismas preguntas con las que se evalúa) |
| Punta a punta con Groq (11 preguntas): sin RAG / con RAG / con RAG + reglas | 2 / 8 / 10 |
| Devoluciones (4 de las 11): sin RAG / con RAG / con RAG + reglas | 2 / 2 / 4 |
| Preguntas cercanas al dominio respondidas (de 8): con la instrucción de rechazo / sin ella | 0 / 4 |
| Control con el modelo local (5 preguntas): sin RAG / con RAG / con RAG + reglas | 0 / 1 / 3 (Groq en las mismas 5: 2 / 4 / 5) |

Son muestras pequeñas: una diferencia de una pregunta no es concluyente. Las advertencias (por ejemplo, que el empate en Hit@4 entre
estrategias de fragmentación dice poco, o que RAGAS se juzgó con el mismo modelo que genera) y el detalle de cada experimento están en
[resultados.md](resultados.md).

## Limitaciones y supuestos

- **Solo CPU y modelo local pequeño.** El generador local es lento y de baja calidad; por eso es grupo de control y no respaldo.
- **Documentos simulados y pocas preguntas.** Los documentos son ficticios; las 43 preguntas de `gold.json`, las 11 de la evaluación
  punta a punta y las 5 del control local no bastan para una evaluación a mayor profundidad.
- **Umbral con poco margen y sin conjunto de prueba separado.** Entre el mejor `ooc_facil` (0,807) y el peor `in` (0,837) hay solo 0,03,
  y el umbral se calibró con las mismas preguntas con las que se evalúa, así que las cifras de rechazo (0/29 `in` rechazadas, 0/6
  `ooc_facil` aceptadas) son optimistas. Otro modelo de embeddings o preguntas nuevas pueden exigir recalibrar. De las preguntas
  cercanas al dominio que no están en los documentos, 4 de 8 superan el umbral y dependen del prompt del generador; con el modelo
  local, la única probada (D01) no se rechazó.
- **Verificador de devoluciones.** Sus reglas viven en el texto de la política y en el código (el plazo está en `reglas.json` y un test
  comprueba que coincide con la política); si la política cambia de estructura hay que revisar el código. Además extrae producto, días,
  estado y empaque del texto del cliente con regex simples: si faltan datos, los pide, y puede interpretar mal frases ambiguas. Se
  corrigieron varios casos y hay pruebas con frases límite (`tests/test_parse_return.py`), pero la lista no es exhaustiva y no
  entiende matices como «casi no lo usé»: ese caso podría aceptarse por error y debería revisarlo un agente humano (lo documenta una
  prueba marcada como fallo esperado, `xfail`).
- **Secciones 7 y 8 siempre en devoluciones aceptadas.** Cuando el verificador acepta, el chat añade al prompt los pasos (`politica::7`)
  y el reembolso (`politica::8`) aunque no salgan en el top 4; sin ellos el modelo inventaba los pasos. Es una regla fija ligada a la
  estructura de la política.
- **Conversación sin memoria.** El cliente debe dar los datos de la devolución en un solo mensaje.
- **Fallo de recuperación conocido.** Q18 («¿Puedo pagar cuando me entreguen el pedido?») no recupera la sección correcta: el sistema
  responde el rechazo seguro aunque la respuesta existe en los documentos (sin RAG, el modelo afirma algo falso).
- **RAGAS.** El mismo modelo genera y juzga, y las 10 preguntas juzgadas son sencillas; Faithfulness tiene efecto techo y Response
  Relevancy usa `strictness=1`, mezcla los prefijos `query:`/`passage:` y, con E5, su escala útil es de solo ~0,14, así que discrimina
  poco. Se fijó `langchain-community==0.4.1` porque `ragas 0.4.3` no importa con la 0.4.2.
- **Privacidad y límites de la API.** Con Groq, la pregunta del cliente y los fragmentos recuperados salen a un tercero; los embeddings y
  la base vectorial permanecen en local, y con el modelo local no sale nada (RAGAS se ejecuta con su telemetría desactivada,
  `RAGAS_DO_NOT_TRACK=true`). Se respetan los 429 (espera de `retry-after`, 3 reintentos) y las evaluaciones pausan `LLM_PAUSE_S`
  segundos (20 por defecto) entre preguntas; los límites dependen de la cuenta de cada usuario y pueden cambiar.
- **Chroma local** es adecuada para este taller, no para alta concurrencia.

El detalle de las limitaciones está en la sección 4 de [fase_3.md](fase_3.md).
