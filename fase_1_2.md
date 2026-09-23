# Taller Práctico #1

## Caso de Estudio: Optimización de la Atención al Cliente en EcoMarket

---

# Fase 1 — Selección y Justificación del Modelo de IA

## 1.1. Entendimiento del problema

EcoMarket es una empresa de comercio electrónico que está experimentando un rápido crecimiento y recibe miles de consultas diarias a través de diferentes canales, como chat, correo electrónico y redes sociales.

El **80 % de las consultas son repetitivas**, principalmente relacionadas con:

- Estado de los pedidos.
- Devoluciones.
- Características de los productos.

El **20 % restante corresponde a consultas más complejas**, como quejas, problemas técnicos y sugerencias, que requieren un mayor nivel de análisis, empatía y, en algunos casos, intervención humana.

Actualmente, el tiempo promedio de respuesta es de **24 horas**, lo que está afectando la satisfacción de los clientes.

---

## 1.2. Modelo seleccionado

Para EcoMarket propongo utilizar un **LLM (Large Language Model) de propósito general**, integrado con las fuentes de información empresarial de la compañía.

La razón principal es que el problema requiere dos capacidades complementarias:

- **Comprensión y generación de lenguaje natural**, para interpretar las preguntas de los clientes y producir respuestas claras, fluidas y empáticas.
- **Acceso a información específica de EcoMarket**, como pedidos, catálogo, información de envíos y políticas de devolución.

Por esta razón, el LLM no funcionará de manera aislada.

La solución propuesta será una **arquitectura híbrida que combine el LLM con datos estructurados, RAG y escalamiento a agentes humanos**.

---

## 1.3. Arquitectura propuesta

EcoMarket utilizará un **LLM de propósito general integrado con sus fuentes de información empresarial**.

La arquitectura combinará:

- Consultas a datos estructurados, como:
  - Pedidos.
  - Catálogo de productos.
  - Información de envíos.
- **RAG (Retrieval-Augmented Generation)** para recuperar información documental relevante, como políticas y procedimientos.
- Un **LLM** encargado de comprender las solicitudes y generar las respuestas.
- **Agentes humanos** para atender casos complejos que requieran intervención especializada.

La arquitectura propuesta está representada de la siguiente manera:

```text
                         CLIENTE
                            │
                            ▼
                  ┌───────────────────┐
                  │ Canal de atención │
                  │ Chat / Email / RRSS│
                  └─────────┬─────────┘
                            │
                            ▼
                  ┌───────────────────┐
                  │       LLM         │
                  │ Comprensión y     │
                  │ generación        │
                  └─────────┬─────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
       ┌────────────────┐      ┌────────────────────┐
       │      RAG       │      │ Datos estructurados│
       │                │      │                    │
       │ • Políticas    │      │ • Pedidos          │
       │ • Devoluciones │      │ • Catálogo         │
       │ • Documentos   │      │ • Envíos           │
       └────────────────┘      └────────────────────┘
                │                       │
                └───────────┬───────────┘
                            │
                            ▼
                    Respuesta al cliente
                            │
                  ┌─────────┴─────────┐
                  │                   │
                  ▼                   ▼
          Caso automático       Caso complejo
                                      │
                                      ▼
                              Agente humano
```

Esta arquitectura permite separar las responsabilidades:

> **El LLM se encarga de comprender y generar lenguaje, mientras que las fuentes de EcoMarket proporcionan la información utilizada para responder.**

---

## 1.4. Integración con la base de datos de EcoMarket

El modelo se integraría con las fuentes de información de EcoMarket.

Sin embargo, el LLM **no deberia tener acceso directo e indiscriminado a toda la base de datos**.

En su lugar, existiría una capa intermedia que identifique la información necesaria y realice las consultas correspondientes.

Por ejemplo, ante la pregunta:

> "¿Cuál es el estado de mi pedido ECM10004?"

el flujo sería:

