# Evaluación de punta a punta — local/Qwen/Qwen2.5-0.5B-Instruct — 2026-10-15

Grupo de control con el modelo local: subconjunto pequeño, sin pausas. Las marcas ok son heurísticas (regex); revisa las respuestas.

Carga del modelo + primera generación: 13.3 s.

## Aciertos heurísticos (5 preguntas)

| Condición | Aciertos |
|---|---|
| sin_rag | 0/5 |
| con_rag | 1/5 |
| con_rag_reglas | 3/5 |

Solo devoluciones (3):

- sin_rag: 0/3
- con_rag: 0/3
- con_rag_reglas: 2/3

En las preguntas que no son devoluciones, «con_rag_reglas» reutiliza «con_rag» (el verificador no interviene).

## Detalle

| Id | Condición | ok | Segundos | Llamadas LLM | Tokens (ent./sal.) |
|---|---|---|---|---|---|
| Q08 | sin_rag | no | 13.1 | 1 | 101/16 |
| Q08 | con_rag | sí | 71.9 | 1 | 681/18 |
| Q08 | con_rag_reglas (reutilizada) | sí | 71.9 | 1 | 681/18 |
| D01 | sin_rag | no | 21.8 | 1 | 97/24 |
| D01 | con_rag | no | 32.8 | 1 | 291/48 |
| D01 | con_rag_reglas (reutilizada) | no | 32.8 | 1 | 291/48 |
| R1 | sin_rag | no | 20.8 | 1 | 115/44 |
| R1 | con_rag | no | 50.3 | 1 | 460/49 |
| R1 | con_rag_reglas | no | 219.5 | 1 | 722/199 |
| R2 | sin_rag | no | 35.7 | 1 | 112/26 |
| R2 | con_rag | no | 115.9 | 1 | 452/87 |
| R2 | con_rag_reglas | sí | 115.7 | 1 | 566/38 |
| R3 | sin_rag | no | 37.6 | 1 | 112/40 |
| R3 | con_rag | no | 109.6 | 1 | 457/73 |
| R3 | con_rag_reglas | sí | 126.4 | 1 | 573/57 |

## Respuestas

### Q08 — ¿Cuánto cuesta el envío estándar?
Esperado: menciona $12.000

**sin_rag**

```text
El costo del envío estándar es $5.00.
```

**con_rag**

```text
El envío estándar cuesta $12.000 COP.
```

**con_rag_reglas**

```text
El envío estándar cuesta $12.000 COP.
```

### D01 — ¿Venden computadores portátiles?
Esperado: mensaje de rechazo

**sin_rag**

```text
Sí, venderemos muchos tipos de computadoras portátiles. ¿En qué te gustaría comprar?
```

**con_rag**

```text
El equipo de EcoMarket no vende computadoras portátiles. Estamos especializados en otros productos ecológicos. Te recomiendo buscar en sitios web o tiendas físicas más conocidas para comprar estos dispositivos.
```

**con_rag_reglas**

```text
El equipo de EcoMarket no vende computadoras portátiles. Estamos especializados en otros productos ecológicos. Te recomiendo buscar en sitios web o tiendas físicas más conocidas para comprar estos dispositivos.
```

### R1 — Quiero devolver unos audífonos, los compré hace 10 días, sin usar y con su empaque original
Esperado: aceptada y con los pasos de la política (escribir a soporte@…)

**sin_rag**

```text
¡Por supuesto! Nos encantaría ayudarte a devolver tus audífonos. Por favor, proporciona la fecha exacta de compra y el número del paquete para que pueda verificarlo.
```

**con_rag**

```text
La solicitud de devolución de los audífonos es válida. Para realizarla, asegúrate de tenerlos en buen estado y que no estén utilizados. Por favor, envíales tu solicitud de devolución.
```

**con_rag_reglas**

```text
¡Gracias por tu solicitud! Estoy muy contento de que te haya gustado nuestro producto. Para poder realizar tu devolución, necesitamos que cumplies con algunas condiciones:

1. Cumplir las condiciones: Necesitas que tengas el producto sin usar y que tenga tu empaque original. Esto significa que debes tener el producto en tu casa antes de hacer la devolución.

2. Conservar el empaque original: El empaque debe mantenerse intacto durante todo el proceso de devolución. No puedes cambiar o modificar el empaque.

3. Plazo de devolución: Tu solicitud debe ser recibida dentro de los 30 días siguientes a la fecha de entrega.

Si cumples con estas condiciones, podrás solicitar nuestra devolución. Por favor, enviaremos tu solicitud y pedimos que lo hagas. ¡Estoy segura de que te daré un reembolso si lo logras!
```

### R2 — Quiero devolver mi crema de cuidado personal, está abierta, la recibí hace 5 días
Esperado: rechazada (higiene abierta)

**sin_rag**

```text
¡Hola! Estoy aquí para ayudarte. ¿En qué puedo ayudarte con tu crema de cuidado personal?
```

**con_rag**

```text
La solicitud de devolución de tu crema de cuidado personal es válida. Para realizarla, necesitas presentarla dentro de los 30 días siguientes a la entrega. Asegúrate de que la crema esté completamente limpia y sin uso antes de hacer la solicitud. Si no cumple con estas condiciones, te recomendaría buscar otro producto similar o solicitar un reembolso.
```

**con_rag_reglas**

```text
El veredicto es RECHAZADA. Los productos de higiene personal que están abiertos no pueden ser devueltos debido a su estado de uso.
```

### R3 — Quiero devolver una camiseta que recibí hace 45 días, sin usar y con su empaque
Esperado: rechazada (45 días)

**sin_rag**

```text
¡Por supuesto! Nos encantaría ayudarte a devolver tu camiseta. Por favor, proporciona los detalles del producto para que pueda hacerlo de manera más eficiente.
```

**con_rag**

```text
La solicitud del cliente es válida. Según la política de devoluciones, la devolución se realizará por el mismo medio de pago utilizado en la compra, en un plazo de 5 a 10 días hábiles. Además, la camiseta fue devuelta dentro de los 30 días posteriores a la entrega.
```

**con_rag_reglas**

```text
El veredicto es RECHAZADA debido a que han pasado 45 días desde la entrega y el plazo es de 30 días calendario. No cumplimos con las condiciones generales de devolución establecidas en la política de EcoMarket.
```

Tiempo por generación con el modelo local: mediana 50.3 s, mín. 13.1 s, máx. 219.5 s (13 generaciones).

