# Fase 3 — Aplicación de Ingeniería de Prompts

## 1. Objetivo

En esta fase se aplicó ingeniería de prompts a dos casos de uso del servicio al cliente de EcoMarket:

1. Consulta del estado de un pedido a partir de su número de seguimiento.
2. Evaluación de solicitudes de devolución de productos.

El objetivo fue observar cómo diferentes estructuras de prompt modifican el comportamiento y la calidad de las respuestas generadas por un modelo de lenguaje.

Para los experimentos se utilizó principalmente `Qwen/Qwen2.5-0.5B-Instruct`, ejecutado localmente mediante Transformers y CPU. También se realizaron experimentos comparativos con modelos de mayor tamaño y una versión cuantizada ejecutada mediante `llama.cpp`.

---

## 2. Base de datos de pedidos

Para el ejercicio de estado de pedidos se construyó el archivo:

`fase_3/data/pedidos.json`

La base contiene 16 pedidos, identificados mediante números de seguimiento desde `ECM10001` hasta `ECM10016`.

Cada registro contiene información de:

- Número de seguimiento.
- Cliente.
- Producto.
- Estado del pedido.
- Fecha estimada de entrega.
- URL de seguimiento.

Esto permite que los prompts utilicen información contextual de una fuente estructurada en lugar de solicitar al modelo que invente el estado del pedido.

---

## 3. Ingeniería de prompts para estado de pedidos

Se desarrollaron cinco versiones progresivas:

1. `01_zero_shot.py`
2. `02_few_shot.py`
3. `03_delimiters.py`
4. `04_numbered_steps.py`
5. `05_role_and_output.py`

La evolución buscó incorporar gradualmente diferentes técnicas de prompting: instrucciones directas, ejemplos, delimitación del contexto, pasos explícitos y definición del rol y formato esperado.

### 3.1 Zero-shot

La primera versión utiliza una instrucción directa para solicitar el estado del pedido.

Su principal ventaja es la simplicidad, pero deja mayor libertad al modelo para decidir qué información presentar.

### 3.2 Few-shot

Se incorporaron ejemplos para orientar al modelo sobre el tipo de respuesta esperado.

El experimento mostró que proporcionar ejemplos puede influir en el formato y contenido generado, aunque no garantiza que el modelo reproduzca correctamente todos los valores del pedido.

### 3.3 Delimitadores

Se separó explícitamente la información del pedido de la instrucción.

Esta estructura busca reducir ambigüedad y facilitar que el modelo identifique qué información debe utilizar como contexto.

### 3.4 Pasos numerados

La instrucción se organizó mediante pasos explícitos para orientar el proceso de generación.

Esto permitió estructurar mejor la respuesta, aunque en algunos casos el modelo pequeño presentó interpretaciones incorrectas de algunos términos.

### 3.5 Rol y formato de salida

La última versión define el comportamiento esperado del asistente y establece una estructura de salida con:

- Estado.
- Fecha estimada de entrega.
- Mensaje para el cliente.

Esta versión produjo respuestas más consistentes y estructuradas.

### 3.6 Análisis

Los experimentos muestran que la ingeniería del prompt modifica de manera significativa las respuestas del modelo.

La incorporación progresiva de contexto, estructura y formato permitió obtener respuestas más organizadas. Sin embargo, los resultados también muestran una limitación importante de los modelos pequeños: una instrucción más detallada no garantiza por sí sola una interpretación correcta de todos los datos.

Por ejemplo, en los resultados de `ECM10004`, cuyo estado real es `Retrasado`, algunas versiones generaron estados diferentes, mientras que la versión con rol y formato produjo una respuesta estructurada con estado, fecha y mensaje. Esto evidencia que el diseño del prompt puede mejorar la presentación, pero la exactitud de la información sigue dependiendo de la capacidad del modelo para utilizar correctamente el contexto proporcionado.

---

## 4. Ingeniería de prompts para devoluciones

Para este ejercicio se definió una política de devoluciones utilizada como contexto del modelo.

Los experimentos realizados con `Qwen/Qwen2.5-0.5B-Instruct` fueron:

- `v1`
- `v2`
- `v3`
- `final`

Se utilizaron tres casos de prueba:

| Caso | Situación | Resultado esperado |
|---|---|---|
| 1 | Audífonos, 10 días, sin usar y con empaque | Aceptada |
| 2 | Producto de higiene personal abierto | No aceptada |
| 3 | Camiseta, 45 días, sin usar y con empaque | No aceptada |

### 4.1 Resultados con Qwen2.5-0.5B-Instruct

Los resultados muestran diferentes comportamientos entre las versiones.

La versión `v1` tendió a considerar principalmente la condición del producto y el empaque, pero aceptó casos que debían ser rechazados.

La versión `v2` incorporó una verificación más explícita de las condiciones y obtuvo correctamente 2 de los 3 casos evaluados. Sin embargo, presentó un problema de diseño: incluía una condición relacionada con daños que posteriormente fue eliminada de la política utilizada en la versión final.

