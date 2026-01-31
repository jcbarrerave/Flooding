"""
Spatial operations for vector data (Stage C).

This module performs spatial operations using GeoPandas and pyproj.
It assumes that the Area of Interest (AOI) is defined externally
(e.g., from a raster extent generated in stages A/B) and provided
as a vector geometry.

The module is responsible for:
- ensuring CRS consistency,
- clipping vector datasets to a raster-derived AOI,
- assigning administrative unit identifiers to buildings.

This module does NOT handle file I/O or geometry cleaning.
"""

import geopandas as gpd


# ---------------------------------------------------------------------
# CRS handling
# ---------------------------------------------------------------------

def ensure_same_crs(
    gdf: gpd.GeoDataFrame,
    target_crs
) -> gpd.GeoDataFrame:
    """
    Reproject a GeoDataFrame to a target CRS if needed.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        Input GeoDataFrame.
    target_crs : pyproj CRS, EPSG code, or string
        Target coordinate reference system.

    Returns
    -------
    geopandas.GeoDataFrame
        GeoDataFrame in the target CRS.
    """
    if gdf.crs != target_crs:
        return gdf.to_crs(target_crs)
    return gdf


# ---------------------------------------------------------------------
# AOI-based clipping
# ---------------------------------------------------------------------

def clip_to_aoi(
    gdf: gpd.GeoDataFrame,
    aoi: gpd.GeoDataFrame
) -> gpd.GeoDataFrame:
    """
    Clip a GeoDataFrame to a raster-derived Area of Interest (AOI).

    The AOI is expected to be provided as a GeoDataFrame representing
    the spatial extent of the raster used in stages A/B.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        Input vector dataset (e.g., buildings or admin units).
    aoi : geopandas.GeoDataFrame
        AOI geometry derived from raster extent.

    Returns
    -------
    geopandas.GeoDataFrame
        GeoDataFrame clipped to the AOI.
    """
    return gpd.clip(gdf, aoi)


# ---------------------------------------------------------------------
# Spatial join
# ---------------------------------------------------------------------

def assign_admin_id(
    buildings: gpd.GeoDataFrame,
    admin_units: gpd.GeoDataFrame,
    admin_id_field: str = "GID_3",
) -> gpd.GeoDataFrame:
    """
    Assign an administrative unit identifier to each building
    using a spatial join.

    Buildings are assigned to administrative units based on a
    'within' spatial predicate. The administrative identifier
    is standardized to a column named 'admin_id' in the output,
    regardless of the original field name in the administrative
    dataset.

    Parameters
    ----------
    buildings : geopandas.GeoDataFrame
        Building footprint geometries.
    admin_units : geopandas.GeoDataFrame
        Administrative boundaries containing an identifier field.
    admin_id_field : str, default "GID_3"
        Name of the identifier field in the administrative dataset
        (e.g. 'GID_3' for GADM ADM level 3).

    Returns
    -------
    geopandas.GeoDataFrame
        Buildings with an added 'admin_id' column identifying
        the administrative unit each building belongs to.
    """

    # Select identifier and geometry, and standardize column name
    admin = admin_units[[admin_id_field, "geometry"]].rename(
        columns={admin_id_field: "admin_id"}
    )

    # Spatial join: preserve all buildings (left join)
    joined = gpd.sjoin(
        buildings,
        admin,
        how="left",
        predicate="within",
    )

    # Remove join index artifact
    return joined.drop(columns="index_right")