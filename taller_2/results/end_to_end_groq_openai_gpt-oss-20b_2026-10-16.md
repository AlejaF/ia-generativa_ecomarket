# Evaluación de punta a punta — groq/openai/gpt-oss-20b — 2026-10-16

Pausa de 20 s entre preguntas. Las marcas ok son heurísticas (regex); revisa las respuestas.

## Aciertos heurísticos (11 preguntas)

| Condición | Aciertos |
|---|---|
| sin_rag | 2/11 |
| con_rag | 8/11 |
| con_rag_reglas | 10/11 |

Solo devoluciones (4):

- sin_rag: 2/4
- con_rag: 2/4
- con_rag_reglas: 4/4

En las preguntas que no son devoluciones, «con_rag_reglas» reutiliza «con_rag» (el verificador no interviene).

## Detalle

| Id | Condición | ok | Segundos | Llamadas LLM | Tokens (ent./sal.) |
|---|---|---|---|---|---|
| Q08 | sin_rag | no | 2.6 | 1 | 148/62 |
| Q08 | con_rag | sí | 16.7 | 1 | 629/69 |
| Q08 | con_rag_reglas (reutilizada) | sí | 16.7 | 1 | 629/69 |
| Q14 | sin_rag | no | 1.1 | 1 | 153/99 |
| Q14 | con_rag | sí | 1.1 | 1 | 623/83 |
| Q14 | con_rag_reglas (reutilizada) | sí | 1.1 | 1 | 623/83 |
| Q18 | sin_rag | no | 0.8 | 1 | 152/61 |
| Q18 | con_rag | no | 1.1 | 1 | 637/59 |
| Q18 | con_rag_reglas (reutilizada) | no | 1.1 | 1 | 637/59 |
| Q28 | sin_rag | no | 1.1 | 1 | 154/89 |
| Q28 | con_rag | no | 0.9 | 1 | 545/136 |
| Q28 | con_rag_reglas | sí | 1.8 | 1 | 633/53 |
| F03 | sin_rag | no | 1.0 | 1 | 150/46 |
| F03 | con_rag | sí | 0.1 | 0 | 0/0 |
| F03 | con_rag_reglas (reutilizada) | sí | 0.1 | 0 | 0/0 |
| D01 | sin_rag | no | 0.8 | 1 | 148/90 |
| D01 | con_rag | sí | 0.7 | 1 | 317/51 |
| D01 | con_rag_reglas (reutilizada) | sí | 0.7 | 1 | 317/51 |
| D04 | sin_rag | no | 0.8 | 1 | 150/63 |
| D04 | con_rag | sí | 0.2 | 0 | 0/0 |
| D04 | con_rag_reglas (reutilizada) | sí | 0.2 | 0 | 0/0 |
| R1 | sin_rag | no | 0.8 | 1 | 165/99 |
| R1 | con_rag | no | 1.9 | 1 | 469/182 |
| R1 | con_rag_reglas | sí | 1.4 | 1 | 698/203 |
| R2 | sin_rag | sí | 0.9 | 1 | 160/68 |
| R2 | con_rag | sí | 1.1 | 1 | 457/84 |
| R2 | con_rag_reglas | sí | 0.9 | 1 | 551/54 |
| R3 | sin_rag | sí | 0.5 | 1 | 161/96 |
| R3 | con_rag | sí | 0.7 | 1 | 465/72 |
| R3 | con_rag_reglas | sí | 0.9 | 1 | 563/62 |
| P1 | sin_rag | no | 0.9 | 1 | 150/70 |
| P1 | con_rag | sí | 1.9 | 1 | 288/59 |
| P1 | con_rag_reglas (reutilizada) | sí | 1.9 | 1 | 288/59 |

## Respuestas

### Q08 — ¿Cuánto cuesta el envío estándar?
Esperado: menciona $12.000

**sin_rag**

```text
El envío estándar cuesta 5 € para pedidos superiores a 50 €. Si tu compra es menor, el precio es 7 €. Puedes ver el detalle en la sección de pagos al finalizar tu compra.
```

**con_rag**

```text
El envío estándar cuesta $12.000 COP y es gratis si tu compra supera los $150.000 COP. (Fuentes: faq::FAQ02, envios::costos-de-envio)
```

**con_rag_reglas**

```text
El envío estándar cuesta $12.000 COP y es gratis si tu compra supera los $150.000 COP. (Fuentes: faq::FAQ02, envios::costos-de-envio)
```

### Q14 — ¿Puedo cancelar mi compra si el pedido ya salió?
Esperado: solo en preparación

**sin_rag**

