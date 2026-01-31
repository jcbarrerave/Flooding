"""
ndwi_datacube.py

Build an NDWI time data cube (time × y × x) using xarray from multiple analytical
NDWI GeoTIFFs, ensuring grid alignment, and compute simple temporal summaries.

This module is designed for filenames like:
    2023-09-10-00_00_2023-09-10-23_59_Sentinel-2_L2A_NDWI.tiff

Key outputs
-----------
1) cube_stats.yaml
   - inputs: list of files used
   - reference_grid: CRS/transform/width/height
   - threshold: NDWI threshold used for flooded_ratio
   - stats: per-date global mean/min/max and flooded_ratio_ndwi_gt_thr
2) ndwi_time_mean.tif
   - pixel-wise mean NDWI across time
3) ndwi_change_last_minus_first.tif
   - pixel-wise NDWI change (last date minus first date)

Usage
-----
Option A (recommended): use a small config dict in code:
    python ndwi_datacube.py

Option B: integrate into your pipeline by importing `run_datacube(...)`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple
import re

import numpy as np
import xarray as xr
import yaml

from utils_rasterio import read_tif, write_tif, same_grid, resample_to_match

# Extract the first "YYYY-MM-DD" in filename
_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def extract_date_str(filename: str) -> str:
    """
    Extract a date string (YYYY-MM-DD) from a filename.

    Parameters
    ----------
    filename : str
        Input filename.

    Returns
    -------
    str
        Date string in YYYY-MM-DD format.

    Raises
    ------
    ValueError
        If no date pattern is found.
    """
    m = _DATE_RE.search(filename)
    if not m:
        raise ValueError(f"Cannot find YYYY-MM-DD in filename: {filename}")
    return m.group(1)


def list_ndwi_files(ndwi_dir: Path) -> List[Path]:
    """
    List NDWI GeoTIFF files in a directory and sort them by extracted date.

    Parameters
    ----------
    ndwi_dir : Path
        Directory containing NDWI GeoTIFFs.

    Returns
    -------
    List[Path]
        Sorted list of NDWI files.

    Notes
    -----
    - Files with extension .tif or .tiff are included.
    - Sidecar files (e.g., .aux.xml) are automatically excluded by the glob.
    """
    files = list(ndwi_dir.glob("*.tif")) + list(ndwi_dir.glob("*.tiff"))
    if not files:
        raise FileNotFoundError(f"No .tif/.tiff files found in: {ndwi_dir}")
    return sorted(files, key=lambda p: extract_date_str(p.name))


def nodata_to_nan(arr: np.ndarray, nodata: float | int | None) -> np.ndarray:
    """
    Convert nodata pixels to NaN for robust statistics.

    Parameters
    ----------
    arr : np.ndarray
        Input array.
    nodata : float | int | None
        Nodata value (if present).

    Returns
    -------
    np.ndarray
        Float32 array with nodata replaced by NaN.
    """
    out = arr.astype(np.float32, copy=False)
    if nodata is None:
        return out
    return np.where(out == np.float32(nodata), np.nan, out)


def build_time_cube(
    files: List[Path],
    *,
    resampling_continuous: str = "bilinear",
) -> Tuple[xr.DataArray, dict, List[str]]:
    """
    Read multiple NDWI rasters, align them to a common grid, and stack into an xarray cube.

    Parameters
    ----------
    files : List[Path]
        NDWI GeoTIFF paths (multiple dates).
    resampling_continuous : str, optional
        Resampling method for continuous rasters (default: "bilinear").

    Returns
    -------
    Tuple[xr.DataArray, dict, List[str]]
        (xarray DataArray with dims (time,y,x), reference profile, list of date strings)
    """
    # Use the first raster as the reference grid
    ref_arr, ref_prof = read_tif(files[0])
    ref_nodata = ref_prof.get("nodata", None)

    dates: List[str] = []
    stack: List[np.ndarray] = []

    for i, fp in enumerate(files):
        date_str = extract_date_str(fp.name)
        arr, prof = read_tif(fp)

        # Align current raster to reference grid if needed
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
                    method=resampling_continuous,
                    out_dtype=np.float32,
                )

        dates.append(date_str)
        stack.append(aligned.astype(np.float32, copy=False))

    data = np.stack(stack, axis=0)  # (time, y, x)

    # Build x/y coordinates from the reference affine transform
    tr = ref_prof["transform"]
    height = ref_prof["height"]
    width = ref_prof["width"]

    # Pixel center coordinates
    x = tr.c + tr.a * (np.arange(width) + 0.5)
    y = tr.f + tr.e * (np.arange(height) + 0.5)  # tr.e is usually negative

    da = xr.DataArray(
        data,
        dims=("time", "y", "x"),
        coords={"time": dates, "y": y, "x": x},
        name="NDWI",
        attrs={"crs": str(ref_prof.get("crs", "")), "nodata": ref_nodata},
    )
    return da, ref_prof, dates


def run_datacube(
    ndwi_time_dir: str | Path,
    output_dir: str | Path = "data/output",
    *,
    threshold: float = 0.1,
    resampling_continuous: str = "bilinear",
    out_nodata: float = -9999.0,
) -> Dict[str, Any]:
    """
    Run the NDWI datacube workflow end-to-end and write outputs.

    Parameters
    ----------
    ndwi_time_dir : str | Path
        Directory containing analytical NDWI GeoTIFFs (single-band float).
    output_dir : str | Path, optional
        Output directory for cube artifacts (default: "data/output").
    threshold : float, optional
        NDWI threshold used to compute flooded_ratio (default: 0.1).
    resampling_continuous : str, optional
        Resampling method for alignment (default: "bilinear").
    out_nodata : float, optional
        Nodata value used in output GeoTIFFs (default: -9999.0).

    Returns
    -------
    Dict[str, Any]
        A result dictionary matching the structure you can embed in reports/logs.
    """
    ndwi_dir = Path(ndwi_time_dir)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    files = list_ndwi_files(ndwi_dir)
    da, ref_prof, dates = build_time_cube(files, resampling_continuous=resampling_continuous)

    ref_nodata = ref_prof.get("nodata", None)
    thr = float(threshold)

    # Per-date global statistics (aggregate over y,x)
    stats: Dict[str, Any] = {}
    for t in dates:
        arr_t = da.sel(time=t).values  # (y,x)
        valid = nodata_to_nan(arr_t, ref_nodata)

        flooded_ratio = float(np.nanmean((valid > thr).astype(np.float32)))
        stats[t] = {
            "mean": float(np.nanmean(valid)),
            "min": float(np.nanmin(valid)),
            "max": float(np.nanmax(valid)),
            "flooded_ratio_ndwi_gt_thr": flooded_ratio,
        }

    # Pixel-wise temporal summaries
    change = (da.isel(time=-1) - da.isel(time=0)).values.astype(np.float32)
    mean_img = da.mean(dim="time", skipna=True).values.astype(np.float32)

    # Write GeoTIFF outputs (use a consistent nodata value)
    change_path = out_dir / "ndwi_change_last_minus_first.tif"
    mean_path = out_dir / "ndwi_time_mean.tif"

    write_tif(change_path, change, ref_prof, dtype="float32", nodata=out_nodata)
    write_tif(mean_path, mean_img, ref_prof, dtype="float32", nodata=out_nodata)

    # Write YAML summary
    stats_path = out_dir / "cube_stats.yaml"
    result: Dict[str, Any] = {
        "cube_stats": str(stats_path),
        "inputs": [str(p) for p in files],
        "reference_grid": {
            "crs": str(ref_prof.get("crs", "")),
            "transform": [float(v) for v in ref_prof["transform"]][:6],
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


def main() -> None:
    """
    CLI entry point.

    Edit paths here if your project uses different folders.
    """
    res = run_datacube(
        ndwi_time_dir="raster_data/ndwi_time",
        output_dir="data/output",
        threshold=0.1,
        resampling_continuous="bilinear",
    )
    print("[Datacube] cube_stats:", res["cube_stats"])
    print("[Datacube] outputs:", res["outputs"])

def run(cfg: dict):
    paths = cfg.get("paths", {})
    ndwi_dir = paths.get("ndwi_time_dir", "raster_data/ndwi_time")
    out_dir = paths.get("output_dir", "data/output")

    cube_cfg = cfg.get("cube", {})
    thr = float(cube_cfg.get("threshold", 0.1))

    return run_datacube(
        ndwi_time_dir=ndwi_dir,
        output_dir=out_dir,
        threshold=thr,
    )


if __name__ == "__main__":
    main()