"""
Mapping utilities for flood visualization (Stage E).

This module contains functions to visualize flood extent and
flood impact during, and after the flood event.
"""

from pathlib import Path

import geopandas as gpd
import rasterio
import matplotlib.pyplot as plt
from rasterio.plot import show
from matplotlib.patches import Patch



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

    flooded = buildings[buildings["flooded"] == 1]
    not_flooded = buildings[buildings["flooded"] == 0]

    fig, ax = plt.subplots(figsize=(14, 14))

    with rasterio.open(raster_path) as src:
        show(src, ax=ax, cmap="Blues", alpha=0.35)

    not_flooded.plot(
        ax=ax,
        color="lightgrey",
        edgecolor="none",
        alpha=0.2,
    )

    flooded.plot(
        ax=ax,
        color="red",
        edgecolor="black",
        linewidth=0.2,
        alpha=0.9,
    )

    legend_elements = [
        Patch(facecolor="red", edgecolor="black", label="Flooded buildings"),
        Patch(facecolor="lightgrey", label="Not flooded buildings"),
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
        linewidth=0.5,
        edgecolor="black",
        legend=True,
        legend_kwds={
            "label": "Flooded buildings (%)",
            "shrink": 0.6,
        },
    )

    ax.set_title("Relative flood impact by administrative unit (%)")
    ax.set_axis_off()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")

    plt.close(fig)
