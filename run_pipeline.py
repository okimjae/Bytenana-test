import sys
import argparse
from src.config import settings
from src.observability.logger import logger, PipelineStageTimer
from src.observability.sentry_integration import init_sentry
from src.db.connection import db_manager
from src.db.ddl import initialize_schemas
from src.db.sink import db_sink
from src.ingestion.zoning_extractor import zoning_extractor
from src.ingestion.parcels_extractor import parcels_extractor
from src.spatial.matcher import spatial_matcher
from src.analytics.queries import analytics_engine, print_analytical_results
from src.analytics.stretch_nearby import proximity_analytics
from src.evals.eval_harness import EvaluationHarness
from tabulate import tabulate


def run_pipeline(run_evals: bool = True, backend: str = "duckdb"):
    print("=" * 80)
    print(" 🚀 STARTING BUDA & HAYS COUNTY GEOSPATIAL DATA PIPELINE")
    print("=" * 80)

    # 1. Initialize Observability
    init_sentry()

    # 2. Database Initialization
    with PipelineStageTimer("initialize_database", {"backend": backend}):
        initialize_schemas(backend=backend)

    # 3. Ingestion: City of Buda Zoning
    with PipelineStageTimer("ingest_city_of_buda_zoning"):
        zoning_gdf = zoning_extractor.extract_from_api()
        logger.info(f"Loaded {len(zoning_gdf)} zoning polygons.")

    # 4. Ingestion: Hays County Parcels
    with PipelineStageTimer("ingest_hays_county_parcels"):
        parcels_gdf = parcels_extractor.extract_from_api()
        logger.info(f"Loaded {len(parcels_gdf)} county parcels with computed lot sizes.")

    # 5. Spatial Match & Fact Table Materialization
    with PipelineStageTimer("spatial_join_and_classification"):
        enriched_gdf = spatial_matcher.match_parcels_to_zoning(parcels_gdf, zoning_gdf)

    # 6. Physical Database Persistence (SINK)
    if backend == "duckdb":
        db_sink.persist_to_duckdb(zoning_gdf, parcels_gdf, enriched_gdf)

    # 7. Core Analytical Queries Presentation
    print_analytical_results(enriched_gdf)

    # 8. Optional Stretch: 1km Radius Analysis
    print("=" * 80)
    print(" 🎯 OPTIONAL STRETCH: 1 KM RADIUS LOT SIZE QUERY (Downtown Buda)")
    print("=" * 80)
    stretch_df = proximity_analytics.get_parcels_within_radius(enriched_gdf, lon=-97.843, lat=30.083, radius_km=1.0)
    if not stretch_df.empty:
        print(tabulate(stretch_df, headers="keys", tablefmt="fancy_grid", showindex=False))
    else:
        print("No parcels found in 1 km radius.")
    print("\n")

    # 9. Run Automated Evals Harness
    if run_evals:
        harness = EvaluationHarness()
        eval_ok = harness.run_all()
        if not eval_ok:
            logger.error("Automated Evaluation Suite failed assertions.")
            sys.exit(1)

    print("=" * 80)
    print(" ✅ PIPELINE COMPLETED SUCCESSFULLY WITH ALL ASSERIONS VERIFIED")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Buda & Hays County Geospatial Pipeline")
    parser.add_argument("--no-evals", action="store_true", help="Skip automated evaluation harness")
    parser.add_argument("--backend", choices=["duckdb", "postgis"], default="duckdb", help="Database backend")
    args = parser.parse_args()

    run_pipeline(run_evals=not args.no_evals, backend=args.backend)
