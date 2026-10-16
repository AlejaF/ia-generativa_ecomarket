# Calibración del umbral de relevancia

Puntaje = similitud coseno del mejor fragmento (1 − distancia de Chroma).

| Tipo | n | mínimo | media | máximo |
|---|---|---|---|---|
| in | 29 | 0.837 | 0.887 | 0.927 |
| ooc_facil | 6 | 0.722 | 0.773 | 0.807 |
| ooc_dificil | 8 | 0.798 | 0.820 | 0.842 |

Separables (máx. ooc_facil 0.807 < mín. in 0.837): **True**
Umbral propuesto (punto medio): **0.822**

| Umbral | Falsos rechazados (in) | Falsos aceptados (ooc_facil) | Falsos aceptados (ooc_dificil) |
|---|---|---|---|
| 0.807 | 0/29 | 0/6 | 7/8 |
| 0.822 | 0/29 | 0/6 | 4/8 |
| 0.837 | 0/29 | 0/6 | 1/8 |

## Puntaje por pregunta (de mayor a menor dentro de cada tipo)

**in**
- 0.927 Q01: ¿Cuántos días tengo para devolver un producto?
- 0.924 Q25: ¿Cuántas velas vienen en el pack de cera de soja?
- 0.916 Q08: ¿Cuánto cuesta el envío estándar?
- 0.915 Q24: ¿Qué tallas hay de la camiseta de algodón orgánico?
- 0.908 Q07: ¿Qué condiciones debe cumplir un producto para que acepten la devolución?
- 0.908 Q26: ¿Cómo debo lavar los productos de bambú?
- 0.905 Q13: Ya pasó la fecha estimada y mi pedido no llega, ¿qué hago?
- 0.901 Q05: ¿Cuánto demora el reembolso y por qué medio me devuelven el dinero?
- 0.900 Q17: ¿Qué medios de pago aceptan?
- 0.900 Q23: ¿Qué trae el set de cubiertos reutilizables?
- 0.899 Q19: ¿Me envían factura de mi compra?
- 0.897 Q14: ¿Puedo cancelar mi compra si el pedido ya salió?
- 0.895 Q22: ¿Cuántas horas de batería tienen los audífonos inalámbricos?
- 0.892 Q03: ¿Qué productos no se pueden devolver?
- 0.891 Q10: ¿Cuánto tarda el envío express y en qué ciudades está disponible?
- 0.887 Q12: ¿Qué significa que mi pedido esté retrasado?
- 0.886 Q09: ¿Desde qué valor de compra el envío es gratis?
- 0.885 Q15: ¿Puedo cambiar la dirección de entrega después de comprar?
- 0.880 Q04: ¿Cómo hago el trámite para devolver un producto?
- 0.878 Q20: ¿Hasta qué hora atiende una persona del servicio al cliente?
- 0.877 Q21: ¿De qué material es la botella de vidrio?
- 0.875 Q27: ¿Con qué materiales fabrican sus productos?
- 0.872 Q16: ¿Cómo puedo rastrear mi pedido?
- 0.862 Q18: ¿Puedo pagar cuando me entreguen el pedido?
- 0.858 Q28: ¿Puedo devolver la taza que tiene mi nombre grabado?
- 0.853 Q02: Compré una camiseta y no me gustó, ¿puedo devolverla?
- 0.850 Q11: ¿Envían a otros países?
- 0.847 Q06: ¿Quién paga el envío cuando devuelvo algo?
- 0.837 Q29: ¿Se puede devolver la granola?

**ooc_facil**
- 0.807 F06: ¿Qué receta me recomiendas para la cena de hoy?
- 0.805 F05: ¿Cuánto es 15 por 12?
- 0.784 F04: ¿Cómo se hace un bucle for en Python?
- 0.784 F02: Escríbeme un poema sobre el mar.
- 0.737 F01: ¿Cuál es la capital de Francia?
- 0.722 F03: ¿Quién ganó el último mundial de fútbol?

**ooc_dificil**
- 0.842 D06: ¿Puedo pagar mi compra en cuotas?
- 0.829 D07: ¿Venden ropa para niños?
- 0.824 D02: ¿Tienen tienda física en Bogotá?
- 0.822 D01: ¿Venden computadores portátiles?
- 0.818 D03: ¿Tienen programa de puntos o descuentos para clientes frecuentes?
- 0.816 D05: ¿Cuál es el teléfono de servicio al cliente?
- 0.811 D04: ¿Los electrónicos tienen garantía de dos años?
- 0.798 D08: ¿Tienen aplicación móvil?
