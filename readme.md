# Flood Mapping with Sentinel-2 NDWI Datacube

Raster-based flood mapping using Sentinel-2 L2A imagery. Flooded areas are derived from NDWI thresholding and analyzed over time with a simple raster datacube.

## Workflow

1. Preprocess Sentinel-2 bands (B03, B08)
2. Compute NDWI and generate a threshold-based flood mask
3. Apply spatial filtering to reduce salt-and-pepper noise
4. Build a multi-temporal NDWI datacube
5. Produce temporal statistics and change products

## Environment Setup (Windows / conda-forge)

### 1) Create conda environment
conda env create -f environment.yml  
conda activate flood

### 2) Install pip dependencies
pip install -r requirements-pip.txt

## Run

From the project root directory:
python run_raster_pipeline.py

## Outputs

Main outputs are written to `data/output/` and include:
- ndwi.tif (NDWI raster)
- flood_mask_raw.tif (raw flood mask)
- flood_mask_filtered.tif (filtered flood mask)
- cube_stats.yaml (datacube statistics per date)
- ndwi_time_mean.tif (temporal mean NDWI)
- ndwi_change_last_minus_first.tif (NDWI change map)

The file `cube_stats.yaml` summarizes NDWI statistics (mean/min/max) and flooded-area ratios (NDWI > threshold) for each acquisition date.

## Reproducibility

Dependencies are specified in:
- environment.yml (conda / binary GIS stack)
- requirements-pip.txt (additional pip packages)

Tested on Windows using conda-forge packages.