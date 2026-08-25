import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from src.spatial.geometry import geo_engine
from src.spatial.classifier import zoning_classifier
from src.observability.logger import logger, PipelineStageTimer


class SpatialMatcher:
    """Matches parcels to zoning districts using spatial indexing and Point-on-Surface."""

    @staticmethod
    def match_parcels_to_zoning(
        parcels_gdf: gpd.GeoDataFrame,
        zoning_gdf: gpd.GeoDataFrame,
    ) -> gpd.GeoDataFrame:
        with PipelineStageTimer("spatial_join_parcels_zoning"):
            # Ensure both are in target planar CRS (EPSG:2277)
            parcels_proj = geo_engine.reproject_to_local_plane(parcels_gdf)
            zoning_proj = geo_engine.reproject_to_local_plane(zoning_gdf)

            # Generate representative points (Point-on-surface) to avoid edge cases in concave/L-shaped parcels
            points_geom = parcels_proj["geometry"].apply(geo_engine.get_point_on_surface)
            points_gdf = gpd.GeoDataFrame(
                parcels_proj[["parcel_id"]],
                geometry=points_geom,
                crs=parcels_proj.crs,
            )

            # Perform Spatial Join: points within or intersecting zoning polygon
            joined = gpd.sjoin(
                points_gdf,
                zoning_proj[["zoning_id", "zone_code", "zone_name", "geometry"]],
                how="left",
                predicate="intersects",
            )

            # Remove duplicate matches if a point touches an exact boundary edge (keep first)
            joined = joined[~joined.index.duplicated(keep="first")]

            # Attach attributes back to original parcel polygons
            result_gdf = parcels_proj.copy()
            result_gdf["zoning_id"] = joined["zoning_id"].values
            result_gdf["zone_code"] = joined["zone_code"].values
            result_gdf["zone_name"] = joined["zone_name"].values

            # Classify residential status
            result_gdf["is_residential"] = result_gdf.apply(
                lambda row: zoning_classifier.is_residential(row.get("zone_code"), row.get("zone_name")),
                axis=1,
            )

            # Match status flag
            result_gdf["match_status"] = result_gdf["zoning_id"].apply(
                lambda zid: "BUDA_MATCHED" if (pd.notna(zid) and str(zid) != "nan") else "UNMATCHED_COUNTY_OUTSIDE_BUDA"
            )

            buda_count = (result_gdf["match_status"] == "BUDA_MATCHED").sum()
            county_count = (result_gdf["match_status"] == "UNMATCHED_COUNTY_OUTSIDE_BUDA").sum()
            res_count = (result_gdf["is_residential"] == True).sum()

            logger.info(
                f"Spatial match complete: {buda_count} Buda parcels matched ({res_count} residential), "
                f"{county_count} outside Buda."
            )
            return result_gdf


spatial_matcher = SpatialMatcher()
