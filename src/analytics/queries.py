import argparse
import pandas as pd
import geopandas as gpd
from tabulate import tabulate
from src.observability.logger import logger, PipelineStageTimer


class AnalyticsEngine:
    """Answers core analytical questions on the enriched geospatial dataset."""

    @staticmethod
    def get_residential_parcels_gt_1ac(enriched_gdf: gpd.GeoDataFrame) -> pd.DataFrame:
        """Finds all residential parcels with calculated area > 1.0 acre."""
        with PipelineStageTimer("query_residential_gt_1ac"):
            mask = (enriched_gdf["is_residential"] == True) & (enriched_gdf["calculated_area_acres"] > 1.0)
            df = enriched_gdf[mask][
                [
                    "parcel_id",
                    "subdivision",
                    "zone_code",
                    "zone_name",
                    "calculated_area_acres",
                    "legal_description",
                ]
            ].copy()
            df["calculated_area_acres"] = df["calculated_area_acres"].round(3)
            return df.sort_values(by="calculated_area_acres", ascending=False)

    @staticmethod
    def roll_up_stats_by_area(enriched_gdf: gpd.GeoDataFrame) -> pd.DataFrame:
        """Computes summary statistics (count, median, mean, min, max) grouped by subdivision/area."""
        with PipelineStageTimer("query_rollup_stats_by_area"):
            res_gdf = enriched_gdf[enriched_gdf["is_residential"] == True].copy()
            if res_gdf.empty:
                return pd.DataFrame(columns=["area_group", "total_parcels", "residential_gt_1ac", "median_lot_size_ac", "mean_lot_size_ac"])

            grouped = (
                res_gdf.groupby("subdivision")
                .agg(
                    total_residential_parcels=("parcel_id", "count"),
                    residential_gt_1ac=("calculated_area_acres", lambda s: (s > 1.0).sum()),
                    median_lot_size_ac=("calculated_area_acres", "median"),
                    mean_lot_size_ac=("calculated_area_acres", "mean"),
                    min_lot_size_ac=("calculated_area_acres", "min"),
                    max_lot_size_ac=("calculated_area_acres", "max"),
                )
                .reset_index()
            )

            # Round numeric columns for presentation
            num_cols = ["median_lot_size_ac", "mean_lot_size_ac", "min_lot_size_ac", "max_lot_size_ac"]
            grouped[num_cols] = grouped[num_cols].round(3)

            return grouped.sort_values(by="total_residential_parcels", ascending=False)


analytics_engine = AnalyticsEngine()


def print_analytical_results(enriched_gdf: gpd.GeoDataFrame):
    """Utility to print formatted tabular results to the terminal."""
    print("\n" + "=" * 80)
    print(" 🏙️ TAKE-HOME RESULTS: RESIDENTIAL PARCELS > 1 ACRE (Calculated from Geometry)")
    print("=" * 80)
    res_gt_1ac = analytics_engine.get_residential_parcels_gt_1ac(enriched_gdf)
    if not res_gt_1ac.empty:
        print(tabulate(res_gt_1ac, headers="keys", tablefmt="fancy_grid", showindex=False))
    else:
        print("No residential parcels found with lot size > 1 acre.")

    print("\n" + "=" * 80)
    print(" 📊 TAKE-HOME RESULTS: SUMMARY STATS BY AREA / SUBDIVISION")
    print("=" * 80)
    stats_df = analytics_engine.roll_up_stats_by_area(enriched_gdf)
    if not stats_df.empty:
        print(tabulate(stats_df, headers="keys", tablefmt="fancy_grid", showindex=False))
    else:
        print("No summary statistics available.")
    print("\n")