La versión `v3` modificó nuevamente la estructura de respuesta y mantuvo un formato más conciso, pero continuó presentando errores en la decisión de devolución.

La versión `final` buscó conservar una respuesta clara y empática, aunque los resultados evidenciaron que el modelo de 0.5B todavía tenía dificultades para aplicar simultáneamente todas las condiciones de la política.

Por esta razón, los resultados no se interpretan únicamente mediante el número de casos correctos. También se considera si la respuesta se fundamenta en las condiciones reales de la política.

---

## 5. Comparación entre modelos

Debido a las dificultades observadas en el ejercicio de devoluciones, se realizaron experimentos adicionales con modelos de mayor tamaño.

### Qwen/Qwen2.5-0.5B-Instruct

Fue utilizado como modelo principal debido a que puede ejecutarse localmente con recursos limitados y presentó tiempos de ejecución adecuados para realizar múltiples iteraciones de ingeniería de prompts.

Su principal limitación observada fue la dificultad para aplicar simultáneamente varias reglas condicionales en el caso de devoluciones.

### Qwen/Qwen2.5-1.5B-Instruct

Se realizó una prueba con la versión `v1` del prompt de devoluciones.

El modelo mostró una mejor capacidad para interpretar algunas condiciones de la política. En particular, identificó correctamente que un producto de higiene personal abierto no debía aceptarse.

Sin embargo, también presentó errores: aceptó el caso de la camiseta con 45 días, aunque excedía el plazo establecido.

Además, el tiempo de ejecución en CPU fue considerablemente mayor, por lo que continuar con múltiples iteraciones de prompts no resultaba eficiente para este entorno.

### Qwen2.5-1.5B-Instruct-GGUF-Q4_K_M

Finalmente se probó una versión cuantizada del modelo 1.5B mediante `llama.cpp`.

Este experimento permitió evaluar una alternativa de ejecución local con menor representación del modelo, pero mantuvo limitaciones en la aplicación de las reglas de devolución. Por ejemplo, en los resultados se observa que el modelo identificó correctamente el caso del producto de higiene personal abierto, pero aceptó incorrectamente la solicitud realizada después de 45 días.

Por tanto, aumentar el tamaño del modelo no eliminó completamente los errores de razonamiento sobre las reglas de negocio.

---

## 6. Análisis general de los experimentos

Los experimentos permitieron observar que la ingeniería de prompts tiene un efecto directo sobre el comportamiento del modelo.

En el caso de estado de pedidos, las diferentes técnicas permitieron mejorar progresivamente la estructura y presentación de las respuestas.

En el caso de devoluciones, el problema fue más complejo porque la respuesta dependía de la evaluación conjunta de varias condiciones. Los resultados mostraron que los modelos pueden generar respuestas lingüísticamente adecuadas y empáticas, pero aun así equivocarse en la decisión final.

También se observó que un modelo más grande no necesariamente elimina todos los errores. El modelo 1.5B mostró mejoras en algunos casos, pero continuó aceptando solicitudes que no cumplían el plazo.

Por esta razón, los resultados deben interpretarse como evidencia experimental sobre los casos evaluados y no como una garantía general de comportamiento del modelo.

---

## 7. Limitaciones

Durante los experimentos se identificaron las siguientes limitaciones:

- Los modelos se ejecutaron utilizando CPU, lo que aumentó considerablemente los tiempos de inferencia de los modelos de mayor tamaño.
- El modelo 0.5B presentó dificultades para aplicar simultáneamente varias reglas de negocio.
- Algunas respuestas incluyeron información no solicitada o condiciones que no correspondían a la política utilizada en ese momento.
- Las pruebas de devoluciones utilizaron tres casos representativos, por lo que no constituyen una evaluación exhaustiva de todas las situaciones posibles.
- Una mejora en el formato de la respuesta no necesariamente implica una mejora en la exactitud de la decisión.

---

## 8. Conclusiones

La Fase 3 permitió comprobar de manera práctica que la estructura del prompt influye directamente en las respuestas generadas por un modelo de lenguaje.

Para el estado de pedidos, técnicas como delimitadores, pasos explícitos, definición de rol y formato de salida ayudaron a obtener respuestas más estructuradas.

Para devoluciones, los experimentos mostraron un problema más complejo: el modelo debía combinar diferentes condiciones antes de tomar una decisión. En este escenario, el modelo 0.5B presentó limitaciones para aplicar correctamente todas las reglas de manera simultánea.

Los experimentos con modelos 1.5B permitieron observar que una mayor capacidad puede mejorar determinados casos, pero no garantiza por sí sola una aplicación correcta de las reglas de negocio.

Finalmente, el trabajo permitió comprobar que la ingeniería de prompts debe evaluarse no solamente por la calidad lingüística de la respuesta, sino también por su correspondencia con los datos y reglas proporcionados como contexto.