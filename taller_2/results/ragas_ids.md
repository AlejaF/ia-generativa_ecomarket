# RAGAS — métricas por ids de fragmentos (k=4, sin LLM)

| Grupo | Precisión del contexto | Exhaustividad del contexto |
|---|---|---|
| total | 0.34 | 0.90 |
| politica | 0.29 | 0.93 |
| faq | 0.45 | 0.96 |
| envios | 0.00 | 0.00 |
| catalogo | 0.25 | 0.86 |

Cómo leerlo: cada pregunta tiene 1 o 2 fragmentos de referencia y se recuperan 4, así que la precisión máxima posible es 0,25 (una referencia) o 0,5 (dos): un valor bajo no indica mala recuperación. Cuando hay dos fuentes válidas por la redundancia FAQ/envíos (p. ej. `faq::FAQ02` y `envios::costos-de-envio`), la exhaustividad por ids exige recuperar ambas, mientras que Hit@4 acepta cualquiera; por eso la exhaustividad es menor que Hit@4.
