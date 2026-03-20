import logging

import pandas as pd

from config import CRITICAL_FACT_COLUMNS, FACT_TABLE_NAME


AUDIT_COLUMNS = ["tipo", "tabla", "campo", "valor", "detalle"]


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

    return pd.DataFrame(audit_rows, columns=AUDIT_COLUMNS)
