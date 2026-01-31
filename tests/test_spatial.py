"""
Tests for spatial operations.

These tests validate that spatial functions such as CRS harmonization
and administrative unit assignment operate correctly on vector data.
"""

from flood_project.vector.io import read_buildings, read_admin_units
from flood_project.vector.spatial import (
    ensure_same_crs,
    assign_admin_id,
)


def test_ensure_same_crs_applies_target_crs():
    """
    Test that ensure_same_crs reprojects a GeoDataFrame when needed.
    """
    buildings = read_buildings().head(500)
    admin = read_admin_units()

    reprojected = ensure_same_crs(buildings, admin.crs)

    assert reprojected.crs == admin.crs


def test_assign_admin_id_creates_column():
    """
    Test that a spatial join assigns an administrative ID column
    to the buildings GeoDataFrame.
    """
    buildings = read_buildings().head(500)
    admin = read_admin_units()

    buildings = ensure_same_crs(buildings, admin.crs)
    joined = assign_admin_id(buildings, admin)

    assert "admin_id" in joined.columns