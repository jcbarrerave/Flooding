"""
Plotting utilities for flood impact summaries (Stage E).
"""

from pathlib import Path
import geopandas as gpd
import matplotlib.pyplot as plt


def plot_flooded_buildings_bar(
    admin_summary_path: Path,
    output_path: Path,
    top_n: int = 10,
):
    """
    Create a bar chart showing the number of flooded buildings
    per administrative unit.

    Parameters
    ----------
    admin_summary_path : pathlib.Path
        Path to administrative flood summary.
    output_path : pathlib.Path
        Path to save the bar chart (PNG).
    top_n : int, default 10
        Number of administrative units to display.
    """
    admin = gpd.read_file(admin_summary_path)

    admin_sorted = (
        admin.sort_values("flooded_buildings", ascending=False)
        .head(top_n)
    )

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.bar(
        admin_sorted["NAME_3"],
        admin_sorted["flooded_buildings"],
    )

    ax.set_title("Most affected administrative units")
    ax.set_ylabel("Flooded buildings")
    ax.set_xlabel("Administrative unit")
    ax.tick_params(axis="x", rotation=45)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)