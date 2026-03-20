# Inventario Logistica ETL

Programa en Python para procesar un archivo Excel de logistica, generar un Excel limpio para revision y publicar tablas analiticas en formato `parquet` para Power BI.

## Que hace el programa

- Lee el archivo Excel original desde la carpeta de entrada.
- Limpia y normaliza la informacion de la hoja `PPTO 2026`.
- Genera un Excel limpio para revision operativa.
- Genera un archivo de auditoria basico.
- Construye tablas analiticas en formato `parquet`.
- Registra cada ejecucion en logs y en un archivo de control.

## Requisitos

Necesitas tener instalado:

- Python 3.13 o compatible
- `pandas>=2.2.0`
- `openpyxl>=3.1.0`
- `pyarrow>=15.0.0`
- `numpy>=1.26.0`

Las dependencias del proyecto estan definidas en `requirements.txt`.

## Preparacion del entorno

El proyecto usa un entorno virtual local llamado `.venv`.

Si necesitas crearlo desde cero:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Como ejecutar el programa

Opcion recomendada:

```powershell
.\.venv\Scripts\Activate.ps1
python main.py
```

Tambien puedes ejecutarlo directamente asi:

```powershell
.\.venv\Scripts\python.exe main.py
```

## Archivo de entrada

El programa espera encontrar en la carpeta de entrada un archivo llamado:

- `PTTO 2026.xlsx`

La hoja de lectura esta fijada en:

- `PPTO 2026`

## Archivos que genera

### Salidas para revision

- `PROCESADOS/Excel/PTTO 2026 ETL.xlsx`
- `PROCESADOS/Auditoria/PTTO 2026 AUDITORIA.xlsx`

### Salidas para Power BI

- `DW/fact_compras_logistica.parquet`
- `DW/dim_fecha.parquet`
- `DW/dim_area.parquet`
- `DW/dim_proveedor.parquet`
- `DW/dim_material.parquet`
- `DW/dim_estado.parquet`

## Estructura de carpetas

```text
REPORTE/
|- ORIGINAL/
|- PROCESADOS/
|  |- Excel/
|  \- Auditoria/
|- DW/
|- LOGS/
\- control_procesamiento.csv
```

## Comportamiento actual

- El Excel limpio siempre se genera con el nombre `PTTO 2026 ETL.xlsx`.
- La auditoria siempre se genera con el nombre `PTTO 2026 AUDITORIA.xlsx`.
- Los archivos `.parquet` de `DW` se reemplazan en cada corrida.
- El archivo `control_procesamiento.csv` guarda historial de ejecuciones.
- El log tecnico queda en la carpeta `LOGS`.

## Nota importante

Si alguno de los archivos Excel de salida esta abierto mientras corre el proceso, Windows puede bloquear su reemplazo. En ese caso, cierra el archivo y vuelve a ejecutar el ETL.

