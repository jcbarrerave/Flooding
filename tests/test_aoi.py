"""
Tests for AOI extraction from raster data.

These tests verify that a vector Area of Interest (AOI) can be
correctly derived from the spatial extent of a raster file.
The tests focus on data types, geometry validity, and CRS presence,
not on the scientific correctness of the raster itself.
"""

import geopandas as gpd
from flood_project.vector.aoi import aoi_from_raster
from flood_project.config.paths import AOI_RASTER


def test_aoi_from_raster_returns_valid_geodataframe():
    """
    Test that aoi_from_raster returns a valid GeoDataFrame.

    The AOI should:
    - be a GeoDataFrame
    - contain exactly one geometry
    - have a defined CRS
    - contain a polygon geometry representing the raster extent
    """
    aoi = aoi_from_raster(AOI_RASTER)

    assert isinstance(aoi, gpd.GeoDataFrame)
    assert len(aoi) == 1
    assert aoi.crs is not None
    assert aoi.geometry.iloc[0].geom_type == "Polygon"