```text
Cliente
   │
   ▼
LLM identifica la intención
   │
   ▼
Consulta a los datos de pedidos
   │
   ▼
ECM10004
Estado: Retrasado
Fecha estimada: 2026-09-28
   │
   ▼
LLM genera una respuesta clara
   │
   ▼
Cliente
```

De esta manera, el modelo no necesita "recordar" el estado de un pedido. La información se obtiene de la fuente correspondiente.

Esto es especialmente importante para reducir el riesgo de que el modelo invente información sobre pedidos.

---

## 1.5. Uso de RAG

El sistema también utilizará **RAG (Retrieval-Augmented Generation)** para consultar información documental de EcoMarket.

Por ejemplo:

- Política de devoluciones.
- Condiciones de envío.
- Características y documentación de productos.
- Procedimientos de atención.

El funcionamiento general sería:

```text
Pregunta del cliente
        │
        ▼
Recuperación de información relevante
        │
        ▼
Contexto de EcoMarket
        │
        ▼
LLM
        │
        ▼
Respuesta fundamentada en el contexto
```

La principal ventaja es que la información empresarial puede actualizarse en las fuentes de conocimiento sin tener que volver a entrenar el modelo cada vez que exista un cambio.

---

## 1.6. ¿Modelo de propósito general o Fine-Tuned LLM?

La propuesta inicial será utilizar un **modelo de propósito general**, complementado con las fuentes de información de EcoMarket.

La razón es que gran parte de la información utilizada por el sistema puede cambiar con frecuencia:

- Estado de los pedidos.
- Fechas de entrega.
- Información de envíos.
- Catálogo.
- Políticas empresariales.

El fine-tuning no sería la estrategia principal para mantener actualizada esta información.

En cambio, RAG y las consultas a fuentes estructuradas permiten obtener información más actualizada sin necesidad de volver a entrenar el modelo.

El fine-tuning podría evaluarse posteriormente si EcoMarket necesitara adaptar aspectos específicos del comportamiento o estilo del modelo.

---

## 1.7. ¿Por qué un LLM y no una solución exclusivamente tradicional?

Una solución tradicional basada únicamente en reglas podría manejar determinadas consultas estructuradas, pero tendría dificultades para interpretar la gran variedad de formas en las que los clientes pueden expresar una misma necesidad.

Por ejemplo:

- "¿Dónde está mi pedido?"
- "¿Ya salió mi paquete?"
- "Quiero saber cuándo llega mi compra."
- "¿Me pueden decir qué pasó con ECM10004?"

Todas pueden representar una intención similar.

El LLM permite interpretar diferentes formulaciones del lenguaje natural y generar respuestas adaptadas al contexto.

Sin embargo, no se propone utilizar el LLM como única fuente de información. La información empresarial continuará proveniendo de las fuentes de EcoMarket.

---

## 1.8. Costo

La solución puede ayudar a controlar los costos mediante la automatización de una parte importante de las consultas.

El **80 % de las consultas son repetitivas**, por lo que existe una oportunidad considerable para automatizar este tipo de solicitudes.

Además, no sería necesario utilizar los mismos recursos para todas las consultas.

Las consultas sencillas podrían resolverse automáticamente, mientras que los casos complejos podrían ser escalados a agentes humanos.

---

## 1.9. Escalabilidad

La arquitectura propuesta es escalable porque permite automatizar consultas y procesar múltiples solicitudes simultáneamente.

Esto resulta especialmente relevante debido al rápido crecimiento de EcoMarket y al alto volumen de consultas.

A medida que aumente el número de clientes, el sistema podría continuar atendiendo las consultas repetitivas mientras los agentes humanos se concentran en los casos más complejos.

---

## 1.10. Facilidad de integración

La solución puede integrarse con diferentes fuentes y sistemas de EcoMarket:

- Base de datos de pedidos.
- Catálogo de productos.
- Información de envíos.
- Documentación de políticas.
- Sistema de atención al cliente.

El LLM actuaría como una capa de interacción y generación de lenguaje, mientras que los sistemas empresariales continuarían siendo responsables de proporcionar los datos.

Esto facilita una arquitectura modular, donde cada componente tiene una responsabilidad específica.

