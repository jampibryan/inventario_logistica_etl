import logging
import re

import pandas as pd

from config import (
    COLUMN_MAPPING,
    DATE_COLUMNS,
    INTEGER_COLUMNS,
    MAX_VALID_YEAR,
    MIN_VALID_YEAR,
    NUMERIC_COLUMNS,
    TEXT_COLUMNS,
)


EMPTY_TEXT_VALUES = {"", "NAN", "NONE", "<NA>"}
TYPE_ERROR_FLAG_COLUMN = "_fila_tipo_invalido"
TYPE_ERROR_DETAIL_COLUMN = "_detalle_tipos_invalidos"


def _normalize_header(value: str) -> str:
    text = str(value).strip().upper()
    text = re.sub(r"\s+", " ", text)
    return text


def _normalize_raw_series(series: pd.Series) -> pd.Series:
    normalized = series.astype("string").str.strip()
    return normalized.replace({value: pd.NA for value in EMPTY_TEXT_VALUES})


def _clean_numeric_series(series: pd.Series) -> pd.Series:
    cleaned = series.astype("string")
    cleaned = cleaned.str.replace("$", "", regex=False)
    cleaned = cleaned.str.replace(",", "", regex=False)
    cleaned = cleaned.str.replace(" ", "", regex=False)
    cleaned = cleaned.str.replace(r"[^0-9.\-]", "", regex=True)
    cleaned = cleaned.replace({value: pd.NA for value in EMPTY_TEXT_VALUES})
    return pd.to_numeric(cleaned, errors="coerce")


def _clean_numeric_column(series: pd.Series) -> tuple[pd.Series, pd.Series]:
    raw_values = _normalize_raw_series(series)
    cleaned = _clean_numeric_series(series)
    invalid_mask = raw_values.notna() & cleaned.isna()
    return cleaned, invalid_mask


def _clean_integer_column(series: pd.Series) -> tuple[pd.Series, pd.Series]:
    raw_values = _normalize_raw_series(series)
    cleaned = _clean_numeric_series(series)
    non_integer_mask = cleaned.notna() & cleaned.mod(1).ne(0)
    invalid_mask = raw_values.notna() & (cleaned.isna() | non_integer_mask)
    cleaned = cleaned.mask(non_integer_mask)
    return cleaned.astype("Int64"), invalid_mask


def _clean_date_column(series: pd.Series) -> tuple[pd.Series, pd.Series]:
    raw_values = _normalize_raw_series(series)
    parsed = pd.to_datetime(series, errors="coerce", dayfirst=True)
    out_of_range_mask = parsed.notna() & ((parsed.dt.year < MIN_VALID_YEAR) | (parsed.dt.year > MAX_VALID_YEAR))
    invalid_mask = raw_values.notna() & (parsed.isna() | out_of_range_mask)

    invalid_count = int(out_of_range_mask.sum())
    if invalid_count:
        logging.warning(
            "Se anularon %s fechas fuera del rango valido %s-%s",
            invalid_count,
            MIN_VALID_YEAR,
            MAX_VALID_YEAR,
        )
        parsed.loc[out_of_range_mask] = pd.NaT

    return parsed, invalid_mask


def _build_invalid_type_columns(clean_df: pd.DataFrame, invalid_masks: dict[str, pd.Series]) -> pd.DataFrame:
    if not invalid_masks:
        clean_df[TYPE_ERROR_FLAG_COLUMN] = False
        clean_df[TYPE_ERROR_DETAIL_COLUMN] = pd.NA
        return clean_df

    invalid_matrix = pd.DataFrame(invalid_masks).fillna(False)
    clean_df[TYPE_ERROR_FLAG_COLUMN] = invalid_matrix.any(axis=1)
    clean_df[TYPE_ERROR_DETAIL_COLUMN] = invalid_matrix.apply(
        lambda row: "|".join([column for column, is_invalid in row.items() if bool(is_invalid)]),
        axis=1,
    ).astype("string")
    clean_df.loc[~clean_df[TYPE_ERROR_FLAG_COLUMN], TYPE_ERROR_DETAIL_COLUMN] = pd.NA

    invalid_rows = int(clean_df[TYPE_ERROR_FLAG_COLUMN].sum())
    if invalid_rows:
        logging.warning("Se detectaron %s filas con tipos de dato invalidos", invalid_rows)

    return clean_df


def clean_logistics_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean headers, normalize business names and cast base data types."""
    clean_df = df.copy()
    clean_df.columns = [_normalize_header(column) for column in clean_df.columns]
    clean_df = clean_df.rename(columns=COLUMN_MAPPING)
    clean_df = clean_df.dropna(how="all").reset_index(drop=True)

    for column in TEXT_COLUMNS:
        if column in clean_df.columns:
            clean_df[column] = _normalize_raw_series(clean_df[column])

    invalid_masks: dict[str, pd.Series] = {}

    for column in NUMERIC_COLUMNS:
        if column in clean_df.columns:
            clean_df[column], invalid_masks[column] = _clean_numeric_column(clean_df[column])

    for column in INTEGER_COLUMNS:
        if column in clean_df.columns:
            clean_df[column], invalid_masks[column] = _clean_integer_column(clean_df[column])

    for column in DATE_COLUMNS:
        if column in clean_df.columns:
            clean_df[column], invalid_masks[column] = _clean_date_column(clean_df[column])

    clean_df = _build_invalid_type_columns(clean_df, invalid_masks)
    logging.info("Columnas limpias y estandarizadas")
    return clean_df
