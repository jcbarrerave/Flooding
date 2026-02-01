"""
Mapping utilities for flood visualization (Stage E).

This module contains functions to visualize flood extent and
flood impact before, during, and after the flood event.
"""

from pathlib import Path

import geopandas as gpd
import rasterio
import matplotlib.pyplot as plt
from rasterio.plot import show
from matplotlib.patches import Patch
from shapely.geometry import box

def plot_during_flood(
    raster_path: Path,
    buildings_path: Path,
    output_path: Path,
):
    """
    Map showing flood extent and affected buildings
    during the flood event.
    """
    buildings = gpd.read_file(buildings_path)

    # Open raster to get its spatial extent and CRS
    with rasterio.open(raster_path) as src:
        raster_bounds = src.bounds
        raster_crs = src.crs

    # Reproject buildings if needed
    if buildings.crs != raster_crs:
        buildings = buildings.to_crs(raster_crs)

    # Create a GeoDataFrame with the raster bounding box
    raster_bbox = gpd.GeoDataFrame(
        geometry=[box(*raster_bounds)],
        crs=raster_crs,
    )

    # Clip buildings to raster extent
    buildings = gpd.clip(buildings, raster_bbox)

    # Separate flooded / non-flooded after clipping
    flooded = buildings[buildings["flooded"] == 1]
    not_flooded = buildings[buildings["flooded"] == 0]

    fig, ax = plt.subplots(figsize=(14, 14))

    # Flood raster (background)
    with rasterio.open(raster_path) as src:
        show(src, ax=ax, cmap="Blues", alpha=0.25)

    # Non-flooded buildings (background but visible)
    not_flooded.plot(
        ax=ax,
        color="#bdbdbd",
        edgecolor="black",
        linewidth=0.3,
        alpha=0.6,
        zorder=3,
    )

    # Flooded buildings (foreground)
    flooded.plot(
        ax=ax,
        color="#d73027",
        edgecolor="red",
        linewidth=0.5,
        alpha=0.95,
        zorder=4,
    )

    legend_elements = [
        Patch(facecolor="#d73027", edgecolor="black", label="Flooded buildings"),
        Patch(facecolor="#bdbdbd", edgecolor="black", label="Not flooded buildings"),
    ]
    ax.legend(handles=legend_elements, loc="lower left")

    ax.set_title("Flood extent and affected buildings (During event)")
    ax.set_axis_off()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_admin_impact(
    admin_summary_path: Path,
    output_path: Path,
):
    """
    Choropleth map showing relative flood impact by
    administrative unit (percentage of flooded buildings).
    """
    admin = gpd.read_file(admin_summary_path)

    # Convert ratio to percentage for visualization
    admin["flooded_pct"] = admin["flooded_ratio"] * 100

    fig, ax = plt.subplots(figsize=(12, 12))

    admin.plot(
        ax=ax,
        column="flooded_pct",
        cmap="Reds",
        scheme="NaturalBreaks",
        k=5,
        linewidth=0.5,
        edgecolor="black",
        legend=True,
        legend_kwds={
            "title": "Flooded buildings (%)",
            "loc": "lower left",
        },
    )

    ax.set_title("Relative flood impact by administrative unit (%)")
    ax.set_axis_off()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)