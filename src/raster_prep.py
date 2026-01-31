"""
Module A: Raster preparation for Sentinel-2 flood analysis.

This module reads Sentinel-2 L2A bands (B03 and B08), checks whether the rasters
share the same grid (CRS/transform/shape), and aligns B08 to the B03 reference
grid if needed. It writes preprocessed GeoTIFFs and a small YAML artifact that
records output paths and reference grid metadata for downstream steps.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import numpy as np
import yaml

from utils_rasterio import read_tif, write_tif, same_grid, resample_to_match


def run(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare Sentinel-2 bands for downstream NDWI computation.

    The function:
    1) Reads B03 and B08 GeoTIFFs.
    2) Prints basic metadata (CRS, resolution, shape, dtype).
    3) If grids differ, resamples/reprojects B08 to match the B03 grid.
    4) Writes preprocessed rasters to disk.
    5) Returns a dictionary with output paths and reference grid metadata.

    Parameters
    ----------
    cfg:
        Configuration dictionary loaded from a YAML file.
        Expected keys:
        - cfg["paths"]["b03"], cfg["paths"]["b08"], cfg["paths"]["out_dir"]
        - cfg["processing"]["resampling_continuous"] (optional)

    Returns
    -------
    dict
        A dictionary containing:
        - "b03_preprocessed": path to preprocessed B03 GeoTIFF
        - "b08_preprocessed": path to preprocessed B08 GeoTIFF
        - "grid_ref": reference grid metadata (CRS, transform, shape, resolution)
    """
    paths = cfg["paths"]
    out_dir = Path(paths["out_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    b03_path = paths["b03"]
    b08_path = paths["b08"]

    res_cont = cfg["processing"].get("resampling_continuous", "bilinear")

    b03, prof03 = read_tif(b03_path)
    b08, prof08 = read_tif(b08_path)

    print(
        "[A] B03:",
        prof03["crs"],
        "res:",
        (prof03["transform"].a, -prof03["transform"].e),
        "shape:",
        (prof03["height"], prof03["width"]),
        "dtype:",
        b03.dtype,
    )
    print(
        "[A] B08:",
        prof08["crs"],
        "res:",
        (prof08["transform"].a, -prof08["transform"].e),
        "shape:",
        (prof08["height"], prof08["width"]),
        "dtype:",
        b08.dtype,
    )

    if same_grid(prof03, prof08):
        b08_aligned = b08
        print("[A] B08 already aligned. No resampling needed.")
    else:
        b08_aligned = resample_to_match(
            b08, prof08, prof03, method=res_cont, out_dtype=np.float32
        )
        print("[A] B08 resampled to match B03 grid.")

    # Fixed output filenames for downstream modules.
    b03_out = out_dir / "B03_preprocessed.tif"
    b08_out = out_dir / "B08_preprocessed.tif"

    # Write B03 using its original dtype.
    write_tif(b03_out, b03, prof03, dtype=str(b03.dtype))

    # If B08 was resampled, write as float32; otherwise keep original dtype.
    if isinstance(b08_aligned, np.ndarray) and b08_aligned.dtype == np.float32:
        write_tif(b08_out, b08_aligned, prof03, dtype="float32")
    else:
        write_tif(b08_out, b08_aligned, prof03, dtype=str(b08.dtype))

    result = {
        "b03_preprocessed": str(b03_out),
        "b08_preprocessed": str(b08_out),
        "grid_ref": {
            "crs": str(prof03["crs"]),
            "transform": [float(x) for x in prof03["transform"]][:6],
            "width": int(prof03["width"]),
            "height": int(prof03["height"]),
            "res": (
                float(prof03["transform"].a),
                float(-prof03["transform"].e),
            ),
        },
    }
    return result


def main(config_path: str = "config.yaml") -> None:
    """
    Run Module A from a YAML configuration file and write an artifact YAML.

    Parameters
    ----------
    config_path:
        Path to the YAML configuration file.
    """
    cfg = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    res = run(cfg)

    out_dir = Path(cfg["paths"]["out_dir"])
    (out_dir / "a_raster_prep_result.yaml").write_text(
        yaml.safe_dump(res, sort_keys=False), encoding="utf-8"
    )
    print("[A] Done. Results saved to:", out_dir)


if __name__ == "__main__":
    main()