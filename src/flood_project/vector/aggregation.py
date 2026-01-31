"""
Aggregation utilities for flood impact assessment (Stage D).

This module aggregates per-building flood classifications by
administrative unit, producing summary statistics suitable
for mapping and reporting.
"""

import geopandas as gpd


def aggregate_by_admin(
    buildings: gpd.GeoDataFrame,
    admin_units: gpd.GeoDataFrame,
    admin_id_field: str = "admin_id",
) -> gpd.GeoDataFrame:
    """
    Aggregate flooded buildings by administrative unit.

    For each administrative unit, the total number of buildings,
    the number of flooded buildings, and the flooded ratio are
    computed and attached to the administrative geometries.

    Parameters
    ----------
    buildings : geopandas.GeoDataFrame
        Buildings with a binary flood indicator (0/1) and an
        administrative identifier.
    admin_units : geopandas.GeoDataFrame
        Administrative unit polygons with an identifier field
        and geometry.
    admin_id_field : str, default "admin_id"
        Name of the administrative unit identifier field.

    Returns
    -------
    geopandas.GeoDataFrame
        Administrative units with the following added attributes:
        - total_buildings
        - flooded_buildings
        - flooded_ratio
    """

    # -----------------------------------------------------------------
    # Aggregate building statistics by administrative unit
    # -----------------------------------------------------------------
    stats = (
        buildings
        .groupby(admin_id_field)
        .agg(
            total_buildings=("flooded", "count"),
            flooded_buildings=("flooded", "sum"),
        )
        .reset_index()
    )

    # -----------------------------------------------------------------
    # Calculate flooded ratio
    # -----------------------------------------------------------------
    stats["flooded_ratio"] = (
        stats["flooded_buildings"] / stats["total_buildings"]
    )

    # -----------------------------------------------------------------
    # Join statistics back to administrative geometries
    # -----------------------------------------------------------------
    admin = admin_units.merge(
        stats,
        on=admin_id_field,
        how="left",
    )

    # -----------------------------------------------------------------
    # Handle administrative units without buildings
    # -----------------------------------------------------------------
    admin[["total_buildings", "flooded_buildings", "flooded_ratio"]] = (
        admin[["total_buildings", "flooded_buildings", "flooded_ratio"]]
        .fillna(0)
    )

    return admin