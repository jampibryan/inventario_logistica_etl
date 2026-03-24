import logging

import pandas as pd

from config import (
    CRITICAL_FACT_COLUMNS,
    DATE_COLUMNS,
    DIMENSION_MATCH_RULES,
    FACT_TABLE_NAME,
    MAX_VALID_YEAR,
    MIN_VALID_YEAR,
)


AUDIT_COLUMNS = ["tipo", "tabla", "campo", "valor", "detalle"]


def _validate_dimension_keys(fact_df: pd.DataFrame) -> list[dict[str, object]]:
    audit_rows: list[dict[str, object]] = []

    for rule in DIMENSION_MATCH_RULES:
        id_column = rule["id_column"]
        natural_columns = rule["natural_columns"]
        detalle = rule["detalle"]

        if id_column not in fact_df.columns:
            audit_rows.append(
                {
                    "tipo": "id_dimension_faltante",
                    "tabla": FACT_TABLE_NAME,
                    "campo": id_column,
                    "valor": pd.NA,
                    "detalle": detalle,
                }
            )
            continue

        available_natural_columns = [column for column in natural_columns if column in fact_df.columns]
        if not available_natural_columns:
            audit_rows.append(
                {
                    "tipo": "columnas_naturales_faltantes",
                    "tabla": FACT_TABLE_NAME,
                    "campo": id_column,
                    "valor": pd.NA,
                    "detalle": detalle,
                }
            )
            continue

        natural_match_mask = fact_df[available_natural_columns].notna().all(axis=1)
        missing_id_count = int((natural_match_mask & fact_df[id_column].isna()).sum())

        if missing_id_count:
            logging.warning(
                "Se detectaron %s filas donde %s quedo vacio pese a tener columnas naturales completas",
                missing_id_count,
                id_column,
            )

        audit_rows.append(
            {
                "tipo": "ids_dimension_sin_match",
                "tabla": FACT_TABLE_NAME,
                "campo": id_column,
                "valor": missing_id_count,
                "detalle": detalle,
            }
        )

    return audit_rows


def validate_tables(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Run minimal data-quality checks and return an audit summary."""
    audit_rows: list[dict[str, object]] = []

    for table_name, df in tables.items():
        logging.info("Tabla %s | filas=%s | columnas=%s", table_name, len(df), len(df.columns))
        audit_rows.append(
            {
                "tipo": "filas_tabla",
                "tabla": table_name,
                "campo": pd.NA,
                "valor": int(len(df)),
                "detalle": "conteo_filas",
            }
        )

    fact_df = tables.get(FACT_TABLE_NAME)
    if fact_df is None:
        raise ValueError(f"No se genero la tabla {FACT_TABLE_NAME}")

    duplicated_rows = int(fact_df.duplicated().sum())
    if duplicated_rows:
        logging.warning("Se detectaron %s filas duplicadas exactas en la fact", duplicated_rows)

    audit_rows.append(
        {
            "tipo": "filas_duplicadas",
            "tabla": FACT_TABLE_NAME,
            "campo": pd.NA,
            "valor": duplicated_rows,
            "detalle": "duplicados_exactos_en_fact",
        }
    )

    for column in CRITICAL_FACT_COLUMNS:
        if column not in fact_df.columns:
            audit_rows.append(
                {
                    "tipo": "columna_faltante",
                    "tabla": FACT_TABLE_NAME,
                    "campo": column,
                    "valor": pd.NA,
                    "detalle": "campo_critico_no_generado",
                }
            )
            continue

        null_count = int(fact_df[column].isna().sum())
        audit_rows.append(
            {
                "tipo": "nulos_campo_critico",
                "tabla": FACT_TABLE_NAME,
                "campo": column,
                "valor": null_count,
                "detalle": "conteo_nulos",
            }
        )

    for column in DATE_COLUMNS:
        if column not in fact_df.columns:
            continue

        valid_dates = pd.to_datetime(fact_df[column].dropna(), errors="coerce")
        out_of_range_count = int(((valid_dates.dt.year < MIN_VALID_YEAR) | (valid_dates.dt.year > MAX_VALID_YEAR)).sum())
        audit_rows.append(
            {
                "tipo": "fechas_fuera_rango",
                "tabla": FACT_TABLE_NAME,
                "campo": column,
                "valor": out_of_range_count,
                "detalle": f"rango_permitido_{MIN_VALID_YEAR}_{MAX_VALID_YEAR}",
            }
        )

    audit_rows.extend(_validate_dimension_keys(fact_df))
    return pd.DataFrame(audit_rows, columns=AUDIT_COLUMNS)
