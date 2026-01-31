"""
Geometry cleaning utilities for vector data (Stage C).

This module performs geometry-level cleaning operations using Shapely.
It ensures that vector datasets contain valid, non-duplicated geometries
before spatial operations such as clipping or spatial joins are applied.
"""

import geopandas as gpd


# ---------------------------------------------------------------------
# Geometry validation and fixing
# ---------------------------------------------------------------------

def fix_invalid_geometries(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Detect and fix invalid geometries using a Shapely buffer-based approach.

    Invalid geometries are repaired by applying a zero-width buffer,
    which resolves common issues such as self-intersections.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        Input GeoDataFrame.

    Returns
    -------
    geopandas.GeoDataFrame
        GeoDataFrame with corrected geometries.
    """
    gdf = gdf.copy()
    gdf["geometry"] = gdf.geometry.buffer(0)
    return gdf


def count_invalid_geometries(gdf: gpd.GeoDataFrame) -> int:
    """
    Count invalid geometries in a GeoDataFrame.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame

    Returns
    -------
    int
        Number of invalid geometries.
    """
    return (~gdf.is_valid).sum()


# ---------------------------------------------------------------------
# Duplicate handling
# ---------------------------------------------------------------------

def drop_duplicate_geometries(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Remove duplicated geometries from a GeoDataFrame.

    Duplicate detection is based on the WKT (well-known text) representation of geometries,
    which is derived from Shapely geometry objects.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame

    Returns
    -------
    geopandas.GeoDataFrame
        GeoDataFrame with duplicate geometries removed.
    """
    gdf = gdf.copy()
    gdf["_geom_wkt"] = gdf.geometry.apply(lambda geom: geom.wkt)
    gdf = gdf.drop_duplicates(subset="_geom_wkt")
    gdf = gdf.drop(columns="_geom_wkt")
    return gdf