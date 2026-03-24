import logging
from pathlib import Path

import pandas as pd
from openpyxl.styles import numbers

from config import (
    AUDIT_EXCEL_NAME,
    CONTROL_FILE,
    DATE_COLUMNS,
    DW_DIR,
    OVERWRITE_OUTPUTS,
    PROCESSED_AUDIT_DIR,
    PROCESSED_EXCEL_DIR,
    REVIEW_COLUMN_ORDER,
    REVIEW_EXCEL_NAME,
    VISUAL_COLUMN_NAMES,
)


OUTPUT_DATE_COLUMNS = set(DATE_COLUMNS + ["fecha"])
EXCEL_DATE_FORMAT = "dd/mm/yyyy"


def _clear_directory_files(directory: Path, patterns: list[str]) -> None:
    if not OVERWRITE_OUTPUTS or not directory.exists():
        return

    for pattern in patterns:
        for file_path in directory.glob(pattern):
            if not file_path.is_file():
                continue

            try:
                file_path.unlink()
            except PermissionError:
                logging.warning("No se pudo eliminar %s porque esta abierto en otro proceso", file_path.name)


def reset_runtime_artifacts(clear_control: bool = False) -> None:
    """Remove generated outputs before a force run."""
    _clear_directory_files(PROCESSED_EXCEL_DIR, ["*.xlsx"])
    _clear_directory_files(PROCESSED_AUDIT_DIR, ["*.xlsx"])
    _clear_directory_files(DW_DIR, ["*.parquet", "*.csv"])

    if clear_control and CONTROL_FILE.exists():
        try:
            CONTROL_FILE.unlink()
        except PermissionError:
            logging.warning("No se pudo eliminar %s porque esta abierto en otro proceso", CONTROL_FILE.name)


def _convert_date_columns_for_output(df: pd.DataFrame) -> pd.DataFrame:
    output_df = df.copy()
    candidate_columns = [column for column in OUTPUT_DATE_COLUMNS if column in output_df.columns]

    for column in candidate_columns:
        if pd.api.types.is_datetime64_any_dtype(output_df[column]):
            output_df[column] = output_df[column].dt.date

    return output_df


def _build_review_dataframe(clean_df: pd.DataFrame) -> pd.DataFrame:
    ordered_columns = [column for column in REVIEW_COLUMN_ORDER if column in clean_df.columns]
    remaining_columns = [column for column in clean_df.columns if column not in ordered_columns]
    review_df = clean_df[ordered_columns + remaining_columns].copy()
    review_df = _convert_date_columns_for_output(review_df)
    review_df = review_df.rename(columns=VISUAL_COLUMN_NAMES)
    return review_df


def _apply_excel_date_format(worksheet, headers: list[str]) -> None:
    visual_date_headers = {
        VISUAL_COLUMN_NAMES[column]
        for column in DATE_COLUMNS
        if column in VISUAL_COLUMN_NAMES
    }

    for column_index, header in enumerate(headers, start=1):
        if header not in visual_date_headers:
            continue

        for row in worksheet.iter_rows(min_row=2, min_col=column_index, max_col=column_index):
            cell = row[0]
            if cell.value is not None:
                cell.number_format = EXCEL_DATE_FORMAT


def export_review_outputs(clean_df: pd.DataFrame, audit_df: pd.DataFrame, source_file) -> None:
    """Generate human-readable outputs for operational review."""
    PROCESSED_EXCEL_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    _clear_directory_files(PROCESSED_EXCEL_DIR, ["*.xlsx"])
    _clear_directory_files(PROCESSED_AUDIT_DIR, ["*.xlsx"])

    review_df = _build_review_dataframe(clean_df)
    clean_output_path = PROCESSED_EXCEL_DIR / REVIEW_EXCEL_NAME
    audit_output_path = PROCESSED_AUDIT_DIR / AUDIT_EXCEL_NAME

    try:
        with pd.ExcelWriter(clean_output_path, engine="openpyxl") as writer:
            review_df.to_excel(writer, index=False, sheet_name="datos")
            worksheet = writer.sheets["datos"]
            _apply_excel_date_format(worksheet, list(review_df.columns))
        logging.info("Excel limpio generado: %s", clean_output_path.name)
    except PermissionError:
        logging.warning("No se pudo escribir %s porque esta abierto en otro proceso", clean_output_path.name)

    try:
        with pd.ExcelWriter(audit_output_path, engine="openpyxl") as writer:
            audit_df.to_excel(writer, sheet_name="resumen", index=False)
        logging.info("Auditoria generada: %s", audit_output_path.name)
    except PermissionError:
        logging.warning("No se pudo escribir %s porque esta abierto en otro proceso", audit_output_path.name)


def export_tables(
    tables: dict[str, pd.DataFrame],
    export_csv: bool = False,
    export_parquet: bool = True,
) -> None:
    """Export analytical tables to the DW layer."""
    DW_DIR.mkdir(parents=True, exist_ok=True)
    _clear_directory_files(DW_DIR, ["*.parquet", "*.csv"])

    for table_name, df in tables.items():
        output_df = _convert_date_columns_for_output(df)

        if export_parquet:
            parquet_path = DW_DIR / f"{table_name}.parquet"
            output_df.to_parquet(parquet_path, index=False)
            logging.info("Parquet generado: %s", parquet_path.name)

        if export_csv:
            csv_path = DW_DIR / f"{table_name}.csv"
            output_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
            logging.info("CSV generado: %s", csv_path.name)


def update_control_file(source_file, status: str, rows_read: int, rows_fact: int, message: str) -> None:
    """Append one execution record to the process control file."""
    CONTROL_FILE.parent.mkdir(parents=True, exist_ok=True)

    control_row = pd.DataFrame(
        [
            {
                "fecha_ejecucion": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                "archivo_fuente": source_file.name,
                "estado": status,
                "filas_leidas": rows_read,
                "filas_fact": rows_fact,
                "mensaje": message,
            }
        ]
    )

    if CONTROL_FILE.exists():
        previous = pd.read_csv(CONTROL_FILE)
        control_row = pd.concat([previous, control_row], ignore_index=True)

    control_row.to_csv(CONTROL_FILE, index=False, encoding="utf-8-sig")