```text
Sí, puedes cancelar tu compra aunque el pedido ya haya salido. Envíanos un mensaje con tu número de pedido y te indicaremos si el envío ya está en tránsito. Si es así, te ayudaremos a devolver el producto y a procesar el reembolso. Si el pedido aún no se ha enviado, lo cancelamos de inmediato. ¡Avísanos y lo resolvemos!
```

**con_rag**

```text
No, no puedes cancelar el pedido una vez que ya está En tránsito. Solo se puede cancelar mientras esté En preparación. (Fuentes: faq::FAQ07, envios::cancelaciones-y-cambios-de-direccion)
```

**con_rag_reglas**

```text
No, no puedes cancelar el pedido una vez que ya está En tránsito. Solo se puede cancelar mientras esté En preparación. (Fuentes: faq::FAQ07, envios::cancelaciones-y-cambios-de-direccion)
```

### Q18 — ¿Puedo pagar cuando me entreguen el pedido?
Esperado: no hay pago contra entrega

**sin_rag**

```text
Claro, puedes pagar en el momento de la entrega. Solo ten a mano tu método de pago y el número de pedido para que el repartidor lo registre. ¡Gracias por comprar con EcoMarket!
```

**con_rag**

```text
No cuento con las herramientas para atender esta solicitud. Si lo deseas, puedo derivarte con un agente humano: escribe a soporte@ecomarket.example.
```

**con_rag_reglas**

```text
No cuento con las herramientas para atender esta solicitud. Si lo deseas, puedo derivarte con un agente humano: escribe a soporte@ecomarket.example.
```

### Q28 — ¿Puedo devolver la taza que tiene mi nombre grabado?
Esperado: no (personalizado)

**sin_rag**

```text
Claro, puedes devolverla. Solo ten en cuenta que las tazas personalizadas tienen un plazo de devolución de 14 días desde la compra y deben estar en su estado original. Si la taza está sin usar y con el embalaje, envíanos un mensaje con tu número de pedido y te indicamos el proceso.
```

**con_rag**

```text
No puedo decidir si la devolución es posible sin más información. Por favor dime:

1. ¿Cuánto tiempo ha pasado desde que recibiste la taza?
2. ¿La taza está sin usar y con su empaque original?

Con esos datos podré decirte si puedes devolverla y, si es posible, los pasos a seguir.
```

**con_rag_reglas**

```text
Lo siento, pero no podemos aceptar la devolución de la taza con tu nombre grabado. Los productos personalizados no pueden devolverse.
```

### F03 — ¿Quién ganó el último mundial de fútbol?
Esperado: mensaje de rechazo

**sin_rag**

```text
Argentina ganó el último mundial de fútbol, el de 2022 en Qatar.
```

**con_rag**

```text
No cuento con las herramientas para atender esta solicitud. Si lo deseas, puedo derivarte con un agente humano: escribe a soporte@ecomarket.example.
```

**con_rag_reglas**

```text
No cuento con las herramientas para atender esta solicitud. Si lo deseas, puedo derivarte con un agente humano: escribe a soporte@ecomarket.example.
```

### D01 — ¿Venden computadores portátiles?
Esperado: mensaje de rechazo

**sin_rag**

```text
Hola! En EcoMarket nos enfocamos en productos ecológicos como alimentos, cosméticos naturales, artículos de higiene sostenible y utensilios de cocina eco‑friendly. No vendemos computadores portátiles. Si buscas algo relacionado con la tecnología verde, dime y te ayudo a encontrar alternativas más sostenibles. ¡Saludos!
```

**con_rag**

```text
No cuento con las herramientas para atender esta solicitud. Si lo deseas, puedo derivarte con un agente humano: escribe a soporte@ecomarket.example.
```

**con_rag_reglas**

```text
No cuento con las herramientas para atender esta solicitud. Si lo deseas, puedo derivarte con un agente humano: escribe a soporte@ecomarket.example.
```

### D04 — ¿Los electrónicos tienen garantía de dos años?
Esperado: mensaje de rechazo

**sin_rag**

```text
Sí, todos los productos electrónicos que vendemos en EcoMarket vienen con una garantía de dos años. Si tienes algún problema con tu compra, avísanos y te ayudaremos a resolverlo.
```

**con_rag**

```text
No cuento con las herramientas para atender esta solicitud. Si lo deseas, puedo derivarte con un agente humano: escribe a soporte@ecomarket.example.
```

**con_rag_reglas**

```text
No cuento con las herramientas para atender esta solicitud. Si lo deseas, puedo derivarte con un agente humano: escribe a soporte@ecomarket.example.
```

