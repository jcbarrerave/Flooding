"""
Raster–vector integration utilities (Stage D).

This module assigns flood information to building footprints by
sampling a raster flood mask at building centroid locations.
The resulting per-building flood indicators can later be aggregated
by administrative unit.
"""

from pathlib import Path

import geopandas as gpd
import rasterio
import numpy as np


# ---------------------------------------------------------------------
# Raster sampling at building centroids
# ---------------------------------------------------------------------

def sample_raster_at_centroids(
    buildings: gpd.GeoDataFrame,
    raster_path: Path,
    value_field: str = "flood_value",
) -> gpd.GeoDataFrame:
    """
    Sample a raster flood mask at building centroid locations.

    For each building geometry, the centroid is computed and used
    to extract the raster value at that location. The sampled raster
    value is stored in a new column.

    Parameters
    ----------
    buildings : geopandas.GeoDataFrame
        Building footprint geometries (polygons).
    raster_path : pathlib.Path
        Path to the raster flood mask (e.g. flood_mask_filtered.tif).
    value_field : str, default "flood_value"
        Name of the column used to store the sampled raster values.

    Returns
    -------
    geopandas.GeoDataFrame
        Buildings GeoDataFrame with an additional column containing
        the raster value sampled at each building centroid.

    Raises
    ------
    ValueError
        If the CRS of the raster and the buildings do not match.
    """
    # Create a copy to avoid modifying the input GeoDataFrame in place
    gdf = buildings.copy()

    # -----------------------------------------------------------------
    # Compute building centroids
    # -----------------------------------------------------------------
    # Centroids are used only for sampling and do not replace
    # the original building geometries.
    centroids = gdf.geometry.centroid

    # -----------------------------------------------------------------
    # Open raster and sample values
    # -----------------------------------------------------------------
    with rasterio.open(raster_path) as src:
        # Ensure CRS consistency between raster and vector data
        if src.crs != gdf.crs:
            raise ValueError(
                "CRS mismatch between raster and buildings. "
                "Ensure both datasets share the same CRS before sampling."
            )

        # Extract (x, y) coordinates of centroids
        coords = [(pt.x, pt.y) for pt in centroids]

        # Sample raster values at centroid locations
        sampled = list(src.sample(coords))

    # -----------------------------------------------------------------
    # Store sampled raster values
    # -----------------------------------------------------------------
    # Rasterio returns values as arrays (one per band),
    # so we flatten them into a 1D NumPy array.
    values = np.array(sampled).flatten()

    # Add sampled values to the GeoDataFrame
    gdf[value_field] = values

    return gdf


# ---------------------------------------------------------------------
# Flood classification
# ---------------------------------------------------------------------

def classify_flooded(
    buildings: gpd.GeoDataFrame,
    value_field: str = "flood_value",
    flooded_field: str = "flooded",
    threshold: float = 0.5,
) -> gpd.GeoDataFrame:
    """
    Classify buildings as flooded or not flooded based on raster values.

    A binary flood indicator is created by applying a threshold
    to the raster value sampled at each building centroid.

    Parameters
    ----------
    buildings : geopandas.GeoDataFrame
        Buildings with sampled raster values.
    value_field : str, default "flood_value"
        Column containing raster values.
    flooded_field : str, default "flooded"
        Name of the binary flood indicator column to create.
    threshold : float, default 0.5
        Threshold above which a building is considered flooded.

    Returns
    -------
    geopandas.GeoDataFrame
        Buildings GeoDataFrame with a binary flooded indicator:
        - 1 = flooded
        - 0 = not flooded
    """
    # Defensive copy
    gdf = buildings.copy()

    # Apply threshold-based classification
    gdf[flooded_field] = (gdf[value_field] > threshold).astype(int)

    return gdf