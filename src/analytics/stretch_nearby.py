import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from src.config import settings
from src.spatial.geometry import geo_engine
from src.observability.logger import logger, PipelineStageTimer


class ProximityAnalytics:
    """Answers optional stretch question: compute statistics within radius of a point."""

    # 1 kilometer = 3280.84 US Survey Feet (EPSG:2277 units)
    KM_TO_FEET: float = 3280.84

    @staticmethod
    def get_parcels_within_radius(
        enriched_gdf: gpd.GeoDataFrame,
        lon: float = -97.843,
        lat: float = 30.083,
        radius_km: float = 1.0,
    ) -> pd.DataFrame:
        """Computes summary metrics for parcels within radius_km of a geographic coordinate (WGS84)."""
        with PipelineStageTimer("stretch_proximity_query", {"lon": lon, "lat": lat, "radius_km": radius_km}):
            # Ensure target CRS (EPSG:2277)
            parcels_proj = geo_engine.reproject_to_local_plane(enriched_gdf)

            # Create point in WGS84 and project to EPSG:2277
            pt_wgs84 = gpd.GeoSeries([Point(lon, lat)], crs=settings.SOURCE_CRS)
            pt_proj = pt_wgs84.to_crs(settings.TARGET_CRS).iloc[0]

            # Buffer distance in feet
            radius_ft = radius_km * ProximityAnalytics.KM_TO_FEET
            buffer_geom = pt_proj.buffer(radius_ft)

            # Filter parcels intersecting buffer
            nearby_mask = parcels_proj["geometry"].intersects(buffer_geom)
            nearby_gdf = parcels_proj[nearby_mask].copy()

            if nearby_gdf.empty:
                return pd.DataFrame()

            # Compute summary stats
            total_count = len(nearby_gdf)
            res_count = (nearby_gdf["is_residential"] == True).sum()
            avg_lot_size = nearby_gdf["calculated_area_acres"].mean()
            median_lot_size = nearby_gdf["calculated_area_acres"].median()

            summary = pd.DataFrame(
                [
                    {
                        "center_lon": lon,
                        "center_lat": lat,
                        "radius_km": radius_km,
                        "total_parcels_in_radius": total_count,
                        "residential_parcels_in_radius": res_count,
                        "avg_lot_size_acres": round(avg_lot_size, 3),
                        "median_lot_size_acres": round(median_lot_size, 3),
                    }
                ]
            )
            return summary


proximity_analytics = ProximityAnalytics()
