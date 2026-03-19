import logging
import re

import pandas as pd

from config import COLUMN_MAPPING, DATE_COLUMNS, NUMERIC_COLUMNS


def _normalize_header(value: str) -> str:
    text = str(value).strip().upper()
    text = re.sub(r"\s+", " ", text)
    return text


def clean_logistics_data(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia encabezados, normaliza nombres y convierte tipos basicos."""
    clean_df = df.copy()
    clean_df.columns = [_normalize_header(column) for column in clean_df.columns]
    clean_df = clean_df.rename(columns=COLUMN_MAPPING)

    clean_df = clean_df.dropna(how="all").reset_index(drop=True)

    for column in clean_df.select_dtypes(include="object").columns:
        clean_df[column] = clean_df[column].astype(str).str.strip()
        clean_df[column] = clean_df[column].replace({"nan": None, "": None})

    for column in NUMERIC_COLUMNS:
        if column in clean_df.columns:
            clean_df[column] = pd.to_numeric(clean_df[column], errors="coerce")

    for column in DATE_COLUMNS:
        if column in clean_df.columns:
            clean_df[column] = pd.to_datetime(clean_df[column], errors="coerce")

    logging.info("Columnas limpias y estandarizadas")
    return clean_df