### R1 — Quiero devolver unos audífonos, los compré hace 10 días, sin usar y con su empaque original
Esperado: aceptada y con los pasos de la política (escribir a soporte@…)

**sin_rag**

```text
¡Hola! Claro, podemos ayudarte con la devolución. Los audífonos están dentro del plazo de 30 días y están sin usar con el empaque original, así que todo está bien. Por favor, envíanos una foto del producto y el número de pedido, y te indicaremos el proceso para que lo devuelvas. ¡Gracias por confiar en EcoMarket!
```

**con_rag**

```text
¡Hola! Sí, puedes devolver los audífonos.  
Para hacerlo, sigue estos pasos:

1. Envía una solicitud de devolución a través de tu cuenta en EcoMarket.  
2. Empaza los audífonos en su empaque original y asegúrate de que estén sin usar.  
3. Incluye el número de pedido y la razón de la devolución.  
4. Envía el paquete a la dirección que te indique el servicio de atención al cliente.  

Una vez que EcoMarket reciba y revise el producto, el reembolso se realizará por el mismo medio de pago que usaste en la compra, en un plazo de 5 a 10 días hábiles.
```

**con_rag_reglas**

```text
¡Hola! Tu solicitud de devolución ha sido aceptada porque cumples con todas las condiciones: el pedido está dentro de los 30 días, el producto está sin usar y conserva su empaque original.

Pasos generales:
1. Escribe a soporte@ecomarket.example indicando el número de seguimiento del pedido y el producto que deseas devolver.
2. Espera la confirmación de EcoMarket, que incluirá las instrucciones de envío.
3. Empaca el producto sin usar, dentro de su empaque original.
4. Entrega el paquete a la transportadora indicada por EcoMarket. El costo del envío de la devolución lo asume EcoMarket.

Reembolso:
Una vez que EcoMarket reciba y revise el producto, el reembolso se realizará por el mismo medio de pago utilizado en la compra, en un plazo de 5 a 10 días hábiles.
```

### R2 — Quiero devolver mi crema de cuidado personal, está abierta, la recibí hace 5 días
Esperado: rechazada (higiene abierta)

**sin_rag**

```text
Hola, entiendo que quieres devolver la crema. Como está abierta y la recibiste hace 5 días, no podemos aceptarla como devolución. Si tienes algún problema con el producto, avísame y vemos cómo solucionarlo.
```

**con_rag**

```text
No, no se puede devolver la crema de cuidado personal porque es un producto de higiene personal que ya ha sido abierto. La política de devoluciones no permite la devolución de este tipo de artículos.
```

**con_rag_reglas**

```text
Lo siento, pero no podemos aceptar la devolución de tu crema de cuidado personal. Los productos de higiene personal que hayan sido abiertos no pueden devolverse.
```

### R3 — Quiero devolver una camiseta que recibí hace 45 días, sin usar y con su empaque
Esperado: rechazada (45 días)

**sin_rag**

```text
Lo siento, pero la política de devoluciones de EcoMarket permite devolver productos dentro de los 30 días posteriores a la compra. Como han pasado 45 días, no podemos aceptar la devolución. Si lo deseas, puedo ofrecerte un cupón de descuento para tu próxima compra o ayudarte a encontrar otro producto que te interese. ¿Qué prefieres?
```

**con_rag**

```text
No, no puedo aceptar la devolución. El plazo máximo para devolver un producto es de 30 días calendario desde la entrega, y tú recibiste la camiseta hace 45 días. Si necesitas ayuda con otra cosa, avísame.
```

**con_rag_reglas**

```text
Lo siento, pero no podemos aceptar la devolución de la camiseta. Han pasado 45 días desde la entrega y el plazo máximo para solicitar una devolución es de 30 días calendario.
```

### P1 — ¿Dónde está mi pedido ECM10004?
Esperado: Retrasado, 2026-09-28

**sin_rag**

```text
Hola, tu pedido ECM10004 está en tránsito y debería llegar en 2-3 días hábiles. Puedes seguir el número de seguimiento en la sección de pedidos de tu cuenta. Si necesitas más ayuda, avísame.
```

**con_rag**

```text
Estado: Retrasado
Entrega estimada: 2026-09-28
Mensaje: Lamentamos la demora. Puedes seguir el envío en https://tracking.ecomarket.example/ECM10004
```

**con_rag_reglas**

```text
Estado: Retrasado
Entrega estimada: 2026-09-28
Mensaje: Lamentamos la demora. Puedes seguir el envío en https://tracking.ecomarket.example/ECM10004
```

Tokens de la sesión: entrada 8566, salida 2010, llamadas 24.
