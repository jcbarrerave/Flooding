"""
Pytest checks for the raster part of the flood-exposure pipeline (Module A + B).

These tests are intentionally lightweight:
- Smoke test: the pipeline runs and produces expected output files.
- Sanity test: the filtered mask has the expected value domain and nodata handling.

Run:
    pytest -q
or (with Poetry):
    poetry run pytest -q
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import rasterio
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import raster_prep
import flood_mask


def load_cfg() -> dict:
    """
    Load the project configuration from config.yaml.

    Returns
    -------
    dict
        Configuration dictionary used by the pipeline.
    """
    return yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))


def test_pipeline_outputs_exist() -> None:
    """
    Smoke test: run Module A + B and verify that output GeoTIFFs are created.
    """
    cfg = load_cfg()
    a_res = raster_prep.run(cfg)
    b_res = flood_mask.run(cfg, a_res)

    assert Path(b_res["ndwi"]).exists()
    assert Path(b_res["flood_mask_raw"]).exists()
    assert Path(b_res["flood_mask_filtered"]).exists()


def test_mask_values_and_nodata() -> None:
    """
    Sanity test: verify mask nodata value and that pixel values are within {0, 1, 255}.
    """
    cfg = load_cfg()
    a_res = raster_prep.run(cfg)
    b_res = flood_mask.run(cfg, a_res)

    mask_path = Path(b_res["flood_mask_filtered"])
    with rasterio.open(mask_path) as ds:
        m = ds.read(1)
        nodata = ds.nodata

    # Nodata should be 255 (invalid pixels)
    assert nodata == 255

    # Mask values should be binary (0/1) plus nodata (255)
    uniques = set(np.unique(m).tolist())
    assert uniques.issubset({0, 1, 255})

    # Ensure there are sufficient valid pixels (loose bound)
    assert float((m != 255).mean()) > 0.5