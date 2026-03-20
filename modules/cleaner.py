import logging
import re

import pandas as pd

from config import COLUMN_MAPPING, DATE_COLUMNS, INTEGER_COLUMNS, NUMERIC_COLUMNS, TEXT_COLUMNS


EMPTY_TEXT_VALUES = {"", "NAN", "NONE", "<NA>"}


def _normalize_header(value: str) -> str:
    text = str(value).strip().upper()
    text = re.sub(r"\s+", " ", text)
    return text


def _clean_numeric_series(series: pd.Series) -> pd.Series:
    cleaned = series.astype("string")
    cleaned = cleaned.str.replace("$", "", regex=False)
    cleaned = cleaned.str.replace(",", "", regex=False)
    cleaned = cleaned.str.replace(" ", "", regex=False)
    cleaned = cleaned.str.replace(r"[^0-9.\-]", "", regex=True)
    cleaned = cleaned.replace({value: pd.NA for value in EMPTY_TEXT_VALUES})
    return pd.to_numeric(cleaned, errors="coerce")


def clean_logistics_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean headers, normalize business names and cast base data types."""
    clean_df = df.copy()
    clean_df.columns = [_normalize_header(column) for column in clean_df.columns]
    clean_df = clean_df.rename(columns=COLUMN_MAPPING)
    clean_df = clean_df.dropna(how="all").reset_index(drop=True)

    for column in TEXT_COLUMNS:
        if column in clean_df.columns:
            clean_df[column] = clean_df[column].astype("string").str.strip()
            clean_df[column] = clean_df[column].replace({value: pd.NA for value in EMPTY_TEXT_VALUES})

    for column in NUMERIC_COLUMNS:
        if column in clean_df.columns:
            clean_df[column] = _clean_numeric_series(clean_df[column])

    for column in INTEGER_COLUMNS:
        if column in clean_df.columns:
            clean_df[column] = _clean_numeric_series(clean_df[column]).round().astype("Int64")

    for column in DATE_COLUMNS:
        if column in clean_df.columns:
            clean_df[column] = pd.to_datetime(clean_df[column], errors="coerce", dayfirst=True)

    logging.info("Columnas limpias y estandarizadas")
    return clean_df
