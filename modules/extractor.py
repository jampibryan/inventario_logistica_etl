import logging
import re
from pathlib import Path

import pandas as pd

from config import SOURCE_FILE, SOURCE_SHEET


def _normalize_header_token(value: object) -> str:
    if value is None:
        return ""

    text = str(value).replace("\n", " ").strip().upper()
    text = re.sub(r"\s+", " ", text)
    if text.startswith("UNNAMED"):
        return ""
    return text


def _flatten_excel_headers(columns: pd.Index) -> list[str]:
    flattened = []

    for column in columns:
        if isinstance(column, tuple):
            level_0 = _normalize_header_token(column[0])
            level_1 = _normalize_header_token(column[1])
            flattened.append(level_1 or level_0)
            continue

        flattened.append(_normalize_header_token(column))

    return flattened


def _collapse_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    collapsed_df = pd.DataFrame(index=df.index)
    processed_bases: set[str] = set()

    for column in df.columns:
        base_column = re.sub(r"\.\d+$", "", column)
        if base_column in processed_bases:
            continue

        matching_positions = [
            index
            for index, current_column in enumerate(df.columns)
            if re.sub(r"\.\d+$", "", current_column) == base_column
        ]
        subset = df.iloc[:, matching_positions]
        if subset.shape[1] == 1:
            collapsed_df[base_column] = subset.iloc[:, 0]
        else:
            combined = subset.iloc[:, 0].copy()
            for column_index in range(1, subset.shape[1]):
                combined = combined.combine_first(subset.iloc[:, column_index])
            collapsed_df[base_column] = combined

        processed_bases.add(base_column)

    return collapsed_df


def extract_budget_sheet() -> tuple[Path, pd.DataFrame]:
    """Read the source Excel using the two-row business header."""
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(f"No se encontro el archivo fuente esperado: {SOURCE_FILE.name}")

    logging.info("Leyendo archivo fuente: %s", SOURCE_FILE.name)
    df = pd.read_excel(
        SOURCE_FILE,
        sheet_name=SOURCE_SHEET,
        header=[1, 2],
        dtype=object,
        engine="openpyxl",
    )
    df.columns = _flatten_excel_headers(df.columns)
    df = df.loc[:, [column for column in df.columns if column]].copy()
    df = _collapse_duplicate_columns(df)
    df = df.dropna(how="all").reset_index(drop=True)
    logging.info("Filas leidas: %s | Columnas utiles leidas: %s", len(df), len(df.columns))
    return SOURCE_FILE, df
