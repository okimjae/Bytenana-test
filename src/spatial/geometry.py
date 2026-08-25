import geopandas as gpd
from shapely import Point, Polygon, MultiPolygon
from shapely.validation import make_valid
from src.config import settings
from src.observability.logger import logger


class GeospatialEngine:
    """Core geospatial operations: projection, geometry validation, and area computation."""

    @staticmethod
    def reproject_to_local_plane(
        gdf: gpd.GeoDataFrame,
        source_crs: str = settings.SOURCE_CRS,
        target_crs: str = settings.TARGET_CRS,
    ) -> gpd.GeoDataFrame:
        """Reprojects GeoDataFrame to local planar system (EPSG:2277) for true planar area calculation."""
        if gdf.crs is None:
            gdf = gdf.set_crs(source_crs)
        if gdf.crs.to_string() != target_crs:
            gdf = gdf.to_crs(target_crs)
        return gdf

    @staticmethod
    def sanitize_and_fix_geometries(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Repairs invalid geometries (e.g. self-intersecting rings) via make_valid."""
        gdf["geometry"] = gdf["geometry"].apply(lambda g: make_valid(g) if g is not None else None)
        # Drop empty geometries
        valid_mask = ~gdf["geometry"].is_empty & gdf["geometry"].notna()
        return gdf[valid_mask].copy()

    @staticmethod
    def compute_lot_size_acres(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Computes true planar area in square feet and converts to acres (1 ac = 43,560 sq ft)."""
        # Ensure CRS is EPSG:2277 (units in US survey feet)
        if gdf.crs is None or gdf.crs.to_string() != settings.TARGET_CRS:
            gdf = GeospatialEngine.reproject_to_local_plane(gdf)

        gdf["calculated_area_sqft"] = gdf["geometry"].area
        gdf["calculated_area_acres"] = gdf["calculated_area_sqft"] / settings.SQFT_PER_ACRE
        return gdf

    @staticmethod
    def get_point_on_surface(geom) -> Point:
        """Returns a guaranteed interior point for any polygon (including concave 'L' shapes)."""
        if geom is None or geom.is_empty:
            return None
        return geom.representative_point()


geo_engine = GeospatialEngine()
