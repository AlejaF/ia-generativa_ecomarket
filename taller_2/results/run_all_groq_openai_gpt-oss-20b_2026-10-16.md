# Ejecución completa — groq/openai/gpt-oss-20b — 2026-10-16

| Paso | Resultado | Segundos |
|---|---|---|
| 1  fragmentos | ok | 1.4 |
| 2  embeddings | ok | 65.1 |
| 3  recuperación | ok | 43.6 |
| 4  umbral | ok | 44.0 |
| 6  fragmentación y solapamiento | ok | 55.4 |
| 7a RAGAS por ids | ok | 363.4 |
| 5  punta a punta (Groq) | ok | 273.0 |
| 8  experimentos de modificación (Groq) | ok | 399.8 |

## 1  fragmentos

```text
doc          n  media  min  max
politica     8    262  155  536
faq         14    277  153  396
catalogo    21    252  212  296
envios       9    275  113  521
total: 52 fragmentos
gold.json vs fragmentos: OK
Escrito results/chunks.md
```

## 2  embeddings

```text
con prefijos  paráfrasis=0.900 sin relación=0.819 Hit@1=0.90 Hit@4=0.97 MRR=0.93
sin prefijos  paráfrasis=0.918 sin relación=0.845 Hit@1=0.79 Hit@4=0.97 MRR=0.87
escala RR mezclado (como RAGAS)       techo=0.946 paráfrasis=0.885 suelo dominio=0.811 fuera=0.772
escala RR simétrico (query vs query)  techo=1.000 paráfrasis=0.900 suelo dominio=0.815 fuera=0.767
Escrito results/embeddings.md
```

## 3  recuperación

```text
total      n=29 Hit@1=0.90 Hit@4=0.97 MRR=0.93
politica   n= 7 Hit@1=1.00 Hit@4=1.00 MRR=1.00
faq        n=14 Hit@1=0.86 Hit@4=1.00 MRR=0.92
envios     n= 1 Hit@1=0.00 Hit@4=0.00 MRR=0.00
catalogo   n= 7 Hit@1=1.00 Hit@4=1.00 MRR=1.00
3 preguntas sin acierto en la posición 1. Escrito results/retrieval.md
```

## 4  umbral

```text
in           n=29 min=0.837 media=0.887 max=0.927
ooc_facil    n= 6 min=0.722 media=0.773 max=0.807
ooc_dificil  n= 8 min=0.798 media=0.820 max=0.842
separable in/ooc_facil: True  -> umbral propuesto 0.822
Escrito results/threshold.md
```

## 6  fragmentación y solapamiento

```text
estructura           n= 52 Hit@1=0.90 Hit@4=0.97 MRR=0.93 chars/consulta=1109
tamaño fijo 1000/0   n= 15 Hit@1=0.86 Hit@4=0.97 MRR=0.90 chars/consulta=3453
tamaño fijo 500/80   n= 36 Hit@1=0.86 Hit@4=0.97 MRR=0.91 chars/consulta=1450
solapamiento (a) todo                 Hit@1=0.75 Hit@4=0.92 MRR=0.82
solapamiento (b) sin FAQ duplicadas   Hit@1=0.75 Hit@4=0.92 MRR=0.83
duplicados juntos en el top 4: {'preguntas de envíos/pagos/pedidos': '12/12', "las 29 preguntas 'in'": '13/29'}
Escrito results/chunking_baseline.md
```

## 7a RAGAS por ids

```text
RAGAS por ids (k=4, 29 preguntas): precisión=0.34 exhaustividad=0.90 -> results/ragas_ids.md
```

## 5  punta a punta (Groq)

```text
Generador: groq/openai/gpt-oss-20b | 11 preguntas | pausa 20 s
Q08 sin_rag=NO(2.6s) con_rag=ok(16.7s) con_rag_reglas=ok(16.7s)
Q14 sin_rag=NO(1.1s) con_rag=ok(1.1s) con_rag_reglas=ok(1.1s)
Q18 sin_rag=NO(0.8s) con_rag=NO(1.1s) con_rag_reglas=NO(1.1s)
Q28 sin_rag=NO(1.1s) con_rag=NO(0.9s) con_rag_reglas=ok(1.8s)
F03 sin_rag=NO(1.0s) con_rag=ok(0.1s) con_rag_reglas=ok(0.1s)
D01 sin_rag=NO(0.8s) con_rag=ok(0.7s) con_rag_reglas=ok(0.7s)
D04 sin_rag=NO(0.8s) con_rag=ok(0.2s) con_rag_reglas=ok(0.2s)
R1  sin_rag=NO(0.8s) con_rag=NO(1.9s) con_rag_reglas=ok(1.4s)
R2  sin_rag=ok(0.9s) con_rag=ok(1.1s) con_rag_reglas=ok(0.9s)
R3  sin_rag=ok(0.5s) con_rag=ok(0.7s) con_rag_reglas=ok(0.9s)
P1  sin_rag=NO(0.9s) con_rag=ok(1.9s) con_rag_reglas=ok(1.9s)
tokens de la sesión: entrada 8566, salida 2010, llamadas 24
aciertos: {'sin_rag': 2, 'con_rag': 8, 'con_rag_reglas': 10} -> results/end_to_end_groq_openai_gpt-oss-20b_2026-10-16.md
```

## 8  experimentos de modificación (Groq)

```text
k: [(1, 0.9, 0.9, 291), (2, 0.93, 0.91, 536), (4, 0.97, 0.93, 1109), (6, 0.97, 0.93, 1696)]
D01 top1=0.822 pasa=True respondida: actual=False sin_instruccion=True sin_umbral=False
D02 top1=0.824 pasa=True respondida: actual=False sin_instruccion=True sin_umbral=False
D03 top1=0.818 pasa=False respondida: actual=False sin_instruccion=False sin_umbral=False
D04 top1=0.811 pasa=False respondida: actual=False sin_instruccion=False sin_umbral=False
D05 top1=0.816 pasa=False respondida: actual=False sin_instruccion=False sin_umbral=False
D06 top1=0.842 pasa=True respondida: actual=False sin_instruccion=True sin_umbral=False
D07 top1=0.829 pasa=True respondida: actual=False sin_instruccion=True sin_umbral=False
D08 top1=0.798 pasa=False respondida: actual=False sin_instruccion=False sin_umbral=False
Quiero devolver unos audífonos, los compré ha... con_secciones_7_y_8: 3/3 elementos de la política | sin_secciones_7_y_8: 1/3 elementos de la política
Quiero devolver mi botella reutilizable de ac... con_secciones_7_y_8: 3/3 elementos de la política | sin_secciones_7_y_8: 1/3 elementos de la política
Escrito results/modificaciones_groq_openai_gpt-oss-20b_2026-10-16.md
```
