"""
Vector processing pipeline (Stage C).

This script orchestrates the complete vector processing workflow:
- reads vector inputs,
- derives a raster-based AOI,
- cleans geometries,
- ensures CRS consistency,
- clips datasets to the AOI,
- assigns administrative unit identifiers to buildings,
- writes final outputs,
- generates a quality control (QC) report.

Execution
---------
Run this module from the project root using:

    poetry run python -m flood_project.vector.run_c
    or using conda
    python src/flood_project/vector/run_c.py

Inputs
------
- Building footprints (vector)
- Administrative boundaries (ADM level 3)
- Raster flood mask used to define the AOI

Outputs
-------
- outputs/vector/buildings_admin.gpkg
- outputs/vector/admin_units_adm3.gpkg
- outputs/reports/qc_vector_prep.txt
"""
import sys
from pathlib import Path

# Add project root /src to PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from flood_project.config.paths import (
    BUILDINGS_ADMIN,
    ADMIN_OUT,
    QC_VECTOR,
    AOI_RASTER,
    RASTER_OUT_DIR,
    VECTOR_OUT_DIR,
    REPORTS_DIR,
)

from flood_project.vector.io import (
    read_buildings,
    read_admin_units,
    write_vector,
)

from flood_project.vector.cleaning import (
    count_invalid_geometries,
    fix_invalid_geometries,
    drop_duplicate_geometries,
)

from flood_project.vector.spatial import (
    ensure_same_crs,
    clip_to_aoi,
    assign_admin_id,
)

from flood_project.vector.aoi import aoi_from_raster


def main():
    """Run the complete vector processing pipeline (Stage C)."""

    # -----------------------------------------------------------------
    # Prepare output directories
    # -----------------------------------------------------------------
    RASTER_OUT_DIR.mkdir(parents=True, exist_ok=True)
    VECTOR_OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------------------
    # Read inputs
    # -----------------------------------------------------------------
    buildings = read_buildings()
    admin_units = read_admin_units()

    # -----------------------------------------------------------------
    # Extract AOI from raster
    # -----------------------------------------------------------------
    TARGET_CRS = "EPSG:32634"
    aoi = aoi_from_raster(AOI_RASTER)
    
    # Reproject AOI to project CRS (UTM 34N)
    aoi = aoi.to_crs(TARGET_CRS)

    # -----------------------------------------------------------------
    # Geometry cleaning
    # -----------------------------------------------------------------
    invalid_before = count_invalid_geometries(buildings)

    buildings = fix_invalid_geometries(buildings)
    buildings = drop_duplicate_geometries(buildings)

    invalid_after = count_invalid_geometries(buildings)

    # -----------------------------------------------------------------
    # CRS consistency
    # -----------------------------------------------------------------
    buildings = ensure_same_crs(buildings, TARGET_CRS)
    admin_units = ensure_same_crs(admin_units, TARGET_CRS)

    # -----------------------------------------------------------------
    # Clip to raster-derived AOI
    # -----------------------------------------------------------------
    buildings = clip_to_aoi(buildings, aoi)
    admin_units = clip_to_aoi(admin_units, aoi)

    # -----------------------------------------------------------------
    # Spatial join: assign admin_id to buildings
    # -----------------------------------------------------------------
    buildings = assign_admin_id(buildings, admin_units)

    # -----------------------------------------------------------------
    # Write outputs
    # -----------------------------------------------------------------
    write_vector(buildings, BUILDINGS_ADMIN)
    write_vector(admin_units, ADMIN_OUT)

    # -----------------------------------------------------------------
    # Quality control report
    # -----------------------------------------------------------------
    with open(QC_VECTOR, "w") as report:
        report.write("Vector Processing QC Report (Stage C)\n")
        report.write("-----------------------------------\n\n")
        report.write(f"Input buildings: {len(buildings)}\n")
        report.write(f"Administrative units: {len(admin_units)}\n\n")
        report.write(f"Invalid geometries before cleaning: {invalid_before}\n")
        report.write(f"Invalid geometries after cleaning: {invalid_after}\n\n")
        report.write(f"CRS used: {TARGET_CRS}\n")
        report.write(
            f"Buildings without admin_id: "
            f"{buildings['admin_id'].isna().sum()}\n"
        )


if __name__ == "__main__":

    main()