---

## 1.11. Calidad esperada de las respuestas

La calidad de las respuestas dependerá de:

1. El modelo de lenguaje seleccionado.
2. La calidad de los datos de EcoMarket.
3. La actualización de las fuentes.
4. La calidad de la recuperación realizada mediante RAG.
5. La estructura de los prompts.
6. Las reglas utilizadas para controlar la generación.
7. El escalamiento de casos complejos hacia agentes humanos.

Se busca construir un sistema donde la generación del lenguaje esté respaldada por información empresarial relevante.

---

## 1.12. Conclusión de la Fase 1

La solución propuesta para EcoMarket es una **arquitectura híbrida basada en un LLM de propósito general, integrado con las fuentes de información empresarial de la compañía**.

La arquitectura combinará:

**LLM + datos estructurados + RAG + agentes humanos.**

El LLM será responsable de comprender las solicitudes y generar respuestas naturales, mientras que las fuentes de EcoMarket proporcionarán la información utilizada para responder.

Los datos estructurados serán utilizados para información como pedidos, catálogo e información de envíos, mientras que RAG permitirá recuperar información documental relevante.

Los casos complejos podrán ser escalados a agentes humanos.

Esta arquitectura permite equilibrar:

- Calidad de las respuestas.
- Precisión de la información.
- Costo.
- Escalabilidad.
- Facilidad de integración.
- Actualización de la información.
- Control de riesgos.

---

# FASE 2 — Fortalezas, limitaciones y riesgos éticos

## 2.1 Fortalezas de la solución propuesta

La solución basada en un modelo de lenguaje general, integrado con los datos de EcoMarket mediante fuentes estructuradas y RAG, presenta varias ventajas para el escenario planteado.

### Reducción del tiempo de respuesta

Actualmente, EcoMarket presenta un tiempo promedio de respuesta de aproximadamente 24 horas. La automatización de consultas frecuentes permitiría generar respuestas en un tiempo mucho menor, especialmente para solicitudes relacionadas con estados de pedidos, características de productos y políticas de devolución.

### Atención 24/7

El sistema podría atender consultas fuera del horario laboral, permitiendo ofrecer una primera respuesta inmediata y derivar a un agente humano aquellos casos que requieran intervención.

### Automatización de consultas repetitivas

El 80% de las consultas corresponden a solicitudes repetitivas. Estas consultas son candidatas a automatización porque suelen requerir información concreta y verificable.

### Escalabilidad

La solución permitiría atender un aumento en el volumen de consultas sin incrementar proporcionalmente el número de agentes necesarios para responder preguntas rutinarias.

### Mayor consistencia en las respuestas

Al utilizar fuentes centralizadas de información, como la base de datos de pedidos y los documentos oficiales de EcoMarket, el sistema puede mantener respuestas más consistentes respecto a políticas, productos y procesos.

### Apoyo al equipo humano

La automatización no debe limitarse a sustituir tareas humanas. También puede utilizarse para que los agentes  se concentren en el 20% de consultas más complejas, como reclamaciones, problemas técnicos y situaciones que requieren empatía o criterio humano.

---

## 2.2 Limitaciones de la solución

A pesar de sus beneficios, la solución presenta limitaciones que deben considerarse antes de una implementación real.

### Alucinaciones del modelo

Un modelo generativo puede producir información incorrecta o inventada. En el contexto de EcoMarket, esto podría provocar que el sistema indique un estado de pedido inexistente, una fecha de entrega incorrecta o una política que no corresponde a la empresa.

Por esta razón, el modelo no debe considerarse la fuente de verdad. La información transaccional debe obtenerse de las fuentes autorizadas de EcoMarket y utilizarse como contexto para generar la respuesta.

### Dependencia de la calidad de los datos

La calidad de las respuestas dependerá directamente de la calidad y actualización de las fuentes utilizadas.

Si la base de datos contiene un estado incorrecto o una política está desactualizada, el sistema podría generar una respuesta incorrecta aunque el modelo funcione correctamente.

