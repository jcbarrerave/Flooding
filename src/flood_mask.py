"""
Module B: Flood masking from Sentinel-2 bands.

Steps:
1) Compute NDWI from B03 (green) and B08 (NIR) using NumPy.
2) Threshold NDWI to obtain a raw binary flood mask.
3) Denoise the mask using a tensor-based mean filter (PyTorch conv2d).

Outputs:
- ndwi.tif (float32)
- flood_mask_raw.tif (uint8; 0/1, nodata=255)
- flood_mask_filtered.tif (uint8; 0/1, nodata=255)
- b_flood_mask_result.yaml
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import yaml

from utils_rasterio import read_tif, write_tif

try:
    import torch
    import torch.nn.functional as F
except Exception:
    torch = None
    F = None


def compute_ndwi(b03: np.ndarray, b08: np.ndarray, scale: float = 10000.0) -> np.ndarray:
    """
    Compute NDWI: (G - NIR) / (G + NIR).

    Parameters
    ----------
    b03:
        Green band array (Sentinel-2 B03).
    b08:
        NIR band array (Sentinel-2 B08).
    scale:
        Scale factor for converting integer reflectance to float (typical: 10000).

    Returns
    -------
    np.ndarray
        NDWI as float32, typically in [-1, 1].
    """
    g = b03.astype(np.float32) / scale
    n = b08.astype(np.float32) / scale
    ndwi = (g - n) / (g + n + 1e-6)
    return ndwi.astype(np.float32)


def threshold_ndwi(ndwi: np.ndarray, thr: float = 0.1) -> np.ndarray:
    """
    Threshold NDWI into a binary flood mask.

    Parameters
    ----------
    ndwi:
        NDWI array (float).
    thr:
        Flood threshold. Pixels with NDWI > thr are labeled as flooded (1).

    Returns
    -------
    np.ndarray
        Binary mask (uint8) with values 0/1.
    """
    return (ndwi > thr).astype(np.uint8)


def tensor_denoise_mask(mask01: np.ndarray, kernel_size: int = 3, thr: float = 0.5) -> np.ndarray:
    """
    Denoise a binary mask (0/1) using a mean filter implemented with PyTorch conv2d.

    Parameters
    ----------
    mask01:
        Binary mask (uint8 or float) containing only 0/1 values.
    kernel_size:
        Mean filter size (odd integer recommended).
    thr:
        Threshold applied after smoothing (e.g., 0.5 behaves like majority vote).

    Returns
    -------
    np.ndarray
        Denoised binary mask (uint8) with values 0/1.

    Raises
    ------
    RuntimeError
        If PyTorch is not available.
    """
    if torch is None or F is None:
        raise RuntimeError("PyTorch is not available. Install torch to run tensor denoising.")

    x = torch.from_numpy(mask01.astype(np.float32))[None, None, :, :]  # (1,1,H,W)
    kernel = torch.ones((1, 1, kernel_size, kernel_size), dtype=torch.float32)
    kernel = kernel / float(kernel_size * kernel_size)

    y = F.conv2d(x, kernel, padding=kernel_size // 2)
    out = (y[0, 0].cpu().numpy() > thr).astype(np.uint8)
    return out


def run(cfg: Dict[str, Any], raster_prep_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run flood masking using Module A outputs (aligned B03/B08).

    Notes
    -----
    A validity mask is applied: pixels where B03<=0 or B08<=0 are treated as nodata (255).
    This handles common export padding/no-data edges from AOI downloads.

    Parameters
    ----------
    cfg:
        Configuration dictionary (YAML).
    raster_prep_result:
        Output from Module A containing "b03_preprocessed" and "b08_preprocessed".

    Returns
    -------
    dict
        Paths to outputs and parameters used.
    """
    out_dir = Path(cfg.get("paths", {}).get("output_dir", "data/output"))
    out_dir.mkdir(parents=True, exist_ok=True)

    b03_path = raster_prep_result["b03_preprocessed"]
    b08_path = raster_prep_result["b08_preprocessed"]

    b03, prof = read_tif(b03_path)
    b08, _ = read_tif(b08_path)

    # Parameters
    scale = float(cfg.get("ndwi", {}).get("scale", 10000.0))
    ndwi_thr = float(cfg.get("ndwi", {}).get("threshold", 0.1))
    k = int(cfg.get("tensor_denoise", {}).get("kernel_size", 3))
    denoise_thr = float(cfg.get("tensor_denoise", {}).get("threshold", 0.5))

    # Validity mask (exclude export padding / no-data edges)
    valid = (b03 > 0) & (b08 > 0)

    # NDWI
    ndwi = compute_ndwi(b03, b08, scale=scale)
    ndwi_out = out_dir / "ndwi.tif"
    # Use numeric nodata for broader GeoTIFF compatibility.
    ndwi_to_write = ndwi.copy()
    ndwi_to_write[~valid] = -9999.0
    write_tif(ndwi_out, ndwi_to_write, prof, dtype="float32", nodata=-9999.0)

    # Raw mask (0/1) with nodata=255
    mask_raw = threshold_ndwi(ndwi, thr=ndwi_thr)
    mask_raw[~valid] = 255
    raw_out = out_dir / "flood_mask_raw.tif"
    write_tif(raw_out, mask_raw, prof, dtype="uint8", nodata=255)

    # Denoise: conv2d expects 0/1; map nodata(255) -> 0 temporarily, then restore nodata
    mask_for_denoise = mask_raw.copy()
    mask_for_denoise[mask_for_denoise == 255] = 0
    mask_f = tensor_denoise_mask(mask_for_denoise, kernel_size=k, thr=denoise_thr)
    mask_f[~valid] = 255

    filt_out = out_dir / "flood_mask_filtered.tif"
    write_tif(filt_out, mask_f, prof, dtype="uint8", nodata=255)

    return {
        "ndwi": str(ndwi_out),
        "flood_mask_raw": str(raw_out),
        "flood_mask_filtered": str(filt_out),
        "valid_ratio": float(valid.mean()),
        "params": {
            "ndwi_scale": scale,
            "ndwi_threshold": ndwi_thr,
            "tensor_kernel_size": k,
            "tensor_threshold": denoise_thr,
            "ndwi_nodata": -9999.0,
            "mask_nodata": 255,
        },
    }


def main(config_path: str = "config.yaml", prep_result_path: Optional[str] = None) -> None:
    """
    CLI entry point for Module B.

    Parameters
    ----------
    config_path:
        Path to config YAML.
    prep_result_path:
        Path to Module A result YAML (optional).
    """
    cfg = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))

    if prep_result_path is None:
        prep_result_path = str(Path(cfg["paths"]["out_dir"]) / "a_raster_prep_result.yaml")

    prep = yaml.safe_load(Path(prep_result_path).read_text(encoding="utf-8"))
    res = run(cfg, prep)

    out_dir = Path(cfg.get("paths", {}).get("output_dir", "data/output"))
    (out_dir / "b_flood_mask_result.yaml").write_text(
        yaml.safe_dump(res, sort_keys=False), encoding="utf-8"
    )
    print("[B] Done. Outputs in:", out_dir)


if __name__ == "__main__":
    main()
