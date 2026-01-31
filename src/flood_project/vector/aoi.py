"""
AOI utilities for vector processing (Stage C).

This module extracts a vector Area of Interest (AOI) from a raster
by converting the raster spatial extent (bounding box) into a
polygon geometry.
"""

from pathlib import Path
import geopandas as gpd
import rasterio
from shapely.geometry import box


def aoi_from_raster(raster_path: Path) -> gpd.GeoDataFrame:
    """
    Create a vector AOI from the spatial extent of a raster.

    Parameters
    ----------
    raster_path : pathlib.Path
        Path to the raster file.

    Returns
    -------
    geopandas.GeoDataFrame
        GeoDataFrame containing a single polygon representing
        the raster extent.
    """
    with rasterio.open(raster_path) as src:
        bounds = src.bounds
        crs = src.crs

    if crs is None:
        raise ValueError(
            f"Raster '{raster_path}' has no CRS defined. "
            "A valid CRS is required to derive the AOI."
        )

    aoi_geom = box(bounds.left, bounds.bottom, bounds.right, bounds.top)

    return gpd.GeoDataFrame(
        {"geometry": [aoi_geom]},
        crs=crs
    )