"""
Tests for geometry cleaning utilities.

These tests ensure that geometry validation functions can be applied
to real vector data without errors. The tests do not assume the presence
of invalid geometries; they only verify that the functions run correctly
and return consistent results.
"""

from flood_project.vector.io import read_buildings
from flood_project.vector.cleaning import (
    count_invalid_geometries,
    fix_invalid_geometries,
)


def test_count_invalid_geometries_runs():
    """
    Test that invalid geometry counting runs and returns a non-negative integer.
    """
    buildings = read_buildings().head(1000)
    invalid = count_invalid_geometries(buildings)

    import numbers
    assert isinstance(invalid, numbers.Integral)
    assert invalid >= 0


def test_fix_invalid_geometries_preserves_feature_count():
    """
    Test that fixing geometries does not remove features.

    Geometry fixing should correct invalid shapes but preserve
    the number of features.
    """
    buildings = read_buildings().head(1000)
    fixed = fix_invalid_geometries(buildings)

    assert len(fixed) == len(buildings)