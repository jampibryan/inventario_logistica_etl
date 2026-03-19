import logging

import pandas as pd

from config import OUTPUT_DIR


def export_tables(
    tables: dict[str, pd.DataFrame],
    export_csv: bool = True,
    export_parquet: bool = True,
) -> None:
    """Exporta tablas limpias a disco para Power BI o futuras cargas a BD."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for table_name, df in tables.items():
        if export_parquet:
            parquet_path = OUTPUT_DIR / f"{table_name}.parquet"
            df.to_parquet(parquet_path, index=False)
            logging.info("Parquet generado: %s", parquet_path.name)

        if export_csv:
            csv_path = OUTPUT_DIR / f"{table_name}.csv"
            df.to_csv(csv_path, index=False, encoding="utf-8-sig")
            logging.info("CSV generado: %s", csv_path.name)
