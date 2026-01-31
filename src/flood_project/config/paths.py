"""
Project path configuration.

This module defines filesystem paths used for vector data processing
(Stage C). It centralizes input and output locations to ensure
clarity, reproducibility, and clear separation between raster and
vector products across processing stages.

This module does NOT perform any data processing.
"""

from pathlib import Path

# ---------------------------------------------------------------------
# Project root directory
# ---------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[3]
"""
Absolute path to the project root directory.

Expected structure:
flood_project/
├── data/
├── outputs/
├── pyproject.toml
├── poetry.lock
└── src/
    └── flood_project/
        └── config/
            └── paths.py
"""

# ---------------------------------------------------------------------
# Data directories (inputs)
# ---------------------------------------------------------------------

DATA_DIR = BASE_DIR / "data"
"""Root directory for all input data."""

VECTORS_DIR = DATA_DIR / "greece_extra"
"""Directory containing auxiliary vector datasets (e.g. buildings)."""

# ---------------------------------------------------------------------
# Vector inputs (Stage C)
# ---------------------------------------------------------------------

BUILDINGS_RAW = VECTORS_DIR / "gis_osm_buildings_a_free_1.shp"
"""Raw building footprint dataset."""

ADMIN_GPKG = DATA_DIR / "gadm41_GRC.gpkg"
"""GADM Greece geopackage containing multiple administrative layers."""

ADMIN_LAYER = "ADM_ADM_3"
"""Administrative level used for aggregation (ADM level 3)."""

# ---------------------------------------------------------------------
# Output directories
# ---------------------------------------------------------------------

OUTPUTS_DIR = BASE_DIR / "outputs"
"""Root directory for all project outputs."""

RASTER_OUT_DIR = OUTPUTS_DIR / "raster"
"""Directory for raster outputs (Stages A/B)."""

VECTOR_OUT_DIR = OUTPUTS_DIR / "vector"
"""Directory for vector outputs (Stage C and later)."""

REPORTS_DIR = OUTPUTS_DIR / "reports"
"""Directory for quality control reports and summaries."""

# ---------------------------------------------------------------------
# Vector outputs (Stage C)
# ---------------------------------------------------------------------

BUILDINGS_ADMIN = VECTOR_OUT_DIR / "buildings_admin.gpkg"
"""Processed buildings with assigned administrative unit ID."""

ADMIN_OUT = VECTOR_OUT_DIR / "admin_units_adm3.gpkg"
"""Processed administrative boundaries (ADM level 3)."""

QC_VECTOR = REPORTS_DIR / "qc_vector_prep.txt"
"""Quality control report for vector preparation stage."""

# ---------------------------------------------------------------------
# Raster output used for AOI definition (Stages A/B → Stage C)
# ---------------------------------------------------------------------

AOI_RASTER = RASTER_OUT_DIR / "flood_mask_filtered.tif"
"""
Raster used to define the Area of Interest (AOI).

This raster is produced in stages A/B. In Stage C, only its spatial
extent and CRS are used to derive a vector AOI. No raster values
are processed here.
"""