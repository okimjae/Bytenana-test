import pytest
import geopandas as gpd
from shapely.geometry import Polygon
from src.spatial.geometry import geo_engine
from src.config import settings


def test_area_calculation_accuracy():
    """Validates that a 100x100 ft polygon yields exactly 10,000 sqft and 0.229568 acres."""
    poly = Polygon([(0, 0), (100, 0), (100, 100), (0, 100), (0, 0)])
    gdf = gpd.GeoDataFrame([{"geometry": poly}], crs="EPSG:2277")

    result = geo_engine.compute_lot_size_acres(gdf)
    assert result["calculated_area_sqft"].iloc[0] == pytest.approx(10000.0, rel=1e-5)
    assert result["calculated_area_acres"].iloc[0] == pytest.approx(10000.0 / 43560.0, rel=1e-5)


def test_point_on_surface_concave():
    """Validates that representative point for an L-shaped polygon falls inside the polygon."""
    l_poly = Polygon([(0, 0), (6, 0), (6, 2), (2, 2), (2, 6), (0, 6), (0, 0)])
    pt = geo_engine.get_point_on_surface(l_poly)
    assert l_poly.contains(pt)
