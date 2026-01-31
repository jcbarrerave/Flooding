"""
Run raster pipeline (Module A + B + NDWI-Series + Cube) and write a single run log.

Pipeline order:
1) Module A (raster_prep): prepare/align rasters for event-date processing.
2) Module B (flood_mask): compute NDWI + threshold + tensor denoise for event-date flood mask.
3) Module NDWI-Series (ndwi_series): build analytical NDWI time series from bands_time -> ndwi_time.
4) Module Cube (cube_demo): build an xarray time cube from ndwi_time and compute summaries.
"""

from pathlib import Path
import sys
import yaml

# Allow importing modules from src/
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

import raster_prep
import flood_mask
import ndwi_series  # NEW: analytical NDWI time-series builder
import cube_demo


def main() -> None:
    """Main entry point for running the full raster pipeline."""
    cfg = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))

    # Module A: raster preprocessing/alignment (typically event-date related)
    a_res = raster_prep.run(cfg)

    # Module B: NDWI + threshold + tensor denoise to produce event-date flood mask
    b_res = flood_mask.run(cfg, a_res)

    # NEW Module: build analytical NDWI time series (from bands_time -> ndwi_time)
    # This ensures the Cube uses quantitative NDWI rasters (NOT visualization products).
    s_res = ndwi_series.run(cfg)

    # Module Cube: stack NDWI rasters into (time, y, x) cube and compute summaries
    c_res = cube_demo.run(cfg)

    # Write a single run log for reproducibility.
    out_dir = Path(cfg.get("paths", {}).get("output_dir", "data/output"))
    out_dir.mkdir(parents=True, exist_ok=True)

    run_log = {
        "config": cfg,
        "module_a": a_res,
        "module_b": b_res,
        "module_ndwi_series": s_res,  # NEW
        "module_cube": c_res,
    }

    log_path = out_dir / "run_log.yaml"
    log_path.write_text(yaml.safe_dump(run_log, sort_keys=False), encoding="utf-8")

    print("\nPipeline finished.")
    print("A outputs:", a_res)
    print("B outputs:", b_res)
    print("NDWI-Series outputs:", s_res)
    print("Cube outputs:", c_res)
    print("Log:", log_path)


if __name__ == "__main__":
    main()