import pytest
import geopandas as gpd
from shapely.geometry import Polygon
from src.analytics.queries import analytics_engine


def test_residential_gt_1ac_filtering():
    """Validates that only residential parcels with lot size > 1 acre are selected."""
    data = [
        # Residential > 1 acre -> MUST INCLUDE
        {
            "parcel_id": "P1",
            "subdivision": "SubA",
            "zone_code": "R-1",
            "zone_name": "Single Family",
            "is_residential": True,
            "calculated_area_acres": 2.5,
            "legal_description": "Desc 1",
            "geometry": Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]),
        },
        # Residential < 1 acre -> MUST EXCLUDE
        {
            "parcel_id": "P2",
            "subdivision": "SubA",
            "zone_code": "R-1",
            "zone_name": "Single Family",
            "is_residential": True,
            "calculated_area_acres": 0.5,
            "legal_description": "Desc 2",
            "geometry": Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]),
        },
        # Commercial > 1 acre -> MUST EXCLUDE
        {
            "parcel_id": "P3",
            "subdivision": "SubB",
            "zone_code": "C-1",
            "zone_name": "Commercial",
            "is_residential": False,
            "calculated_area_acres": 5.0,
            "legal_description": "Desc 3",
            "geometry": Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]),
        },
    ]
    gdf = gpd.GeoDataFrame(data)
    result = analytics_engine.get_residential_parcels_gt_1ac(gdf)

    assert len(result) == 1
    assert result["parcel_id"].iloc[0] == "P1"
    assert result["calculated_area_acres"].iloc[0] == 2.5


def test_roll_up_stats_calculation():
    """Validates median and count aggregation by subdivision."""
    data = [
        {"parcel_id": "P1", "subdivision": "SubA", "is_residential": True, "calculated_area_acres": 1.0, "geometry": Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])},
        {"parcel_id": "P2", "subdivision": "SubA", "is_residential": True, "calculated_area_acres": 3.0, "geometry": Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])},
        {"parcel_id": "P3", "subdivision": "SubA", "is_residential": True, "calculated_area_acres": 5.0, "geometry": Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])},
    ]
    gdf = gpd.GeoDataFrame(data)
    stats = analytics_engine.roll_up_stats_by_area(gdf)

    assert len(stats) == 1
    assert stats["total_residential_parcels"].iloc[0] == 3
    assert stats["median_lot_size_ac"].iloc[0] == 3.0  # Median of 1.0, 3.0, 5.0 is 3.0
