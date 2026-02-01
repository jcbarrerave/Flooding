# Data Source

Before running the code, make sure the **`data`** folder is available.

Download the **`data`** folder using the provided link. When opening the link, right-click on the **`data`** folder and download it, ensuring that there is **no nested `data` folder inside**. Once downloaded, place the **`data`** folder in the project’s **root directory**.

Download the folder using this link:
[data](https://universiteittwente-my.sharepoint.com/:f:/g/personal/j_c_barreravelandia_student_utwente_nl/IgD8WVNOrx50R6AEdwuHusLoAauio0PJxleHTPem6-QeYSI?e=Xj8r9Q)

# Flood Mapping and Impact Assessment

This project performs raster-based flood mapping using Sentinel-2 NDWI and assesses flood impacts on buildings through vector–raster integration and visualization.  
The workflow is fully reproducible and designed to run directly from a ZIP file using Conda.

## How to Run

1. Download the project as a ZIP file and unzip it.  
2. Open a terminal (or VS Code) in the project root directory.

bash: in the terminal run the following commands
1. conda env create -f environment.yml
2. conda activate flood
3. pip install -r requirements-pip.txt
4. python run_raster_pipeline.py
5. python src/flood_project/vector/run_c.py
6. python src/flood_project/vector/run_d.py
7. python src/flood_project/viz/run_e.py

## Running Tests

To run the unit tests, the project must be installed in editable mode so that the
`flood_project` package can be discovered by Python.

Execute:
1. pip install -e .
2. pytest

# Flood Mapping with Sentinel-2 NDWI Datacube

Raster-based flood mapping using Sentinel-2 L2A imagery. Flooded areas are derived from NDWI thresholding and analyzed over time with a simple raster datacube.

## Workflow

1. Preprocess Sentinel-2 bands (B03, B08)
2. Compute NDWI and generate a threshold-based flood mask
3. Apply spatial filtering to reduce salt-and-pepper noise
4. Build a multi-temporal NDWI datacube
5. Produce temporal statistics and change products

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

--------------------------------------------------------------------------------------------------

# Flood Impact Assessment

This section describes the workflow used to assess flood impacts on buildings through vector processing, raster–vector integration, and visualization. The workflow is implemented as a modular and reproducible pipeline in Python and managed with Poetry.

## Vector Data Preparation

### Objective
Prepare clean and spatially consistent vector datasets of building footprints and administrative units, and assign each building to its corresponding administrative unit.

### Inputs
- Raw building footprints
- Administrative boundaries (ADM level 3)
- Processed flood mask raster (used only to define the area of interest)

### Processing Steps
- Read vector data using GeoPandas and Fiona
- Derive the area of interest from the flood mask raster extent
- Identify and fix invalid geometries using Shapely
- Remove duplicate geometries
- Reproject all vector layers to a common CRS
- Clip buildings and administrative units to the area of interest
- Assign administrative unit identifiers to buildings using a spatial join
- Record basic quality control information

### Outputs
- buildings_admin.gpkg
- admin_units_adm3.gpkg
- qc_vector_prep.txt

### Execution
poetry run python -m flood_project.vector.run_c

## Raster–Vector Integration and Statistics

### Objective
Identify flooded buildings and aggregate flood impact statistics by administrative unit.

### Inputs
- Processed buildings with administrative IDs
- Processed administrative units
- Binary flood mask raster

### Processing Steps
- Compute building centroids
- Sample the flood mask raster at centroid locations
- Create a binary flooded indicator for each building
- Aggregate flooded and total building counts by administrative unit
- Join aggregated statistics back to administrative geometries

### Outputs
- buildings_flooded.gpkg
- admin_flood_summary.gpkg

### Execution
poetry run python -m flood_project.vector.run_d

## Visualization

### Objective
Communicate flood exposure and impact during, and after the flood event using static visualizations.

### Inputs
- Buildings with flood status
- Administrative units and flood summary statistics
- Flood mask raster

### Visualizations
- Map showing flood extent and affected buildings during the flood
- Choropleth map showing relative flood impact as the percentage of flooded buildings per administrative unit
- Bar chart showing absolute numbers of flooded buildings for the most affected administrative units

### Outputs
- fig_during.png
- map_admin_impact.png
- summary_plot.png

### Execution
poetry run python -m flood_project.viz.run_e

## Interpretation Notes

Flood impact is expressed using both relative percentages and absolute counts. Percentages allow comparison across administrative units of different sizes, while absolute counts provide context for small units with few buildings. Both representations should be interpreted together.
