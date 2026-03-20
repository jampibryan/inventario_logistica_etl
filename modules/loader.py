import logging
from pathlib import Path

import pandas as pd

from config import (
    AUDIT_EXCEL_NAME,
    CONTROL_FILE,
    DW_DIR,
    OVERWRITE_OUTPUTS,
    PROCESSED_AUDIT_DIR,
    PROCESSED_EXCEL_DIR,
    REVIEW_COLUMN_ORDER,
    REVIEW_EXCEL_NAME,
    VISUAL_COLUMN_NAMES,
)


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


def _build_review_dataframe(clean_df: pd.DataFrame) -> pd.DataFrame:
    ordered_columns = [column for column in REVIEW_COLUMN_ORDER if column in clean_df.columns]
    remaining_columns = [column for column in clean_df.columns if column not in ordered_columns]
    review_df = clean_df[ordered_columns + remaining_columns].copy()
    review_df = review_df.rename(columns=VISUAL_COLUMN_NAMES)
    return review_df


def export_review_outputs(clean_df: pd.DataFrame, audit_df: pd.DataFrame, source_file) -> None:
    """Generate human-readable outputs for operational review."""
    PROCESSED_EXCEL_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    _clear_directory_files(PROCESSED_EXCEL_DIR, ["*.xlsx"])
    _clear_directory_files(PROCESSED_AUDIT_DIR, ["*.xlsx"])

    review_df = _build_review_dataframe(clean_df)
    clean_output_path = PROCESSED_EXCEL_DIR / REVIEW_EXCEL_NAME
    audit_output_path = PROCESSED_AUDIT_DIR / AUDIT_EXCEL_NAME

    review_df.to_excel(clean_output_path, index=False)
    with pd.ExcelWriter(audit_output_path, engine="openpyxl") as writer:
        audit_df.to_excel(writer, sheet_name="resumen", index=False)

    logging.info("Excel limpio generado: %s", clean_output_path.name)
    logging.info("Auditoria generada: %s", audit_output_path.name)


def export_tables(
    tables: dict[str, pd.DataFrame],
    export_csv: bool = False,
    export_parquet: bool = True,
) -> None:
    """Export analytical tables to the DW layer."""
    DW_DIR.mkdir(parents=True, exist_ok=True)
    _clear_directory_files(DW_DIR, ["*.parquet", "*.csv"])

    for table_name, df in tables.items():
        if export_parquet:
            parquet_path = DW_DIR / f"{table_name}.parquet"
            df.to_parquet(parquet_path, index=False)
            logging.info("Parquet generado: %s", parquet_path.name)

        if export_csv:
            csv_path = DW_DIR / f"{table_name}.csv"
            df.to_csv(csv_path, index=False, encoding="utf-8-sig")
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
