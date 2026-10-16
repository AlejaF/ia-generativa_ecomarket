# Experimentos de modificación — groq/openai/gpt-oss-20b — 2026-10-16

## 1. Número de fragmentos recuperados (k)

29 preguntas 'in', acierto por `chunk_id`, índice en memoria.

| k | Hit@k | MRR | Caracteres enviados por consulta |
|---|---|---|---|
| 1 | 0.90 | 0.90 | 291 |
| 2 | 0.93 | 0.91 | 536 |
| 4 | 0.97 | 0.93 | 1109 |
| 6 | 0.97 | 0.93 | 1696 |

## 2. Prompt: quitar la instrucción de rechazo

8 preguntas cercanas al dominio (ooc_dificil), umbral 0.822. «Respondida» = la respuesta no es el mensaje de rechazo.

| Configuración | Preguntas respondidas (de 8) |
|---|---|
| actual (umbral + instrucción de rechazo) | 0 |
| sin la instrucción de rechazo (umbral sí) | 4 |
| sin umbral (instrucción sí) | 0 |

| Id | Pregunta | Top-1 | Pasa el umbral | actual | sin instrucción | sin umbral |
|---|---|---|---|---|---|---|
| D01 | ¿Venden computadores portátiles? | 0.822 | sí | rechaza | responde | rechaza |
| D02 | ¿Tienen tienda física en Bogotá? | 0.824 | sí | rechaza | responde | rechaza |
| D03 | ¿Tienen programa de puntos o descuentos para clientes frecuentes? | 0.818 | no | rechaza | rechaza | rechaza |
| D04 | ¿Los electrónicos tienen garantía de dos años? | 0.811 | no | rechaza | rechaza | rechaza |
| D05 | ¿Cuál es el teléfono de servicio al cliente? | 0.816 | no | rechaza | rechaza | rechaza |
| D06 | ¿Puedo pagar mi compra en cuotas? | 0.842 | sí | rechaza | responde | rechaza |
| D07 | ¿Venden ropa para niños? | 0.829 | sí | rechaza | responde | rechaza |
| D08 | ¿Tienen aplicación móvil? | 0.798 | no | rechaza | rechaza | rechaza |

### Respuestas cuando el LLM respondió

- **D01 / sin_instruccion_de_rechazo** (¿Venden computadores portátiles?): No, no vendemos computadores portátiles.
- **D02 / sin_instruccion_de_rechazo** (¿Tienen tienda física en Bogotá?): No, EcoMarket no tiene tienda física en Bogotá. Solo realizamos envíos dentro de Colombia. (Fuentes: envios::cobertura)
- **D06 / sin_instruccion_de_rechazo** (¿Puedo pagar mi compra en cuotas?): No, EcoMarket no ofrece la opción de pagar en cuotas.
- **D07 / sin_instruccion_de_rechazo** (¿Venden ropa para niños?): No, no tenemos ropa para niños.

## 3. Código: no forzar las secciones 7 y 8 en devoluciones aceptadas

Elementos de la política que debe contener la respuesta: escribir a soporte@ (paso 1), entregar a la transportadora (paso 4) y reembolso en 5 a 10 días.

| Caso | Con secciones 7 y 8 | Sin secciones 7 y 8 |
|---|---|---|
| Quiero devolver unos audífonos, los compré hace 10 días, sin… | 3/3 | 1/3 |
| Quiero devolver mi botella reutilizable de acero, la recibí … | 3/3 | 1/3 |

### Respuestas sin las secciones 7 y 8

- Quiero devolver unos audífonos, los compré hace 10…: ¡Hola! Tu solicitud de devolución ha sido aceptada porque cumples con todas las condiciones: el producto está dentro de los 30 días, sin usar y con el empaque original.

Pasos generales:
1. Empaqueta el producto en su embalaje original y asegúrate de incluir todos los accesorios y la documentación.
2. Envía el paquete a la dirección de devolución indicada en tu cuenta de EcoMarket.
3. Una vez que recibamos y revisemos el producto, procesaremos el reembolso.

Reembolso:
El reembolso se realizará por el mismo medio de pago que usaste para la compra, en un plazo de 5 a 10 días hábiles. ¡Gracias por confiar en EcoMarket!
- Quiero devolver mi botella reutilizable de acero, …: ¡Hola! Tu solicitud de devolución ha sido aceptada porque cumples con todas las condiciones: la botella está sin usar, con el empaque original y dentro de los 30 días posteriores a la entrega.

Pasos generales:
1. Empaqueta el producto en su empaque original y colócalo en un sobre frágil.
2. Adjunta el formulario de devolución que te enviamos por correo.
3. Envía el paquete a la dirección indicada en el formulario.
4. Una vez que EcoMarket reciba y revise el producto, procesaremos el reembolso.

El reembolso se realizará por el mismo medio de pago que usaste para la compra, en un plazo de 5 a 10 días hábiles. ¡Gracias por confiar en EcoMarket!
