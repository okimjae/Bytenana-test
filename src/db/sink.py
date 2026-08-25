import geopandas as gpd
import pandas as pd
import duckdb
from src.db.connection import db_manager
from src.observability.logger import logger, PipelineStageTimer


class DatabaseSink:
    """Persists staged and enriched geospatial datasets into the database backend."""

    @staticmethod
    def persist_to_duckdb(
        zoning_gdf: gpd.GeoDataFrame,
        parcels_gdf: gpd.GeoDataFrame,
        enriched_gdf: gpd.GeoDataFrame,
    ):
        with PipelineStageTimer("persist_datasets_to_database"):
            conn = db_manager.get_duckdb_connection()

            # 1. Persist stg_zoning
            zoning_df = zoning_gdf.copy()
            zoning_df["geom_wkt"] = zoning_df["geometry"].to_wkt()
            zoning_export = zoning_df[["zoning_id", "zone_code", "zone_name", "jurisdiction", "geom_wkt"]]

            conn.execute("DELETE FROM stg_zoning;")
            conn.register("zoning_df_view", zoning_export)
            conn.execute("""
                INSERT INTO stg_zoning (zoning_id, zone_code, zone_name, jurisdiction, geom_wkt)
                SELECT zoning_id, zone_code, zone_name, jurisdiction, geom_wkt FROM zoning_df_view;
            """)

            # 2. Persist stg_parcels
            parcels_df = parcels_gdf.copy()
            parcels_df["geom_wkt"] = parcels_df["geometry"].to_wkt()
            parcels_export = parcels_df[
                ["parcel_id", "subdivision", "legal_description", "raw_stated_area", "geom_wkt", "calculated_area_sqft", "calculated_area_acres"]
            ]

            conn.execute("DELETE FROM stg_parcels;")
            conn.register("parcels_df_view", parcels_export)
            conn.execute("""
                INSERT INTO stg_parcels (parcel_id, subdivision, legal_description, raw_stated_area, geom_wkt, calculated_area_sqft, calculated_area_acres)
                SELECT parcel_id, subdivision, legal_description, raw_stated_area, geom_wkt, calculated_area_sqft, calculated_area_acres FROM parcels_df_view;
            """)

            # 3. Persist fct_parcels_enriched
            enriched_df = enriched_gdf.copy()
            enriched_df["geom_wkt"] = enriched_df["geometry"].to_wkt()
            enriched_export = enriched_df[
                [
                    "parcel_id",
                    "subdivision",
                    "legal_description",
                    "calculated_area_sqft",
                    "calculated_area_acres",
                    "zoning_id",
                    "zone_code",
                    "zone_name",
                    "is_residential",
                    "match_status",
                    "geom_wkt",
                ]
            ]

            conn.execute("DELETE FROM fct_parcels_enriched;")
            conn.register("enriched_df_view", enriched_export)
            conn.execute("""
                INSERT INTO fct_parcels_enriched
                SELECT parcel_id, subdivision, legal_description, calculated_area_sqft, calculated_area_acres,
                       zoning_id, zone_code, zone_name, is_residential, match_status, geom_wkt
                FROM enriched_df_view;
            """)

            logger.info("Successfully persisted all datasets into DuckDB tables.")


db_sink = DatabaseSink()
