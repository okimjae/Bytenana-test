import requests
import geopandas as gpd
from shapely.geometry import Polygon
from src.config import settings
from src.spatial.geometry import geo_engine
from src.ingestion.sanitizer import sanitizer
from src.observability.logger import logger, PipelineStageTimer


class ParcelsExtractor:
    """Extracts, normalizes, and sanitizes Hays County parcel datasets."""

    @staticmethod
    def extract_from_api() -> gpd.GeoDataFrame:
        """Fetches parcels from ArcGIS open data endpoint."""
        params = {
            "where": "1=1",
            "outFields": "*",
            "f": "geojson",
            "returnGeometry": "true",
            "outSR": "4326",
            "resultRecordCount": "2000",
        }
        try:
            resp = requests.get(settings.HAYS_PARCELS_URL, params=params, timeout=15)
            if resp.status_code == 200:
                gdf = gpd.read_file(resp.text)
                if not gdf.empty:
                    logger.info(f"Successfully fetched {len(gdf)} parcel features from ArcGIS.")
                    return ParcelsExtractor._normalize_schema(gdf)
        except Exception as e:
            logger.warning(f"Parcels API query failed or timed out: {e}. Utilizing fallback sample dataset.")

        return ParcelsExtractor.get_mock_sample_dataset()

    @staticmethod
    def _normalize_schema(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Standardizes column mappings and derives calculated area from geometry."""
        cols = {c.lower(): c for c in gdf.columns}

        id_col = cols.get("parcel_id") or cols.get("prop_id") or cols.get("quickrefid") or cols.get("objectid") or gdf.columns[0]
        subdiv_col = cols.get("subdivision") or cols.get("subdiv_name") or cols.get("hood_cd")
        desc_col = cols.get("legal_description") or cols.get("legal_desc") or cols.get("prop_desc")
        area_col = cols.get("raw_stated_area") or cols.get("stated_area") or cols.get("calc_acre") or cols.get("gis_area")

        norm_df = gpd.GeoDataFrame(
            {
                "parcel_id": gdf[id_col].astype(str),
                "subdivision": gdf[subdiv_col].fillna("UNSPECIFIED").astype(str) if subdiv_col else "UNSPECIFIED",
                "legal_description": gdf[desc_col].fillna("").astype(str) if desc_col else "",
                "raw_stated_area": gdf[area_col].astype(float) if area_col and area_col in gdf else None,
                "geometry": gdf["geometry"],
            },
            crs=gdf.crs or settings.SOURCE_CRS,
        )

        # 1. Clean geometries
        cleaned_df = geo_engine.sanitize_and_fix_geometries(norm_df)

        # 2. Project to EPSG:2277 and compute lot size in acres
        projected_df = geo_engine.compute_lot_size_acres(cleaned_df)
        return projected_df

    @staticmethod
    def get_mock_sample_dataset() -> gpd.GeoDataFrame:
        """Generates realistic Hays County & Buda parcels with varied sizes (below/above 1 acre)."""
        features = [
            # 1. Buda Downtown Residential (Large > 1 acre) in Zone R-1
            {
                "parcel_id": "HAYS-P1001",
                "subdivision": "Whispering Hollow",
                "legal_description": "LOT 1 BLK A WHISPERING HOLLOW SEC 1",
                "raw_stated_area": 2.5,
                "geometry": Polygon([
                    (-97.848, 30.082), (-97.846, 30.082),
                    (-97.846, 30.085), (-97.848, 30.085),
                    (-97.848, 30.082)
                ])
            },
            # 2. Buda Residential (Small < 1 acre) in Zone R-1
            {
                "parcel_id": "HAYS-P1002",
                "subdivision": "Whispering Hollow",
                "legal_description": "LOT 2 BLK A WHISPERING HOLLOW SEC 1",
                "raw_stated_area": 0.45,
                "geometry": Polygon([
                    (-97.845, 30.082), (-97.8445, 30.082),
                    (-97.8445, 30.0825), (-97.845, 30.0825),
                    (-97.845, 30.082)
                ])
            },
            # 3. Buda Multi-Family Residential (> 1 acre) in Zone RM
            {
                "parcel_id": "HAYS-P1003",
                "subdivision": "Bradfield Village",
                "legal_description": "LOT 10 BLK B BRADFIELD VILLAGE",
                "raw_stated_area": 4.2,
                "geometry": Polygon([
                    (-97.838, 30.082), (-97.835, 30.082),
                    (-97.835, 30.086), (-97.838, 30.086),
                    (-97.838, 30.082)
                ])
            },
            # 4. Buda Residential Estates (> 1 acre) in Zone Residential Estates
            {
                "parcel_id": "HAYS-P1004",
                "subdivision": "Garlic Creek",
                "legal_description": "LOT 4 BLK C GARLIC CREEK EST",
                "raw_stated_area": 5.0,
                "geometry": Polygon([
                    (-97.845, 30.072), (-97.840, 30.072),
                    (-97.840, 30.076), (-97.845, 30.076),
                    (-97.845, 30.072)
                ])
            },
            # 5. Buda Commercial Parcel (> 1 acre) in Zone B-2 (NOT Residential)
            {
                "parcel_id": "HAYS-P1005",
                "subdivision": "Buda Commercial Park",
                "legal_description": "LOT 1 COMMERCIAL SEC 2",
                "raw_stated_area": 3.8,
                "geometry": Polygon([
                    (-97.858, 30.082), (-97.854, 30.082),
                    (-97.854, 30.086), (-97.858, 30.086),
                    (-97.858, 30.082)
                ])
            },
            # 6. Hays County Rural Parcel outside Buda city zoning (> 1 acre)
            {
                "parcel_id": "HAYS-P1006",
                "subdivision": "Driftwood Rural",
                "legal_description": "ABS 123 RANCH TRACT 5",
                "raw_stated_area": 15.0,
                "geometry": Polygon([
                    (-98.020, 30.120), (-98.010, 30.120),
                    (-98.010, 30.130), (-98.020, 30.130),
                    (-98.020, 30.120)
                ])
            }
        ]
        gdf = gpd.GeoDataFrame(features, crs="EPSG:4326")
        return ParcelsExtractor._normalize_schema(gdf)


parcels_extractor = ParcelsExtractor()
