import pandas as pd

from config import ID_COLUMNS


FACT_COLUMNS = [
    "id_compra",
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
]


def build_fact_table(df: pd.DataFrame) -> pd.DataFrame:
    """Construye la tabla fact inicial con columnas de negocio homologadas."""
    fact_df = df.copy()

    for column in FACT_COLUMNS:
        if column not in fact_df.columns:
            fact_df[column] = pd.NA

    fact_df = fact_df[FACT_COLUMNS].copy()
    fact_df[ID_COLUMNS["fact"]] = range(1, len(fact_df) + 1)
    return fact_df
