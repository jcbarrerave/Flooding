"""
Visualization pipeline (Stage E).

This script generates static maps and plots to communicate
the results of the flood impact analysis.
"""

from pathlib import Path

from flood_project.viz.maps import (
    plot_during_flood,
    plot_admin_impact,
)
from flood_project.viz.plots import plot_flooded_buildings_bar


def main():
    """Run Stage E visualizations."""

    # -------------------------------------------------------------
    # Input paths (outputs from previous stages)
    # -------------------------------------------------------------
    raster_path = Path("outputs/raster/flood_mask_filtered.tif")   
    buildings_during_path = Path("outputs/vector/buildings_flooded.gpkg")
    admin_summary_path = Path("outputs/vector/admin_flood_summary.gpkg")

    # -------------------------------------------------------------
    # Output directory
    # -------------------------------------------------------------
    figures_dir = Path("outputs/figures")
    figures_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------
    # Output figures
    # -------------------------------------------------------------
    fig_during = figures_dir / "fig_during.png"
    fig_admin = figures_dir / "map_admin_impact.png"
    fig_bar = figures_dir / "summary_plot.png"

    # -------------------------------------------------------------
    # Generate maps and plots
    # -------------------------------------------------------------

    plot_during_flood(
    raster_path=raster_path,
    buildings_path=buildings_during_path,
    output_path=fig_during,
    )

    plot_admin_impact(
        admin_summary_path=admin_summary_path,
        output_path=fig_admin,
    )

    plot_flooded_buildings_bar(
        admin_summary_path=admin_summary_path,
        output_path=fig_bar,
        top_n=10,
    )


if __name__ == "__main__":
    main()