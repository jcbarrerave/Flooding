"""
Raster I/O and grid alignment utilities (rasterio-based).

This module provides small helper functions for:
- reading/writing single-band GeoTIFF rasters,
- checking whether two rasters share the same grid,
- resampling/reprojecting a raster to match a reference grid.

These utilities are used by Module A (raster preparation) and Module B (flood masking).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling


def read_tif(path: str | Path) -> tuple[np.ndarray, dict[str, Any]]:
    """
    Read a single-band GeoTIFF into a NumPy array and return its rasterio profile.

    Parameters
    ----------
    path:
        Path to the GeoTIFF file.

    Returns
    -------
    (array, profile):
        array is a 2D NumPy array (H, W) for band 1.
        profile is a rasterio profile dictionary (CRS, transform, dtype, nodata, etc.).
    """
    path = str(path)
    with rasterio.open(path) as ds:
        arr = ds.read(1)
        profile = ds.profile.copy()
    return arr, profile


def write_tif(
    path: str | Path,
    arr: np.ndarray,
    ref_profile: dict[str, Any],
    dtype: str | None = None,
    nodata: Any | None = None,
) -> None:
    """
    Write a single-band GeoTIFF using a reference profile as the grid contract.

    This function uses ref_profile (CRS/transform/width/height) to ensure the output
    matches a reference grid. Use dtype/nodata to override profile values if needed.

    Parameters
    ----------
    path:
        Output file path.
    arr:
        2D array (H, W) to write.
    ref_profile:
        Reference rasterio profile that defines the target grid.
    dtype:
        Optional dtype override (e.g., "float32", "uint8").
    nodata:
        Optional nodata override (e.g., 255 for masks, -9999.0 for float rasters).

    Raises
    ------
    ValueError
        If arr shape does not match (height, width) defined in ref_profile.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    h = int(ref_profile["height"])
    w = int(ref_profile["width"])
    if arr.shape != (h, w):
        raise ValueError(f"Array shape {arr.shape} does not match reference grid {(h, w)}")

    profile = ref_profile.copy()
    profile.update(count=1)

    if dtype is not None:
        profile.update(dtype=dtype)
    if nodata is not None:
        profile.update(nodata=nodata)

    with rasterio.open(path, "w", **profile) as dst:
        dst.write(arr.astype(profile["dtype"]), 1)


def same_grid(p1: dict[str, Any], p2: dict[str, Any]) -> bool:
    """
    Check whether two rasterio profiles share the exact same grid.

    The grid is considered identical if CRS, affine transform, width, and height
    are exactly equal.

    Parameters
    ----------
    p1, p2:
        Rasterio profile dictionaries.

    Returns
    -------
    bool
        True if the grids match exactly; otherwise False.
    """
    return (
        p1.get("crs") == p2.get("crs")
        and p1.get("transform") == p2.get("transform")
        and p1.get("width") == p2.get("width")
        and p1.get("height") == p2.get("height")
    )


def _resampling(method: str) -> Resampling:
    """
    Map a string name to a rasterio Resampling enum.

    Parameters
    ----------
    method:
        Resampling method name (e.g., "bilinear", "nearest").

    Returns
    -------
    rasterio.warp.Resampling
        Corresponding resampling enum.

    Raises
    ------
    ValueError
        If method is not supported.
    """
    method = method.lower().strip()
    if method == "bilinear":
        return Resampling.bilinear
    if method in ("nearest", "near"):
        return Resampling.nearest
    raise ValueError(f"Unsupported resampling method: {method}")


def resample_to_match(
    src_arr: np.ndarray,
    src_profile: dict[str, Any],
    dst_profile: dict[str, Any],
    method: str = "bilinear",
    out_dtype: Any = np.float32,
) -> np.ndarray:
    """
    Reproject/resample a source raster to match a destination grid exactly.

    The destination grid is defined by dst_profile["crs"], dst_profile["transform"],
    dst_profile["width"], and dst_profile["height"].

    Parameters
    ----------
    src_arr:
        Source raster array (2D).
    src_profile:
        Rasterio profile of the source array.
    dst_profile:
        Rasterio profile defining the target grid.
    method:
        Resampling method: "bilinear" (continuous rasters) or "nearest" (masks/classes).
    out_dtype:
        Output NumPy dtype.

    Returns
    -------
    np.ndarray
        Reprojected/resampled array with shape (dst_height, dst_width).
    """
    dst = np.empty((dst_profile["height"], dst_profile["width"]), dtype=out_dtype)

    reproject(
        source=src_arr,
        destination=dst,
        src_transform=src_profile["transform"],
        src_crs=src_profile["crs"],
        dst_transform=dst_profile["transform"],
        dst_crs=dst_profile["crs"],
        resampling=_resampling(method),
    )
    return dst