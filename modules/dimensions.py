import pandas as pd

from config import (
    AREA_DIM_NAME,
    DATE_DIM_NAME,
    DATE_KEY_COLUMNS,
    ID_COLUMNS,
    MATERIAL_DIM_NAME,
    PAYMENT_DIM_NAME,
    STATUS_DIM_NAME,
    SUPPLIER_DIM_NAME,
)


DATE_SOURCE_COLUMNS = [
    "fecha_oc",
    "fecha_recepcion",
    "fecha_programada_entrega",
]

MONTH_NAMES_ES = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}

DAY_NAMES_ES = {
    0: "Lunes",
    1: "Martes",
    2: "Miércoles",
    3: "Jueves",
    4: "Viernes",
    5: "Sábado",
    6: "Domingo",
}

KEY_COLUMNS = [
    ID_COLUMNS["material"],
    ID_COLUMNS["area"],
    ID_COLUMNS["proveedor"],
    ID_COLUMNS["estado"],
    ID_COLUMNS["forma_pago"],
    *DATE_KEY_COLUMNS.values(),
]


def _cast_nullable_integer_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    result_df = df.copy()
    for column in columns:
        if column in result_df.columns:
            result_df[column] = result_df[column].astype("Int64")
    return result_df


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
    return _cast_nullable_integer_columns(dim_df, [id_column])


