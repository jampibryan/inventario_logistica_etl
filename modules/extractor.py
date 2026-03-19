import logging

import pandas as pd

from config import SOURCE_FILE, SOURCE_SHEET


def extract_budget_sheet() -> pd.DataFrame:
    """Lee la hoja principal del Excel de logistica."""
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(f"No se encontro el archivo fuente: {SOURCE_FILE}")

    logging.info("Leyendo archivo fuente: %s", SOURCE_FILE.name)
    df = pd.read_excel(SOURCE_FILE, sheet_name=SOURCE_SHEET)
    logging.info("Filas leidas: %s | Columnas leidas: %s", len(df), len(df.columns))
    return df
