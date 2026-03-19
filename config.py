from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "logs"
DOCS_DIR = BASE_DIR / "docs"

SOURCE_FILE = INPUT_DIR / "compras_logistica.xlsx"
SOURCE_SHEET = "PPTO 2026"

FACT_TABLE_NAME = "fact_compras_logistica"
DATE_DIM_NAME = "dim_fecha"
AREA_DIM_NAME = "dim_area"
SUPPLIER_DIM_NAME = "dim_proveedor"
MATERIAL_DIM_NAME = "dim_material"
STATUS_DIM_NAME = "dim_estado"

EXPORT_CSV = True
EXPORT_PARQUET = True

ID_COLUMNS = {
    "fact": "id_compra",
    "area": "id_area",
    "proveedor": "id_proveedor",
    "material": "id_material",
    "estado": "id_estado",
}

DATE_COLUMNS = [
    "fecha_oc",
    "fecha_recepcion",
    "fecha_prog_entrega",
]

NUMERIC_COLUMNS = [
    "cantidad",
    "pu_soles",
    "importe_soles",
    "pu_usd",
    "importe_usd",
    "total_punit_usd",
    "importe_total_usd",
]

COLUMN_MAPPING = {
    "SEM": "semana",
    "COD": "cod_material",
    "MATERIAL": "material",
    "UND MED": "unidad_medida",
    "CANT.": "cantidad",
    "PU SOLES": "pu_soles",
    "IMPORTE SO": "importe_soles",
    "PU USD": "pu_usd",
    "IMPORTE US": "importe_usd",
    "TOTAL P.UNIT US$": "total_punit_usd",
    "IMPORTE TOTAL US$": "importe_total_usd",
    "SOLICITANTE": "area_solicitante",
    "REFERENCIA": "referencia",
    "PROVEEDOR": "proveedor",
    "FORMA DE PAGO": "forma_pago",
    "ESTADO RECEPCION": "estado_recepcion",
    "ESTADO RECEPCION ": "estado_recepcion",
    "FECHA RECEPCION": "fecha_recepcion",
    "FECHA PROG ENTREGA": "fecha_prog_entrega",
    "NRO ORDEN DE COMPRA": "nro_oc",
    "FECHA OC": "fecha_oc",
    "# GUIA": "nro_guia",
    "# FACTURA": "nro_factura",
}
