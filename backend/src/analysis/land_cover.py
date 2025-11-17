"""Land cover analysis utilities."""

from __future__ import annotations

from typing import List, Dict

import geopandas as gpd


CLASS_FIELDS = [
    "code_18",
    "Code_18",
    "CODE_18",
    "clc_code",
    "CLC_CODE",
    "CLC18",
    "CLC2018",
    "legend",
    "LABEL3",
]


def summarize_land_cover(gdf: gpd.GeoDataFrame) -> List[Dict]:
    if gdf.empty:
        return []

    class_field = next((field for field in CLASS_FIELDS if field in gdf.columns), None)
    if not class_field:
        raise ValueError("Unable to identify CORINE class column.")

    data = gdf.copy()
    data["area_ha"] = data.geometry.area / 10_000

    summary_df = (
        data.groupby(class_field)
        .agg(total_area_ha=("area_ha", "sum"))
        .reset_index()
        .sort_values("total_area_ha", ascending=False)
    )

    summary_df = summary_df.rename(columns={class_field: "class_code"})
    return summary_df.to_dict(orient="records")