Por ello, es necesario establecer procesos para mantener actualizadas las fuentes de información.

### Dificultad para resolver casos complejos

No todas las consultas pueden automatizarse de manera segura. Las reclamaciones, problemas técnicos, situaciones excepcionales y casos que requieren negociación o empatía pueden necesitar intervención humana.

La arquitectura debe permitir escalar estos casos a un agente.

### Dependencia de servicios tecnológicos

Si el modelo, el sistema de recuperación de información o alguno de los servicios necesarios deja de estar disponible, la capacidad de atención automatizada podría verse afectada.

Por este motivo, una implementación real debería considerar mecanismos de monitoreo, manejo de errores y alternativas de contingencia.

---

# 2.3 Riesgos éticos

La implementación de IA generativa en atención al cliente no solamente implica riesgos técnicos. También puede generar consecuencias relacionadas con privacidad, sesgos y cambios en el trabajo de los empleados.

## 2.3.1 Alucinaciones y desinformación

Uno de los principales riesgos consiste en que el modelo genere información que no está respaldada por las fuentes de EcoMarket.

Por ejemplo, ante una consulta sobre un pedido, el modelo podría inventar una fecha de entrega o afirmar que un pedido fue enviado cuando realmente todavía está en preparación.

### Posibles consecuencias

- Clientes reciben información incorrecta.
- Pérdida de confianza en EcoMarket.
- Incremento de reclamaciones.
- Decisiones incorrectas tomadas por los clientes.
- Posibles consecuencias económicas o reputacionales para la empresa.

### Medidas de mitigación

- Utilizar la base de datos de EcoMarket como fuente de verdad para información transaccional.
- Utilizar RAG para recuperar información relevante de documentos oficiales.
- Prohibir que el modelo invente datos cuando no estén disponibles.
- Indicar explícitamente cuando la información sea insuficiente.
- Escalar a un agente humano los casos que no puedan resolverse con información confiable.

---

## 2.3.2 Sesgos

Los modelos generativos pueden producir respuestas inconsistentes dependiendo de cómo se formule una consulta o del contexto proporcionado.

En atención al cliente, un sesgo podría manifestarse mediante diferencias injustificadas en el tono, nivel de ayuda o tratamiento ofrecido a diferentes clientes.

Por ejemplo, dos clientes que presentan esencialmente el mismo problema deberían recibir respuestas equivalentes en cuanto a las políticas aplicables, aunque utilicen diferentes formas de expresarse.

### Posibles consecuencias

- Tratamiento inconsistente entre clientes.
- Respuestas menos útiles para determinados grupos.
- Percepción de discriminación.
- Pérdida de confianza en el sistema.

### Medidas de mitigación

- Probar el sistema utilizando diferentes formas de expresar una misma solicitud.
- Evaluar sistemáticamente la consistencia de las respuestas.
- Establecer políticas de atención que el modelo deba seguir.
- Revisar manualmente casos problemáticos.
- Mantener mecanismos para que los agentes humanos puedan corregir o escalar respuestas.
- Realizar evaluaciones periódicas después del despliegue.

El objetivo no debe ser asumir que el modelo es imparcial, sino evaluar activamente su comportamiento y detectar posibles diferencias injustificadas.

---

## 2.3.3 Privacidad y protección de datos

Las consultas de atención al cliente pueden involucrar información personal, como nombres, direcciones, historial de compras, números de pedido y otra información relacionada con los clientes.

Existe un riesgo si estos datos se envían innecesariamente al modelo o se utilizan de forma inadecuada para entrenar o ajustar el sistema.

### Posibles consecuencias

- Exposición de información personal.
- Acceso no autorizado a información de clientes.
- Uso de datos para fines diferentes de aquellos para los que fueron recopilados.
- Mayor impacto en caso de una vulnerabilidad del sistema.

### Medidas de mitigación

EcoMarket debería aplicar el principio de minimización de datos: el modelo debe recibir únicamente la información necesaria para resolver la consulta.

