"""
Tests for AOI-based spatial clipping.

These tests ensure that vector datasets can be clipped to a
raster-derived AOI and that clipping does not increase the
number of features.
"""

from flood_project.vector.io import read_buildings
from flood_project.vector.aoi import aoi_from_raster
from flood_project.vector.spatial import clip_to_aoi
from flood_project.config.paths import AOI_RASTER


def test_clip_to_aoi_reduces_or_preserves_feature_count():
    """
    Test that clipping to the AOI does not increase the number
    of vector features.
    """
    buildings = read_buildings().head(1000)
    aoi = aoi_from_raster(AOI_RASTER)

    clipped = clip_to_aoi(buildings, aoi)

    assert len(clipped) <= len(buildings)