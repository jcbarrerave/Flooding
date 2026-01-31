"""Run raster pipeline (Module A + B + Cube) and write a single run log."""
from pathlib import Path
import sys
import yaml

# Allow importing modules from src/
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

import raster_prep
import flood_mask
import cube_demo


def main() -> None:
    cfg = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))

    # Module A
    a_res = raster_prep.run(cfg)

    # Module B
    b_res = flood_mask.run(cfg, a_res)

    # Module Cube (time cube from 3-day NDWI)
    c_res = cube_demo.run(cfg)

    # Write a single run log for reproducibility.
    out_dir = Path(cfg.get("paths", {}).get("output_dir", "data/output"))
    out_dir.mkdir(parents=True, exist_ok=True)

    run_log = {
        "config": cfg,
        "module_a": a_res,
        "module_b": b_res,
        "module_cube": c_res,
    }

    log_path = out_dir / "run_log.yaml"
    log_path.write_text(yaml.safe_dump(run_log, sort_keys=False), encoding="utf-8")

    print("\nPipeline finished.")
    print("A outputs:", a_res)
    print("B outputs:", b_res)
    print("Cube outputs:", c_res)
    print("Log:", log_path)


if __name__ == "__main__":
    main()