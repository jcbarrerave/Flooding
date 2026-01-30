"""
Vector I/O utilities for the vector processing stage (Stage C).

This module handles reading and writing of vector datasets using
GeoPandas (Fiona backend). It isolates file system access from
processing logic to improve modularity and reproducibility.
"""

import geopandas as gpd

from flood_project.config.paths import (
    BUILDINGS_RAW,
    ADMIN_GPKG,
    ADMIN_LAYER,
)


# ---------------------------------------------------------------------
# Reading functions
# ---------------------------------------------------------------------

def read_buildings():
    """
    Read raw building footprint data.

    Returns
    -------
    geopandas.GeoDataFrame
        GeoDataFrame containing building geometries and attributes.
    """
    return gpd.read_file(BUILDINGS_RAW)


def read_admin_units():
    """
    Read administrative boundary data (ADM level 3) from GADM geopackage.

    Returns
    -------
    geopandas.GeoDataFrame
        GeoDataFrame containing administrative boundaries at ADM level 3.
    """
    return gpd.read_file(ADMIN_GPKG, layer=ADMIN_LAYER)


# ---------------------------------------------------------------------
# Writing functions
# ---------------------------------------------------------------------

def write_vector(gdf, output_path):
    """
    Write a GeoDataFrame to disk.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        GeoDataFrame to be written.
    output_path : pathlib.Path or str
        Destination file path.
    """
    gdf.to_file(output_path, driver="GPKG")