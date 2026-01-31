"""
Module Cube: Xarray time data cube demo (time x y x).

This module builds an Xarray DataArray from multiple NDWI GeoTIFFs (3 dates),
ensures grid alignment (CRS/transform/shape), stacks them along a 'time' dimension,
and performs simple aggregations across dimensions.

Outputs
-------
- cube_stats.yaml: per-date global statistics (mean/min/max) and flooded_ratio
- ndwi_change_last_minus_first.tif: pixel-wise NDWI change (last - first)
- ndwi_time_mean.tif (optional): pixel-wise mean NDWI across time
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple
import re

import numpy as np
import xarray as xr
import yaml

from utils_rasterio import read_tif, write_tif, same_grid, resample_to_match


_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def _extract_date_str(filename: str) -> str:
    """Extract YYYY-MM-DD from a filename. Raises if not found."""
    m = _DATE_RE.search(filename)
    if not m:
        raise ValueError(f"Cannot find YYYY-MM-DD in filename: {filename}")
    return m.group(0)


def _list_ndwi_files(ndwi_dir: Path) -> List[Path]:
    """List NDWI GeoTIFFs in a folder and sort by date extracted from filename."""
    tifs = sorted(ndwi_dir.glob("*.tif*"))
    if not tifs:
        raise FileNotFoundError(f"No .tif/.tiff files found in: {ndwi_dir}")

    # Sort by date in filename (YYYY-MM-DD)
    tifs_sorted = sorted(tifs, key=lambda p: _extract_date_str(p.name))
    return tifs_sorted


def _mask_nodata(arr: np.ndarray, nodata: float | int | None) -> np.ndarray:
    """Return a float32 array with nodata masked as NaN (for stats)."""
    out = arr.astype(np.float32)
    if nodata is None:
        return out
    return np.where(out == np.float32(nodata), np.nan, out)


def run(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a time cube from 3 NDWI rasters and write summary outputs.

    Expected config keys
    --------------------
    cfg["paths"]["ndwi_time_dir"] : folder containing NDWI rasters for multiple dates
    cfg["paths"]["output_dir"]    : output folder (default: data/output)
    cfg["ndwi"]["threshold"]      : threshold used to compute flooded_ratio (default: 0.1)
    cfg["processing"]["resampling_continuous"] : resampling method (default: bilinear)

    Returns
    -------
    dict
        Paths + statistics for logging.
    """
    out_dir = Path(cfg.get("paths", {}).get("output_dir", "data/output"))
    out_dir.mkdir(parents=True, exist_ok=True)

    ndwi_dir = Path(cfg["paths"]["ndwi_time_dir"])
    files = _list_ndwi_files(ndwi_dir)

    thr = float(cfg.get("ndwi", {}).get("threshold", 0.1))
    res_cont = cfg.get("processing", {}).get("resampling_continuous", "bilinear")

    # Read first file as reference grid
    ref_arr, ref_prof = read_tif(files[0])
    ref_nodata = ref_prof.get("nodata", None)

    dates: List[str] = []
    stack: List[np.ndarray] = []

    for i, fp in enumerate(files):
        date_str = _extract_date_str(fp.name)
        arr, prof = read_tif(fp)

        if i == 0:
            aligned = arr
        else:
            if same_grid(ref_prof, prof):
                aligned = arr
            else:
                aligned = resample_to_match(
                    src_arr=arr,
                    src_profile=prof,
                    dst_profile=ref_prof,
                    method=res_cont,
                    out_dtype=np.float32,
                )

        dates.append(date_str)
        stack.append(aligned.astype(np.float32))

    data = np.stack(stack, axis=0)  # (time, y, x)

    # Build coordinates from the reference geotransform
    # transform: (a, b, c, d, e, f) where x = a*col + b*row + c ; y = d*col + e*row + f
    tr = ref_prof["transform"]
    height = ref_prof["height"]
    width = ref_prof["width"]

    x0 = tr.c
    y0 = tr.f
    dx = tr.a
    dy = tr.e  # typically negative

    x = x0 + dx * (np.arange(width) + 0.5)
    y = y0 + dy * (np.arange(height) + 0.5)

    da = xr.DataArray(
        data,
        dims=("time", "y", "x"),
        coords={"time": dates, "y": y, "x": x},
        name="NDWI",
        attrs={"crs": str(ref_prof.get("crs", "")), "nodata": ref_nodata},
    )

    # ---- Aggregation across dimensions ----
    # Per-time global stats (aggregate across y,x)
    stats: Dict[str, Any] = {}
    for t in dates:
        arr_t = da.sel(time=t).values  # (y,x)
        valid = _mask_nodata(arr_t, ref_nodata)

        flooded_ratio = float(np.nanmean((valid > thr).astype(np.float32)))
        stats[t] = {
            "mean": float(np.nanmean(valid)),
            "min": float(np.nanmin(valid)),
            "max": float(np.nanmax(valid)),
            "flooded_ratio_ndwi_gt_thr": flooded_ratio,
        }

    # Pixel-wise temporal aggregations
    change = (da.isel(time=-1) - da.isel(time=0)).values.astype(np.float32)
    mean_img = da.mean(dim="time", skipna=True).values.astype(np.float32)

    # Write rasters
    change_path = out_dir / "ndwi_change_last_minus_first.tif"
    mean_path = out_dir / "ndwi_time_mean.tif"

    write_tif(change_path, change, ref_prof, dtype="float32", nodata=-9999.0)
    write_tif(mean_path, mean_img, ref_prof, dtype="float32", nodata=-9999.0)

    # Write stats YAML
    stats_path = out_dir / "cube_stats.yaml"
    result = {
        "cube_stats": str(stats_path),
        "inputs": [str(p) for p in files],
        "reference_grid": {
            "crs": str(ref_prof.get("crs", "")),
            "transform": [float(x) for x in ref_prof["transform"]][:6],
            "width": int(ref_prof["width"]),
            "height": int(ref_prof["height"]),
        },
        "threshold": thr,
        "stats": stats,
        "outputs": {
            "ndwi_change_last_minus_first": str(change_path),
            "ndwi_time_mean": str(mean_path),
        },
    }
    stats_path.write_text(yaml.safe_dump(result, sort_keys=False), encoding="utf-8")
    return result


def main(config_path: str = "config.yaml") -> None:
    """CLI entry point for Module Cube."""
    cfg = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    res = run(cfg)
    print("[Cube] Done. Stats:", res["cube_stats"])
    print("[Cube] Outputs:", res["outputs"])


if __name__ == "__main__":
    main()