import logging

import pandas as pd

from config import COST_COLUMNS, DATE_KEY_COLUMNS, ID_COLUMNS, REQUIRED_FACT_COLUMNS


TYPE_ERROR_FLAG_COLUMN = "_fila_tipo_invalido"
TYPE_ERROR_DETAIL_COLUMN = "_detalle_tipos_invalidos"
FACT_INTERNAL_COLUMNS = [TYPE_ERROR_FLAG_COLUMN, TYPE_ERROR_DETAIL_COLUMN]

FACT_COLUMNS = [
    "id_compra",
    "id_material",
    "id_area",
    "id_proveedor",
    "id_forma_pago",
    "id_estado",
    "id_fecha_oc",
    "id_fecha_programada_entrega",
    "id_fecha_recepcion",
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
    "fecha_oc",
    "fecha_programada_entrega",
    "fecha_recepcion",
    "nro_oc",
    "nro_guia",
    "nro_factura",
    "comentarios",
]

AUDIT_COLUMNS = ["tipo", "tabla", "campo", "valor", "detalle"]


def build_fact_table(df: pd.DataFrame) -> pd.DataFrame:
    """Construye la tabla fact inicial con columnas de negocio homologadas."""
    fact_df = df.copy()
    fact_df[ID_COLUMNS["fact"]] = range(1, len(fact_df) + 1)

    for id_column in [
        ID_COLUMNS["material"],
        ID_COLUMNS["area"],
        ID_COLUMNS["proveedor"],
        ID_COLUMNS["forma_pago"],
        ID_COLUMNS["estado"],
        *DATE_KEY_COLUMNS.values(),
    ]:
        if id_column not in fact_df.columns:
            fact_df[id_column] = pd.NA

    for column in FACT_COLUMNS + FACT_INTERNAL_COLUMNS:
        if column not in fact_df.columns:
            fact_df[column] = pd.NA

    return fact_df[FACT_COLUMNS + FACT_INTERNAL_COLUMNS].copy()


def _build_type_audit_rows(fact_df: pd.DataFrame) -> list[dict[str, object]]:
    if TYPE_ERROR_DETAIL_COLUMN not in fact_df.columns:
        return []

    details = fact_df[TYPE_ERROR_DETAIL_COLUMN].dropna().astype("string")
    if details.empty:
        return []

    invalid_counts = details.str.split("|", regex=False).explode().value_counts()
    return [
        {
            "tipo": "tipos_invalidos_campo",
            "tabla": "fact_compras_logistica",
            "campo": column,
            "valor": int(count),
            "detalle": "filas_descartadas_por_tipo_invalido",
        }
        for column, count in invalid_counts.items()
    ]


def filter_valid_fact_rows(fact_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Keep only rows valid enough for dashboard consumption."""
    if TYPE_ERROR_FLAG_COLUMN in fact_df.columns:
        type_mask = ~fact_df[TYPE_ERROR_FLAG_COLUMN].fillna(False)
    else:
        type_mask = pd.Series(True, index=fact_df.index)

    required_mask = fact_df[REQUIRED_FACT_COLUMNS].notna().all(axis=1)
    cost_mask = fact_df[COST_COLUMNS].notna().any(axis=1)
    valid_mask = type_mask & required_mask & cost_mask

    invalid_type = int((~type_mask).sum())
    invalid_required = int((type_mask & ~required_mask).sum())
    invalid_cost = int((type_mask & required_mask & ~cost_mask).sum())
    dropped_rows = int((~valid_mask).sum())

    if dropped_rows:
        logging.warning(
            "Se descartaron %s filas de la fact por calidad de datos para el dashboard",
            dropped_rows,
        )

    filtered_df = fact_df.loc[valid_mask].copy().reset_index(drop=True)
    filtered_df[ID_COLUMNS["fact"]] = range(1, len(filtered_df) + 1)
    filtered_df = filtered_df.drop(columns=FACT_INTERNAL_COLUMNS, errors="ignore")

    audit_payload = [
        {
            "tipo": "filas_descartadas",
            "tabla": "fact_compras_logistica",
            "campo": pd.NA,
            "valor": dropped_rows,
            "detalle": "filas_excluidas_por_reglas_dashboard",
        },
        {
            "tipo": "filas_descartadas_tipo",
            "tabla": "fact_compras_logistica",
            "campo": pd.NA,
            "valor": invalid_type,
            "detalle": "tipos_de_dato_invalidos",
        },
        {
            "tipo": "filas_descartadas_requeridos",
            "tabla": "fact_compras_logistica",
            "campo": pd.NA,
            "valor": invalid_required,
            "detalle": "faltan_campos_requeridos",
        },
        {
            "tipo": "filas_descartadas_importes",
            "tabla": "fact_compras_logistica",
            "campo": pd.NA,
            "valor": invalid_cost,
            "detalle": "sin_importe_soles_ni_importe_usd",
        },
        *_build_type_audit_rows(fact_df),
    ]
    audit_rows = pd.DataFrame(audit_payload, columns=AUDIT_COLUMNS)
    return filtered_df, audit_rows

