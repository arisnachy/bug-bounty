# Operación Aguja Negra — Informe técnico

## Estado

**Validación independiente publicada.** El parche upstream ya había sido presentado por otro colaborador en pandas PR #66541 antes de esta publicación. Este paquete no reclama autoría de ese PR; conserva el análisis, las pruebas y la evidencia producidos de forma independiente.

## Objetivo seleccionado

- Proyecto: `pandas-dev/pandas`
- Incidencia: GH#66522
- Título: `DataFrame.ewm(...).online().mean() ignores the decay for single-column frames`
- Área: ventanas exponenciales, cálculo online y Numba
- PR upstream existente: GH#66541

## Reproducción

Entorno local usado para ejecución:

```text
python=3.13.5
pandas=2.2.3
numpy=2.3.5
numba=0.65.1
platform=Linux-6.18.35-x86_64-with-glibc2.41
```

La versión local contiene la misma implementación defectuosa que se inspeccionó en el código de `main`.

### Antes del parche

```text
ONLINE
     A
0  1.0
1  1.5
2  2.0
3  2.5

BATCH
          A
0  1.000000
1  1.666667
2  2.428571
3  3.266667
```

El cálculo online devolvía una media acumulada sin el decaimiento exponencial esperado.

## Causa raíz

Había dos errores de dimensión independientes:

1. `OnlineExponentialMovingWindow.mean` construía `update_deltas` usando la última dimensión del objeto seleccionado. En un `DataFrame`, esa dimensión representa columnas, no observaciones. Con una sola columna producía un arreglo vacío.
2. El kernel `online_ewma` elegía el delta usando `j`, índice de columna. Los deltas representan la separación entre filas consecutivas, por lo que debe usarse `i - 1` para todas las columnas de la fila actual.

Con Numba sin comprobación de límites, el acceso al arreglo vacío no generaba una excepción fiable. El valor leído hacía que el factor de peso no decayese y ocultaba el fallo como un resultado numérico plausible.

## Corrección candidata

```diff
- old_wt[j] *= old_wt_factor ** deltas[j - 1]
+ old_wt[j] *= old_wt_factor ** deltas[i - 1]
```

```diff
- update_deltas = np.ones(max(self._selected_obj.shape[-1] - 1, 0), ...)
+ update_deltas = np.ones(max(np_array.shape[0] - 1, 0), ...)
```

La segunda operación se ejecuta después de construir `np_array`, de modo que también calcula correctamente la longitud durante `mean(update=...)`, donde se antepone el último estado acumulado.

## Pruebas independientes

1. Concordancia entre `online().mean()` y `mean()` para un `DataFrame` de una columna.
2. Validación del cálculo inicial y del camino incremental `update=`.
3. Combinaciones `adjust=True/False` e `ignore_na=True/False` con valores ausentes.
4. Prueba directa del kernel con deltas no uniformes `[1.0, 2.0]`, necesaria para detectar el uso incorrecto del índice de columna.
5. Pruebas de humo para `Series`, `DataFrame` de dos columnas y actualización de una sola fila.

## Evidencia ejecutada

### Código original

```text
5 failed in 8.30s
```

Las cinco pruebas de regresión fallaron como se esperaba.

### Código corregido

```text
5 pruebas nuevas:                 5 passed
pruebas relacionadas de humo:    3 passed
pruebas oficiales seleccionadas: 6 passed
compilación sintáctica:           passed
```

El reproductor después del parche produjo resultados online idénticos al cálculo no online.

## Limitaciones

- Las pruebas ejecutables se realizaron contra pandas 2.2.3, cuya sección afectada reproduce la misma implementación defectuosa.
- No se ejecutó un checkout completo actual de `main` en este entorno.
- La suite oficial completa de `pandas/tests/window/test_online.py` no pudo cargarse porque el entorno no incluía `hypothesis`.
- Una matriz extensa con compilación paralela de Numba excedió el límite de ejecución disponible.
- El parche se comprobó contra los contextos de archivos upstream inspeccionados, pero debe validarse nuevamente contra el `main` vigente antes de cualquier uso futuro.

## Riesgo de regresión

El cambio es estrecho:

- no altera la fórmula de EWM;
- no cambia tipos ni API pública;
- conserva el comportamiento esperado para `Series` y marcos multicolumna;
- corrige la fuente de la longitud de `deltas` y el índice temporal utilizado por el kernel.

## Transparencia y atribución

Esta investigación fue desarrollada con asistencia de OpenAI Codex/ChatGPT a solicitud de Arisnachy Gómez Díaz. El PR upstream #66541 pertenece a su autor original. Este registro representa únicamente una validación independiente y no una reclamación de autoría sobre ese trabajo.
