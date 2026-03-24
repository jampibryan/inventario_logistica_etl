import logging
import re
from pathlib import Path

import pandas as pd

from config import SOURCE_FILE, SOURCE_ROW_COLUMN, SOURCE_SHEET, TRAILING_DATA_ANCHOR_COLUMNS


FIRST_DATA_ROW_IN_EXCEL = 4
EMPTY_TEXT_VALUES = {"", "NAN", "NONE", "<NA>"}


def _normalize_header_token(value: object) -> str:
    if value is None:
        return ""

    text = str(value).replace("\n", " ").strip().upper()
    text = re.sub(r"\s+", " ", text)
    if text.startswith("UNNAMED"):
        return ""
    return text


def _normalize_cell_value(value: object) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None

    text = str(value).strip().upper()
    text = re.sub(r"\s+", " ", text)
    if text in EMPTY_TEXT_VALUES:
        return None
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


def _trim_trailing_blank_rows(df: pd.DataFrame) -> pd.DataFrame:
    available_anchor_columns = [column for column in TRAILING_DATA_ANCHOR_COLUMNS if column in df.columns]
    if not available_anchor_columns:
        logging.warning("No se encontraron columnas ancla para recortar filas vacias al final")
        return df

    normalized_anchor_df = df[available_anchor_columns].apply(lambda column: column.map(_normalize_cell_value))
    anchor_presence = normalized_anchor_df.notna().any(axis=1)

    if not anchor_presence.any():
        logging.warning("No se detectaron registros utiles usando las columnas ancla; se conserva la hoja completa")
        return df

    last_valid_position = anchor_presence[anchor_presence].index.max()
    trimmed_rows = len(df) - (last_valid_position + 1)
    trimmed_df = df.iloc[: last_valid_position + 1].copy()

    if trimmed_rows > 0:
        last_excel_row = int(trimmed_df.iloc[-1][SOURCE_ROW_COLUMN])
        logging.info(
            "Se recortaron %s filas vacias al final de la hoja. Ultima fila util detectada: %s",
            trimmed_rows,
            last_excel_row,
        )

    return trimmed_df


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
    df.insert(0, SOURCE_ROW_COLUMN, range(FIRST_DATA_ROW_IN_EXCEL, FIRST_DATA_ROW_IN_EXCEL + len(df)))
    df = _trim_trailing_blank_rows(df)
    df = df.dropna(how="all", subset=[column for column in df.columns if column != SOURCE_ROW_COLUMN]).reset_index(drop=True)
    logging.info("Filas leidas: %s | Columnas utiles leidas: %s", len(df), len(df.columns))
    return SOURCE_FILE, df
