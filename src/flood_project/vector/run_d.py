"""
Raster-vector integration and aggregation pipeline (Stage D).

This script performs the complete Stage D workflow:
- reads processed building footprints (Stage C),
- samples a binary flood mask raster at building centroid locations,
- classifies buildings as flooded or not flooded,
- aggregates flood impact by administrative unit,
- writes per-building and per-admin outputs.

Execution
---------
Run this module from the project root using:

    poetry run python -m flood_project.vector.run_d
"""

import sys
from pathlib import Path

import rasterio
import geopandas as gpd
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------
# Add project root /src to PYTHONPATH
# ---------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from flood_project.config.paths import (
    OUTPUTS_DIR,
    BUILDINGS_ADMIN,
    ADMIN_OUT,
    AOI_RASTER,
)

from flood_project.vector.io import write_vector
from flood_project.vector.flood_sampling import (
    sample_raster_at_centroids,
    classify_flooded,
)
from flood_project.vector.aggregation import aggregate_by_admin


def main():
    """Run the complete raster-vector integration workflow (Stage D)."""

    # -----------------------------------------------------------------
    # Prepare output directories
    # -----------------------------------------------------------------
    vector_out_dir = OUTPUTS_DIR / "vector"
    vector_out_dir.mkdir(parents=True, exist_ok=True)

    buildings_flooded_path = vector_out_dir / "buildings_flooded.gpkg"
    admin_summary_gpkg = vector_out_dir / "admin_flood_summary.gpkg"
    admin_summary_csv = vector_out_dir / "admin_flood_summary.csv"

    # -----------------------------------------------------------------
    # Read inputs from Stage C
    # -----------------------------------------------------------------
    buildings = gpd.read_file(BUILDINGS_ADMIN)
    admin_units = gpd.read_file(ADMIN_OUT)

    # -----------------------------------------------------------------
    # Open raster and extract data mask
    # -----------------------------------------------------------------
    with rasterio.open(AOI_RASTER) as src:
        raster_crs = src.crs
        raster_data = src.read(1)
        transform = src.transform
        nodata = src.nodata

    # -----------------------------------------------------------------
    # Reproject vectors to raster CRS
    # -----------------------------------------------------------------
    if buildings.crs != raster_crs:
        buildings = buildings.to_crs(raster_crs)

    if admin_units.crs != raster_crs:
        admin_units = admin_units.to_crs(raster_crs)

    # -----------------------------------------------------------------
    # Filter buildings: centroid must fall on EXISTING raster pixel
    # -----------------------------------------------------------------
    def centroid_on_valid_pixel(geom):
        x, y = geom.centroid.x, geom.centroid.y
        col, row = ~transform * (x, y)
        row, col = int(row), int(col)

        # Outside raster grid
        if row < 0 or col < 0:
            return False
        if row >= raster_data.shape[0] or col >= raster_data.shape[1]:
            return False

        value = raster_data[row, col]

        # Pixel exists (not outside raster)
        if nodata is not None:
            return value != nodata
        return True

    buildings = buildings[
        buildings.geometry.apply(centroid_on_valid_pixel)
    ].copy()

    # -----------------------------------------------------------------
    # Ensure consistent admin_id field
    # -----------------------------------------------------------------
    admin_units = admin_units.rename(columns={"GID_3": "admin_id"})

    # -----------------------------------------------------------------
    # Raster–vector integration: centroid sampling
    # -----------------------------------------------------------------
    buildings = sample_raster_at_centroids(
        buildings=buildings,
        raster_path=AOI_RASTER,
        value_field="flood_value",
    )

    buildings = classify_flooded(
        buildings=buildings,
        value_field="flood_value",
        flooded_field="flooded",
        threshold=0.5,
    )

    # -----------------------------------------------------------------
    # Write per-building output
    # -----------------------------------------------------------------
    write_vector(buildings, buildings_flooded_path)

    # -----------------------------------------------------------------
    # Aggregate flood impact by administrative unit
    # -----------------------------------------------------------------
    admin_summary = aggregate_by_admin(
        buildings=buildings,
        admin_units=admin_units,
        admin_id_field="admin_id",
    )

    write_vector(admin_summary, admin_summary_gpkg)

    admin_summary.drop(columns="geometry").to_csv(
        admin_summary_csv,
        index=False,
    )


if __name__ == "__main__":
    main()
