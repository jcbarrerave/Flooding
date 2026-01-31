"""
ndwi_series.py

Build an analytical NDWI time series (single-band float GeoTIFFs) from
Sentinel-2 L2A band rasters stored in a directory (bands_time).

This module is designed for filenames like:
  2023-09-10-00_00_2023-09-10-23_59_Sentinel-2_L2A_B03_(Raw).tiff
  2023-09-10-00_00_2023-09-10-23_59_Sentinel-2_L2A_B08_(Raw).tiff

It pairs B03 and B08 per date, aligns B08 to the B03 grid if needed,
computes NDWI = (B03 - B08) / (B03 + B08), and writes Float32 NDWI rasters
to ndwi_time directory for xarray datacube stacking.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Any

import numpy as np

from utils_rasterio import read_tif, resample_to_match, same_grid, write_tif
from flood_mask import compute_ndwi

DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


@dataclass
class BandPair:
    """A pair of band file paths for a single date."""
    b03: Path
    b08: Path


def _extract_date(name: str) -> str:
    """Extract YYYY-MM-DD from filename."""
    m = DATE_RE.search(name)
    if not m:
        raise ValueError(f"Cannot parse date from filename: {name}")
    return m.group(1)


def _detect_band(name: str) -> str | None:
    """Return 'B03' or 'B08' if present in filename; otherwise None."""
    u = name.upper()
    if "B03" in u:
        return "B03"
    if "B08" in u:
        return "B08"
    return None


def _collect_pairs(bands_dir: Path) -> Dict[str, BandPair]:
    """
    Scan bands_dir and collect complete (B03, B08) pairs per date.
    """
    tmp: Dict[str, Dict[str, Path]] = {}

    for fp in sorted(list(bands_dir.glob("*.tif")) + list(bands_dir.glob("*.tiff"))):
        if fp.name.endswith(".aux.xml"):
            continue

        band = _detect_band(fp.name)
        if band is None:
            continue

        date = _extract_date(fp.name)
        tmp.setdefault(date, {})[band] = fp

    pairs: Dict[str, BandPair] = {}
    for date, d in tmp.items():
        if "B03" in d and "B08" in d:
            pairs[date] = BandPair(b03=d["B03"], b08=d["B08"])

    return pairs


def run(cfg: dict) -> Dict[str, Any]:
    """
    Entry point used by the global pipeline.

    Parameters
    ----------
    cfg : dict
        Parsed config.yaml. Expected keys:
          cfg["paths"]["bands_time_dir"]
          cfg["paths"]["ndwi_time_dir"]
        Optional:
          cfg["ndwi"]["scale"] (default 10000.0)
          cfg["ndwi"]["nodata"] (default -9999.0)

    Returns
    -------
    Dict[str, Any]
        Summary dictionary (inputs, outputs, number_of_dates).
    """
    paths = cfg.get("paths", {})
    bands_dir = Path(paths.get("bands_time_dir", "raster_data/bands_time"))
    out_dir = Path(paths.get("ndwi_time_dir", "raster_data/ndwi_time"))
    out_dir.mkdir(parents=True, exist_ok=True)

    ndwi_cfg = cfg.get("ndwi", {})
    scale = float(ndwi_cfg.get("scale", 10000.0))
    out_nodata = float(ndwi_cfg.get("nodata", -9999.0))

    pairs = _collect_pairs(bands_dir)
    if not pairs:
        raise FileNotFoundError(
            f"No complete B03/B08 pairs found in {bands_dir}. "
            "Check that filenames contain a date (YYYY-MM-DD) and band tokens B03/B08."
        )

    outputs: List[str] = []
    for date in sorted(pairs.keys()):
        bp = pairs[date]

        # Read B03/B08
        b03, prof03 = read_tif(bp.b03)
        b08, prof08 = read_tif(bp.b08)

        # Align B08 to B03 grid
        if same_grid(prof03, prof08):
            b08_aligned = b08
            out_prof = prof03
        else:
            b08_aligned = resample_to_match(
                src_arr=b08,
                src_profile=prof08,
                dst_profile=prof03,
                method="bilinear",
                out_dtype=np.float32,
            )
            out_prof = prof03

        # Compute analytical NDWI (float)
        ndwi = compute_ndwi(b03, b08_aligned, scale=scale).astype(np.float32)

        # Basic validity mask (Sentinel-2 reflectance should be > 0)
        valid = (b03 > 0) & (b08_aligned > 0)
        ndwi_out = ndwi.copy()
        ndwi_out[~valid] = np.float32(out_nodata)

        # Write output NDWI with your preferred naming style
        out_fp = out_dir / f"{date}-00_00_{date}-23_59_Sentinel-2_L2A_NDWI.tiff"
        write_tif(out_fp, ndwi_out, out_prof, dtype="float32", nodata=out_nodata)

        outputs.append(str(out_fp))
        print(f"[NDWI-Series] {date}: wrote {out_fp.name}")

    return {
        "inputs_dir": str(bands_dir),
        "output_dir": str(out_dir),
        "num_dates": len(outputs),
        "outputs": outputs,
        "scale": scale,
        "nodata": out_nodata,
    }