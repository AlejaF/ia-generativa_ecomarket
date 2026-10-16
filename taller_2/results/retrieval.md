# Recuperación (k=4, 29 preguntas 'in')

| Grupo | n | Hit@1 | Hit@4 | MRR |
|---|---|---|---|---|
| total | 29 | 0.90 | 0.97 | 0.93 |
| politica | 7 | 1.00 | 1.00 | 1.00 |
| faq | 14 | 0.86 | 1.00 | 0.92 |
| envios | 1 | 0.00 | 0.00 | 0.00 |
| catalogo | 7 | 1.00 | 1.00 | 1.00 |

Grupo = tipo de documento de la primera fuente esperada.

## Preguntas sin acierto en la posición 1

- Q12 «¿Qué significa que mi pedido esté retrasado?»: esperadas ['faq::FAQ05', 'envios::estados-del-pedido'], posición 2, recuperados ['faq::FAQ06', 'faq::FAQ05', 'envios::pedidos-retrasados', 'envios::estados-del-pedido']
- Q16 «¿Cómo puedo rastrear mi pedido?»: esperadas ['faq::FAQ04', 'envios::estados-del-pedido'], posición 3, recuperados ['faq::FAQ06', 'envios::pedidos-retrasados', 'faq::FAQ04', 'faq::FAQ05']
- Q18 «¿Puedo pagar cuando me entreguen el pedido?»: esperadas ['envios::medios-de-pago'], posición None, recuperados ['envios::cancelaciones-y-cambios-de-direccion', 'faq::FAQ07', 'envios::pedidos-retrasados', 'envios::metodos-y-tiempos-de-envio']