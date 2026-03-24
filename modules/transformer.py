import logging

import pandas as pd

from config import COST_COLUMNS, DATE_KEY_COLUMNS, ID_COLUMNS, REQUIRED_FACT_COLUMNS, SOURCE_ROW_COLUMN


TYPE_ERROR_FLAG_COLUMN = "_fila_tipo_invalido"
TYPE_ERROR_DETAIL_COLUMN = "_detalle_tipos_invalidos"
INVALID_DETAIL_SEPARATOR = ";;"
INVALID_PART_SEPARATOR = "|"
LOG_SEPARATOR = "-------------------------------------------------"
FACT_INTERNAL_COLUMNS = [SOURCE_ROW_COLUMN, TYPE_ERROR_FLAG_COLUMN, TYPE_ERROR_DETAIL_COLUMN]

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


def _log_section(title: str, lines: list[str]) -> None:
    if not lines:
        return

    logging.warning(LOG_SEPARATOR)
    logging.warning(title)
    logging.warning(LOG_SEPARATOR)
    for line in lines:
        logging.warning(line)


def _excel_row_label(row: pd.Series) -> str:
    row_number = row.get(SOURCE_ROW_COLUMN, pd.NA)
    if pd.isna(row_number):
        return "Fila desconocida"
    return f"Fila Excel {int(row_number)}"


def _build_type_issue_lines(fact_df: pd.DataFrame) -> tuple[list[str], list[dict[str, object]]]:
    if TYPE_ERROR_DETAIL_COLUMN not in fact_df.columns:
        return [], []

    issue_lines: list[str] = []
    audit_rows: list[dict[str, object]] = []

    invalid_rows = fact_df.loc[fact_df[TYPE_ERROR_FLAG_COLUMN].fillna(False)].copy()
    if invalid_rows.empty:
        return issue_lines, audit_rows

    for _, row in invalid_rows.iterrows():
        detail_text = row.get(TYPE_ERROR_DETAIL_COLUMN, pd.NA)
        if pd.isna(detail_text):
            continue

        for item in str(detail_text).split(INVALID_DETAIL_SEPARATOR):
            parts = item.split(INVALID_PART_SEPARATOR, 2)
            if len(parts) != 3:
                continue
            column, expected_type, original_value = parts
            issue_lines.append(
                f"{_excel_row_label(row)} | Columna: {column} | Esperado: {expected_type} | Valor original: {original_value}"
            )
            audit_rows.append(
                {
                    "tipo": "fila_con_tipo_invalido",
                    "tabla": "fact_compras_logistica",
                    "campo": column,
                    "valor": row.get(SOURCE_ROW_COLUMN, pd.NA),
                    "detalle": f"esperado={expected_type}; valor_original={original_value}",
                }
            )

    return issue_lines, audit_rows


def _build_missing_required_lines(fact_df: pd.DataFrame) -> tuple[list[str], list[dict[str, object]]]:
    issue_lines: list[str] = []
    audit_rows: list[dict[str, object]] = []

    for _, row in fact_df.iterrows():
        for column in REQUIRED_FACT_COLUMNS:
            if column in fact_df.columns and pd.isna(row[column]):
                issue_lines.append(f"{_excel_row_label(row)} | Columna requerida vacia: {column}")
                audit_rows.append(
                    {
                        "tipo": "fila_con_requerido_vacio",
                        "tabla": "fact_compras_logistica",
                        "campo": column,
                        "valor": row.get(SOURCE_ROW_COLUMN, pd.NA),
                        "detalle": "campo_requerido_para_analisis",
                    }
                )

    return issue_lines, audit_rows


def _build_missing_cost_lines(fact_df: pd.DataFrame) -> tuple[list[str], list[dict[str, object]]]:
    issue_lines: list[str] = []
    audit_rows: list[dict[str, object]] = []

    missing_cost_mask = ~fact_df[COST_COLUMNS].notna().any(axis=1)
    missing_cost_rows = fact_df.loc[missing_cost_mask]

    for _, row in missing_cost_rows.iterrows():
        issue_lines.append(
            f"{_excel_row_label(row)} | Sin importe informado en las columnas: {', '.join(COST_COLUMNS)}"
        )
        audit_rows.append(
            {
                "tipo": "fila_sin_importe",
                "tabla": "fact_compras_logistica",
                "campo": pd.NA,
                "valor": row.get(SOURCE_ROW_COLUMN, pd.NA),
                "detalle": "sin_importe_soles_ni_importe_usd",
            }
        )

    return issue_lines, audit_rows


def filter_valid_fact_rows(fact_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Reporta observaciones de calidad sin descartar filas de la fact."""
    type_mask = ~fact_df[TYPE_ERROR_FLAG_COLUMN].fillna(False) if TYPE_ERROR_FLAG_COLUMN in fact_df.columns else pd.Series(True, index=fact_df.index)
    required_mask = fact_df[REQUIRED_FACT_COLUMNS].notna().all(axis=1)
    cost_mask = fact_df[COST_COLUMNS].notna().any(axis=1)

    type_issue_lines, type_issue_audit = _build_type_issue_lines(fact_df)
    missing_required_lines, missing_required_audit = _build_missing_required_lines(fact_df)
    missing_cost_lines, missing_cost_audit = _build_missing_cost_lines(fact_df)

    _log_section("VALIDACIONES DE TIPOS DE DATO", type_issue_lines)
    _log_section("CAMPOS REQUERIDOS VACIOS", missing_required_lines)
    _log_section("FILAS SIN IMPORTES PARA ANALISIS", missing_cost_lines)

    observed_issue_rows = int((~type_mask | ~required_mask | ~cost_mask).sum())
    logging.warning(LOG_SEPARATOR)
    logging.warning("RESUMEN DE OBSERVACIONES DE CALIDAD")
    logging.warning(LOG_SEPARATOR)
    logging.warning("Filas con tipos invalidos: %s", int((~type_mask).sum()))
    logging.warning("Filas con requeridos vacios: %s", int((~required_mask).sum()))
    logging.warning("Filas sin importes: %s", int((~cost_mask).sum()))
    logging.warning("Filas observadas con al menos una incidencia: %s", observed_issue_rows)

    output_df = fact_df.drop(columns=FACT_INTERNAL_COLUMNS, errors="ignore").copy().reset_index(drop=True)
    output_df[ID_COLUMNS["fact"]] = range(1, len(output_df) + 1)

    audit_payload = [
        {
            "tipo": "filas_observadas_total",
            "tabla": "fact_compras_logistica",
            "campo": pd.NA,
            "valor": observed_issue_rows,
            "detalle": "filas_con_alguna_incidencia",
        },
        {
            "tipo": "filas_con_tipo_invalido",
            "tabla": "fact_compras_logistica",
            "campo": pd.NA,
            "valor": int((~type_mask).sum()),
            "detalle": "tipos_de_dato_invalidos",
        },
        {
            "tipo": "filas_con_requeridos_vacios",
            "tabla": "fact_compras_logistica",
            "campo": pd.NA,
            "valor": int((~required_mask).sum()),
            "detalle": "faltan_campos_requeridos",
        },
        {
            "tipo": "filas_sin_importes",
            "tabla": "fact_compras_logistica",
            "campo": pd.NA,
            "valor": int((~cost_mask).sum()),
            "detalle": "sin_importe_soles_ni_importe_usd",
        },
        *type_issue_audit,
        *missing_required_audit,
        *missing_cost_audit,
    ]
    audit_rows = pd.DataFrame(audit_payload, columns=AUDIT_COLUMNS)
    return output_df, audit_rows
