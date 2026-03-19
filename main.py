import logging

import pandas as pd

from config import EXPORT_CSV, EXPORT_PARQUET, LOG_DIR
from modules.cleaner import clean_logistics_data
from modules.dimensions import build_dimensions
from modules.extractor import extract_budget_sheet
from modules.loader import export_tables
from modules.transformer import build_fact_table
from modules.validator import validate_tables


def configure_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(LOG_DIR / "etl.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def run_etl() -> dict[str, pd.DataFrame]:
    raw_df = extract_budget_sheet()
    clean_df = clean_logistics_data(raw_df)
    fact_df = build_fact_table(clean_df)
    dims = build_dimensions(fact_df)

    tables = {"fact_compras_logistica": fact_df, **dims}
    validate_tables(tables)
    export_tables(tables, export_csv=EXPORT_CSV, export_parquet=EXPORT_PARQUET)
    return tables


if __name__ == "__main__":
    configure_logging()
    logging.info("Inicio del ETL de logistica")
    try:
        tables = run_etl()
        logging.info("ETL finalizado. Tablas generadas: %s", ", ".join(tables.keys()))
    except FileNotFoundError as exc:
        logging.error("%s", exc)
        logging.info("Coloca el archivo Excel fuente dentro de la carpeta input y vuelve a ejecutar.")
    except Exception:
        logging.exception("El ETL termino con error")
        raise
