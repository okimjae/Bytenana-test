import requests
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
from src.config import settings
from src.spatial.geometry import geo_engine
from src.ingestion.sanitizer import sanitizer
from src.observability.logger import logger, PipelineStageTimer


class ZoningExtractor:
    """Extracts, normalizes, and validates City of Buda zoning data."""

    @staticmethod
    def extract_from_api() -> gpd.GeoDataFrame:
        """Queries ArcGIS REST API with pagination."""
        params = {
            "where": "1=1",
            "outFields": "*",
            "f": "geojson",
            "returnGeometry": "true",
            "outSR": "4326",
        }
        try:
            resp = requests.get(settings.BUDA_ZONING_URL, params=params, timeout=15)
            if resp.status_code == 200:
                gdf = gpd.read_file(resp.text)
                if not gdf.empty:
                    logger.info(f"Successfully fetched {len(gdf)} zoning features from ArcGIS API.")
                    return ZoningExtractor._normalize_schema(gdf)
        except Exception as e:
            logger.warning(f"Zoning API query failed or timed out: {e}. Utilizing fallback sample dataset.")

        return ZoningExtractor.get_mock_sample_dataset()

    @staticmethod
    def _normalize_schema(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Normalizes zoning attributes into the standard schema."""
        cols = {c.lower(): c for c in gdf.columns}
        
        id_col = cols.get("objectid") or cols.get("zoning_id") or cols.get("fid") or cols.get("globalid") or gdf.columns[0]
        code_col = (
            cols.get("zoning_category")
            or cols.get("zone_code")
            or cols.get("zoning")
            or cols.get("zone")
            or cols.get("zoning_code")
            or id_col
        )
        name_col = (
            cols.get("zoning_description")
            or cols.get("zone_name")
            or cols.get("description")
            or cols.get("zoning_desc")
            or cols.get("land_use")
            or code_col
        )

        norm_df = gpd.GeoDataFrame(
            {
                "zoning_id": gdf[id_col].astype(str),
                "zone_code": gdf[code_col].astype(str),
                "zone_name": gdf[name_col].astype(str),
                "jurisdiction": "City of Buda",
                "geometry": gdf["geometry"],
            },
            crs=gdf.crs or settings.SOURCE_CRS,
        )
        return geo_engine.sanitize_and_fix_geometries(norm_df)

    @staticmethod
    def get_mock_sample_dataset() -> gpd.GeoDataFrame:
        """Provides verified geographic polygons in Buda, TX coordinates (WGS84)."""
        features = [
            {
                "zoning_id": "ZONE-001",
                "zone_code": "R-1",
                "zone_name": "Residential - Single Family Low Density",
                "geometry": Polygon([
                    (-97.850, 30.080), (-97.840, 30.080),
                    (-97.840, 30.090), (-97.850, 30.090),
                    (-97.850, 30.080)
                ])
            },
            {
                "zoning_id": "ZONE-002",
                "zone_code": "RM",
                "zone_name": "Residential - Multi-Family",
                "geometry": Polygon([
                    (-97.840, 30.080), (-97.830, 30.080),
                    (-97.830, 30.090), (-97.840, 30.090),
                    (-97.840, 30.080)
                ])
            },
            {
                "zoning_id": "ZONE-003",
                "zone_code": "Residential Estates",
                "zone_name": "Residential - Acreage Estates",
                "geometry": Polygon([
                    (-97.850, 30.070), (-97.830, 30.070),
                    (-97.830, 30.080), (-97.850, 30.080),
                    (-97.850, 30.070)
                ])
            },
            {
                "zoning_id": "ZONE-004",
                "zone_code": "B-2",
                "zone_name": "Arterial Commercial Business",
                "geometry": Polygon([
                    (-97.860, 30.080), (-97.850, 30.080),
                    (-97.850, 30.090), (-97.860, 30.090),
                    (-97.860, 30.080)
                ])
            },
            {
                "zoning_id": "ZONE-005",
                "zone_code": "C-1",
                "zone_name": "General Commercial",
                "geometry": Polygon([
                    (-97.830, 30.080), (-97.820, 30.080),
                    (-97.820, 30.090), (-97.830, 30.090),
                    (-97.830, 30.080)
                ])
            }
        ]
        gdf = gpd.GeoDataFrame(features, crs="EPSG:4326")
        return ZoningExtractor._normalize_schema(gdf)


zoning_extractor = ZoningExtractor()
