import logging

import pandas as pd


def validate_tables(tables: dict[str, pd.DataFrame]) -> None:
    """Ejecuta controles minimos para tener visibilidad temprana de calidad."""
    for table_name, df in tables.items():
        logging.info("Tabla %s | filas=%s | columnas=%s", table_name, len(df), len(df.columns))

    fact_df = tables.get("fact_compras_logistica")
    if fact_df is None:
        raise ValueError("No se genero la tabla fact_compras_logistica")

    if fact_df.empty:
        logging.warning("La tabla fact esta vacia")

    duplicated_rows = fact_df.duplicated().sum()
    if duplicated_rows:
        logging.warning("Se detectaron %s filas duplicadas exactas en la fact", duplicated_rows)