Por ejemplo, para responder sobre el estado de un pedido podría ser suficiente proporcionar al modelo el identificador del pedido, producto, estado, fecha estimada y enlace de seguimiento, sin incluir información personal que no sea necesaria.

También deberían existir:

- Controles de acceso.
- Protección de las bases de datos.
- Políticas de retención y eliminación de información.
- Registro y monitoreo de accesos.
- Separación entre información transaccional y el modelo generativo.
- Restricciones sobre el uso de datos personales para fine-tuning.

La información sensible no debería incorporarse indiscriminadamente al entrenamiento o ajuste del modelo.

---

## 2.3.4 Impacto en los trabajadores

La automatización del 80% de las consultas repetitivas puede modificar significativamente las funciones del equipo de atención al cliente.

Existe el riesgo de que la implementación se enfoque únicamente en reducir costos mediante sustitución de trabajadores, en lugar de utilizar la IA como herramienta de apoyo.

### Posibles consecuencias

- Reducción de determinadas tareas realizadas actualmente por agentes.
- Cambios en las responsabilidades del equipo.
- Necesidad de adquirir nuevas habilidades.
- Riesgo de desplazamiento laboral si la automatización se utiliza exclusivamente para reemplazar puestos.

### Medidas de mitigación

La solución propuesta debería utilizar un enfoque **human-in-the-loop**.

El sistema puede encargarse de las consultas repetitivas y derivar a los agentes aquellos casos que requieren:

- Empatía.
- Negociación.
- Resolución de problemas complejos.
- Manejo de reclamaciones.
- Excepciones a las políticas.
- Intervención humana explícita.

De esta manera, la IA puede funcionar como una herramienta de apoyo que reduce tareas repetitivas y permite que los agentes se concentren en situaciones de mayor complejidad.

EcoMarket también debería evaluar periódicamente cómo cambia la carga de trabajo del equipo y proporcionar capacitación cuando sean necesarias nuevas competencias.

---

## 2.3.5 Calidad y actualización de la información

Otro riesgo consiste en que las fuentes utilizadas por el sistema estén desactualizadas o contengan información incorrecta.

Por ejemplo, si una política de devolución cambia pero el documento utilizado por el sistema no se actualiza, el asistente podría proporcionar instrucciones incorrectas.

### Medidas de mitigación

- Mantener una única fuente oficial para cada tipo de información.
- Establecer responsables de actualización.
- Versionar los documentos utilizados por RAG.
- Validar periódicamente la información recuperada.
- Monitorear las respuestas generadas.
- Permitir que los agentes reporten información incorrecta.

---

# 2.4 Estrategia general de mitigación

Los riesgos anteriores muestran que implementar un modelo generativo no consiste únicamente en conectar un LLM a los canales de atención.

La arquitectura debe incorporar controles desde el diseño:

```text
                 Cliente
                    |
                    v
          Canal de atención
                    |
                    v
             Modelo LLM
                    |
          +---------+---------+
          |                   |
          v                   v
   Datos estructurados       RAG
   EcoMarket                Documentos
          |                   |
          +---------+---------+
                    |
                    v
          Validación / reglas
                    |
             +------+------+
             |             |
             v             v
        Respuesta      Escalamiento
        automática     a agente humano
```
---

# 2.5. Conclusión de la Fase 2

La solución propuesta puede mejorar significativamente la atención al cliente de EcoMarket al reducir los tiempos de respuesta, automatizar consultas repetitivas y permitir atención continua.

Sin embargo, la automatización no elimina la necesidad de supervisión humana. Los principales riesgos se concentran en la generación de información incorrecta, los posibles sesgos, la protección de datos personales y el impacto de la automatización sobre los trabajadores.

Por esta razón, la propuesta utiliza una arquitectura híbrida en la que el LLM se encarga de comprender las consultas y generar respuestas, mientras que los datos estructurados y los documentos de EcoMarket proporcionan la información de referencia. Los casos complejos se derivan a agentes humanos.

El objetivo no debería ser automatizar la atención al cliente sin restricciones, sino construir un sistema que combine automatización, fuentes confiables, controles de seguridad y supervisión humana.

---


