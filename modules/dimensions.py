import pandas as pd

from config import (
    AREA_DIM_NAME,
    DATE_DIM_NAME,
    ID_COLUMNS,
    MATERIAL_DIM_NAME,
    STATUS_DIM_NAME,
    SUPPLIER_DIM_NAME,
)


def _build_simple_dimension(
    df: pd.DataFrame,
    source_columns: list[str],
    id_column: str,
) -> pd.DataFrame:
    dim_df = (
        df[source_columns]
        .drop_duplicates()
        .dropna(how="all")
        .reset_index(drop=True)
        .copy()
    )
    dim_df.insert(0, id_column, range(1, len(dim_df) + 1))
    return dim_df


def build_date_dimension(fact_df: pd.DataFrame) -> pd.DataFrame:
    date_frames = []

    for source_column in ["fecha_oc", "fecha_recepcion", "fecha_prog_entrega"]:
        if source_column not in fact_df.columns:
            continue

        current = fact_df[[source_column]].dropna().copy()
        if current.empty:
            continue

        current = current.rename(columns={source_column: "fecha"})
        date_frames.append(current)

    if not date_frames:
        return pd.DataFrame(
            columns=[
                "id_fecha",
                "fecha",
                "anio",
                "mes",
                "nombre_mes",
                "trimestre",
                "semana_iso",
                "dia",
                "dia_semana",
            ]
        )

    dim_fecha = pd.concat(date_frames, ignore_index=True).drop_duplicates().sort_values("fecha")
    dim_fecha["anio"] = dim_fecha["fecha"].dt.year
    dim_fecha["mes"] = dim_fecha["fecha"].dt.month
    dim_fecha["nombre_mes"] = dim_fecha["fecha"].dt.strftime("%B")
    dim_fecha["trimestre"] = dim_fecha["fecha"].dt.quarter
    dim_fecha["semana_iso"] = dim_fecha["fecha"].dt.isocalendar().week.astype("Int64")
    dim_fecha["dia"] = dim_fecha["fecha"].dt.day
    dim_fecha["dia_semana"] = dim_fecha["fecha"].dt.strftime("%A")
    dim_fecha.insert(0, "id_fecha", range(1, len(dim_fecha) + 1))
    return dim_fecha.reset_index(drop=True)


def build_dimensions(fact_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    dim_area = _build_simple_dimension(
        fact_df,
        ["area_solicitante"],
        ID_COLUMNS["area"],
    )
    dim_proveedor = _build_simple_dimension(
        fact_df,
        ["proveedor"],
        ID_COLUMNS["proveedor"],
    )
    dim_material = _build_simple_dimension(
        fact_df,
        ["cod_material", "material", "unidad_medida"],
        ID_COLUMNS["material"],
    )
    dim_estado = _build_simple_dimension(
        fact_df,
        ["estado_recepcion"],
        ID_COLUMNS["estado"],
    )
    dim_fecha = build_date_dimension(fact_df)

    return {
        DATE_DIM_NAME: dim_fecha,
        AREA_DIM_NAME: dim_area,
        SUPPLIER_DIM_NAME: dim_proveedor,
        MATERIAL_DIM_NAME: dim_material,
        STATUS_DIM_NAME: dim_estado,
    }
