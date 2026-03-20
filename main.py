import logging
from pathlib import Path

import pandas as pd

from config import EXPORT_CSV, EXPORT_PARQUET, LOG_DIR, ORIGINAL_DIR
from modules.cleaner import clean_logistics_data
from modules.dimensions import build_dimensions
from modules.extractor import extract_budget_sheet
from modules.loader import export_review_outputs, export_tables, update_control_file
from modules.transformer import build_fact_table
from modules.validator import validate_tables


DEFAULT_SOURCE_PLACEHOLDER = ORIGINAL_DIR / "archivo_fuente.xlsx"


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
    source_file, raw_df = extract_budget_sheet()
    clean_df = clean_logistics_data(raw_df)
    fact_df = build_fact_table(clean_df)
    dims = build_dimensions(fact_df)

    tables = {"fact_compras_logistica": fact_df, **dims}
    audit_df = validate_tables(tables)
    export_review_outputs(clean_df, audit_df, source_file)
    export_tables(tables, export_csv=EXPORT_CSV, export_parquet=EXPORT_PARQUET)
    update_control_file(
        source_file=source_file,
        status="OK",
        rows_read=len(raw_df),
        rows_fact=len(fact_df),
        message="Proceso completado correctamente.",
    )
    return tables


if __name__ == "__main__":
    configure_logging()
    logging.info("Inicio del ETL de logistica")
    try:
        tables = run_etl()
        logging.info("ETL finalizado. Tablas generadas: %s", ", ".join(tables.keys()))
    except FileNotFoundError as exc:
        logging.error("%s", exc)
        update_control_file(
            source_file=Path(getattr(exc, "filename", "") or DEFAULT_SOURCE_PLACEHOLDER),
            status="ERROR",
            rows_read=0,
            rows_fact=0,
            message=str(exc),
        )
    except Exception as exc:
        logging.exception("El ETL termino con error")
        update_control_file(
            source_file=DEFAULT_SOURCE_PLACEHOLDER,
            status="ERROR",
            rows_read=0,
            rows_fact=0,
            message=str(exc),
        )
        raise
