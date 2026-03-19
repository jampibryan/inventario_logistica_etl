# Inventario Logistica ETL

Proyecto base para construir un ETL de compras y logistica a partir de la hoja `PPTO 2026` de un archivo Excel.

## Objetivo

Transformar un Excel operativo en un modelo analitico con:

- `fact_compras_logistica`
- `dim_fecha`
- `dim_area`
- `dim_proveedor`
- `dim_material`
- `dim_estado`

## Flujo inicial

1. Leer el archivo Excel fuente.
2. Limpiar encabezados y tipos de datos.
3. Normalizar columnas clave para compras/logistica.
4. Construir la tabla fact.
5. Generar dimensiones.
6. Validar calidad minima.
7. Exportar a `parquet` y `csv`.

