import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent
REPORT_ROOT = PROJECT_ROOT / "REPORTE"
ORIGINAL_DIR = REPORT_ROOT / "ORIGINAL"
PROCESSED_DIR = REPORT_ROOT / "PROCESADOS"
PROCESSED_EXCEL_DIR = PROCESSED_DIR / "Excel"
PROCESSED_AUDIT_DIR = PROCESSED_DIR / "Auditoria"
DW_DIR = REPORT_ROOT / "DW"
LOG_DIR = REPORT_ROOT / "LOGS"
CONTROL_FILE = REPORT_ROOT / "control_procesamiento.csv"

SOURCE_FILENAME = "PTTO 2026.xlsx"
SOURCE_FILE = ORIGINAL_DIR / SOURCE_FILENAME
SOURCE_SHEET = "PPTO 2026"

REVIEW_EXCEL_NAME = os.getenv("ETL_REVIEW_EXCEL_NAME", "PTTO 2026 ETL.xlsx")
AUDIT_EXCEL_NAME = os.getenv("ETL_AUDIT_EXCEL_NAME", "PTTO 2026 AUDITORIA.xlsx")
OVERWRITE_OUTPUTS = True

FACT_TABLE_NAME = "fact_compras_logistica"
DATE_DIM_NAME = "dim_fecha"
AREA_DIM_NAME = "dim_area"
SUPPLIER_DIM_NAME = "dim_proveedor"
MATERIAL_DIM_NAME = "dim_material"
STATUS_DIM_NAME = "dim_estado"

EXPORT_CSV = False
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
    "fecha_programada_entrega",
]

NUMERIC_COLUMNS = [
    "precio_unitario_soles",
    "importe_soles",
    "precio_unitario_usd",
    "importe_usd",
    "total_precio_unit_usd",
    "importe_total_usd",
]

INTEGER_COLUMNS = [
    "semana",
    "cantidad",
]

TEXT_COLUMNS = [
    "codigo",
    "material",
    "unidad_medida",
    "solicitante",
    "referencia",
    "proveedor",
    "forma_pago",
    "estado_recepcion",
    "nro_oc",
    "nro_guia",
    "nro_factura",
    "comentarios",
]

CRITICAL_FACT_COLUMNS = [
    "semana",
    "codigo",
    "material",
    "cantidad",
    "proveedor",
    "fecha_oc",
]

COLUMN_MAPPING = {
    "SEM": "semana",
    "COD": "codigo",
    "MATERIAL": "material",
    "UND MED": "unidad_medida",
    "UNID MED": "unidad_medida",
    "CANT.": "cantidad",
    "PU SOLES": "precio_unitario_soles",
    "IMPORTE SOLES": "importe_soles",
    "IMPORTE SO": "importe_soles",
    "PU USD": "precio_unitario_usd",
    "IMPORTE USD": "importe_usd",
    "IMPORTE US": "importe_usd",
    "TOTAL P.UNIT US$": "total_precio_unit_usd",
    "IMPORTE TOTAL US$": "importe_total_usd",
    "SOLICITANTE": "solicitante",
    "REFERENCIA": "referencia",
    "PROVEEDOR": "proveedor",
    "FORMA DE PAGO": "forma_pago",
    "ESTADO RECEPCION OC": "estado_recepcion",
    "ESTADO RECEPCIÓN OC": "estado_recepcion",
    "ESTADO RECEPCION": "estado_recepcion",
    "ESTADO RECEPCIÓN": "estado_recepcion",
    "FECHA RECEPCION": "fecha_recepcion",
    "FECHA RECEPCIÓN": "fecha_recepcion",
    "FECHA PROG ENTREGA": "fecha_programada_entrega",
    "NRO ORDEN DE COMPRA": "nro_oc",
    "FECHA OC": "fecha_oc",
    "# GUIA": "nro_guia",
    "# GUÍA": "nro_guia",
    "# FACTURA": "nro_factura",
    "COMENTARIOS": "comentarios",
}

VISUAL_COLUMN_NAMES = {
    "semana": "SEMANA",
    "codigo": "CÓDIGO",
    "material": "MATERIAL",
    "unidad_medida": "UNIDAD MEDIDA",
    "cantidad": "CANTIDAD",
    "precio_unitario_soles": "PRECIO UNITARIO SOLES",
    "importe_soles": "IMPORTE SOLES",
    "precio_unitario_usd": "PRECIO UNITARIO USD",
    "importe_usd": "IMPORTE USD",
    "total_precio_unit_usd": "TOTAL PRECIO UNIT USD",
    "importe_total_usd": "IMPORTE TOTAL USD",
    "solicitante": "SOLICITANTE",
    "referencia": "REFERENCIA",
    "proveedor": "PROVEEDOR",
    "forma_pago": "FORMA DE PAGO",
    "estado_recepcion": "ESTADO RECEPCIÓN",
    "fecha_recepcion": "FECHA RECEPCIÓN",
    "fecha_programada_entrega": "FECHA PROGRAMADA ENTREGA",
    "nro_oc": "NRO OC",
    "fecha_oc": "FECHA OC",
    "nro_guia": "NRO GUÍA",
    "nro_factura": "NRO FACTURA",
    "comentarios": "COMENTARIOS",
}

REVIEW_COLUMN_ORDER = [
    "semana",
    "codigo",
    "material",
    "unidad_medida",
    "cantidad",
    "precio_unitario_soles",
    "importe_soles",
    "precio_unitario_usd",
    "importe_usd",
    "total_precio_unit_usd",
    "importe_total_usd",
    "solicitante",
    "referencia",
    "proveedor",
    "forma_pago",
    "estado_recepcion",
    "fecha_recepcion",
    "fecha_programada_entrega",
    "nro_oc",
    "fecha_oc",
    "nro_guia",
    "nro_factura",
    "comentarios",
]

