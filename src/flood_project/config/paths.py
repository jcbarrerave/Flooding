"""
Project path configuration.

This module defines filesystem paths used for vector data processing
(Stage C). It centralizes input and output locations to ensure
clarity, reproducibility, and separation of responsibilities between
vector and raster processing stages.

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
├── pyproject.toml
├── poetry.lock
└── src/
    └── flood_project/
        └── config/
            └── paths.py
"""

# ---------------------------------------------------------------------
# Data directories
# ---------------------------------------------------------------------

DATA_DIR = BASE_DIR / "data"
"""Root directory for all project data."""

VECTORS_DIR = DATA_DIR / "greece_extra"
"""Directory containing auxiliary vector datasets (buildings, roads, land use)."""

# Note: raster data are stored in data/rasters and handled separately
# by the raster processing stages (A and B).

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
# Vector outputs (Stage C)
# ---------------------------------------------------------------------

OUTPUTS_DIR = BASE_DIR / "outputs"
"""Directory where processed vector outputs are stored."""

BUILDINGS_ADMIN = OUTPUTS_DIR / "buildings_admin.gpkg"
"""Processed buildings with assigned administrative unit ID."""

ADMIN_OUT = OUTPUTS_DIR / "admin_units_adm3.gpkg"
"""Processed administrative boundaries (ADM level 3)."""

# ---------------------------------------------------------------------
# Quality control
# ---------------------------------------------------------------------

REPORTS_DIR = BASE_DIR / "reports"
"""Directory for quality control reports."""

QC_VECTOR = REPORTS_DIR / "qc_vector_prep.txt"
"""Quality control report for vector preparation stage."""