def build_date_dimension(fact_df: pd.DataFrame) -> pd.DataFrame:
    date_frames = []

    for source_column in DATE_SOURCE_COLUMNS:
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
                "anio_mes",
                "anio_mes_orden",
                "anio_mes_nombre",
                "semana_mes",
                "semana_mes_nombre",
                "semana_mes_orden",
                "trimestre",
                "semana_iso",
                "dia",
                "dia_semana",
            ]
        )

    dim_fecha = pd.concat(date_frames, ignore_index=True).drop_duplicates().sort_values("fecha")
    dim_fecha["anio"] = dim_fecha["fecha"].dt.year.astype("Int64")
    dim_fecha["mes"] = dim_fecha["fecha"].dt.month.astype("Int64")
    dim_fecha["nombre_mes"] = dim_fecha["mes"].map(MONTH_NAMES_ES).astype("string")
    dim_fecha["anio_mes"] = dim_fecha["fecha"].dt.strftime("%Y-%m").astype("string")
    dim_fecha["anio_mes_orden"] = (dim_fecha["anio"] * 100 + dim_fecha["mes"]).astype("Int64")
    dim_fecha["anio_mes_nombre"] = (dim_fecha["nombre_mes"] + " " + dim_fecha["anio"].astype("string")).astype("string")
    dim_fecha["dia"] = dim_fecha["fecha"].dt.day.astype("Int64")
    dim_fecha["semana_mes"] = (((dim_fecha["dia"] - 1) // 7) + 1).clip(upper=4).astype("Int64")
    dim_fecha["semana_mes_nombre"] = ("Semana " + dim_fecha["semana_mes"].astype("string")).astype("string")
    dim_fecha["semana_mes_orden"] = dim_fecha["semana_mes"].astype("Int64")
    dim_fecha["trimestre"] = dim_fecha["fecha"].dt.quarter.astype("Int64")
    dim_fecha["semana_iso"] = dim_fecha["fecha"].dt.isocalendar().week.astype("Int64")
    dim_fecha["dia_semana"] = dim_fecha["fecha"].dt.dayofweek.map(DAY_NAMES_ES).astype("string")
    dim_fecha.insert(0, "id_fecha", range(1, len(dim_fecha) + 1))
    return _cast_nullable_integer_columns(
        dim_fecha.reset_index(drop=True),
        ["id_fecha", "anio", "mes", "anio_mes_orden", "semana_mes", "semana_mes_orden", "trimestre", "semana_iso", "dia"],
    )


def _assign_simple_key(
    fact_df: pd.DataFrame,
    dim_df: pd.DataFrame,
    natural_columns: list[str],
    id_column: str,
) -> pd.DataFrame:
    if dim_df.empty:
        fact_df[id_column] = pd.Series(pd.NA, index=fact_df.index, dtype="Int64")
        return fact_df

    merge_columns = natural_columns + [id_column]
    merged_df = fact_df.merge(dim_df[merge_columns], on=natural_columns, how="left")
    return _cast_nullable_integer_columns(merged_df, [id_column])


def _assign_date_keys(fact_df: pd.DataFrame, dim_fecha: pd.DataFrame) -> pd.DataFrame:
    if dim_fecha.empty:
        for id_column in DATE_KEY_COLUMNS.values():
            fact_df[id_column] = pd.Series(pd.NA, index=fact_df.index, dtype="Int64")
        return fact_df

    result_df = fact_df.copy()
    date_lookup = dim_fecha[["id_fecha", "fecha"]].copy()

    for source_column, id_column in DATE_KEY_COLUMNS.items():
        current_lookup = date_lookup.rename(columns={"fecha": source_column, "id_fecha": id_column})
        result_df = result_df.merge(current_lookup, on=source_column, how="left")
        result_df = _cast_nullable_integer_columns(result_df, [id_column])

    return result_df


def build_dimensions(fact_df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    dim_area = _build_simple_dimension(
        fact_df,
        ["solicitante"],
        ID_COLUMNS["area"],
    )
    dim_proveedor = _build_simple_dimension(
        fact_df,
        ["proveedor"],
        ID_COLUMNS["proveedor"],
    )
    dim_material = _build_simple_dimension(
        fact_df,
        ["codigo", "material", "unidad_medida"],
        ID_COLUMNS["material"],
    )
    dim_estado = _build_simple_dimension(
        fact_df,
        ["estado_recepcion"],
        ID_COLUMNS["estado"],
    )
    dim_forma_pago = _build_simple_dimension(
        fact_df,
        ["forma_pago"],
        ID_COLUMNS["forma_pago"],
    )
    dim_fecha = build_date_dimension(fact_df)

    enriched_fact = fact_df.drop(columns=[column for column in KEY_COLUMNS if column in fact_df.columns]).copy()
    enriched_fact = _assign_simple_key(enriched_fact, dim_material, ["codigo", "material", "unidad_medida"], ID_COLUMNS["material"])
    enriched_fact = _assign_simple_key(enriched_fact, dim_area, ["solicitante"], ID_COLUMNS["area"])
    enriched_fact = _assign_simple_key(enriched_fact, dim_proveedor, ["proveedor"], ID_COLUMNS["proveedor"])
    enriched_fact = _assign_simple_key(enriched_fact, dim_estado, ["estado_recepcion"], ID_COLUMNS["estado"])
    enriched_fact = _assign_simple_key(enriched_fact, dim_forma_pago, ["forma_pago"], ID_COLUMNS["forma_pago"])
    enriched_fact = _assign_date_keys(enriched_fact, dim_fecha)
    enriched_fact = _cast_nullable_integer_columns(enriched_fact, [ID_COLUMNS["fact"], *KEY_COLUMNS])

    dimensions = {
        DATE_DIM_NAME: _cast_nullable_integer_columns(dim_fecha, ["id_fecha", "anio", "mes", "trimestre", "semana_iso", "dia"]),
        AREA_DIM_NAME: _cast_nullable_integer_columns(dim_area, [ID_COLUMNS["area"]]),
        SUPPLIER_DIM_NAME: _cast_nullable_integer_columns(dim_proveedor, [ID_COLUMNS["proveedor"]]),
        MATERIAL_DIM_NAME: _cast_nullable_integer_columns(dim_material, [ID_COLUMNS["material"]]),
        STATUS_DIM_NAME: _cast_nullable_integer_columns(dim_estado, [ID_COLUMNS["estado"]]),
        PAYMENT_DIM_NAME: _cast_nullable_integer_columns(dim_forma_pago, [ID_COLUMNS["forma_pago"]]),
    }
    return enriched_fact, dimensions


