from shapely.geometry.base import BaseGeometry
from src.config import settings
from src.observability.logger import logger


class SecuritySanitizer:
    """Security guardrails preventing Geom-Bombs and malformed inputs."""

    @staticmethod
    def is_within_texas_bounds(geom: BaseGeometry) -> bool:
        """Validates if geometry bounding box falls strictly within Texas geographical limits."""
        minx, miny, maxx, maxy = geom.bounds
        bounds = settings.TEXAS_BOUNDS
        # In EPSG:4326 (Lon, Lat)
        if (
            minx < bounds["min_lon"]
            or maxx > bounds["max_lon"]
            or miny < bounds["min_lat"]
            or maxy > bounds["max_lat"]
        ):
            return False
        return True

    @staticmethod
    def validate_vertex_count(geom: BaseGeometry) -> bool:
        """Protects against Denial-of-Service / Memory Exhaustion via high vertex complexity."""
        num_coords = 0
        if geom.geom_type == "Polygon":
            num_coords = len(geom.exterior.coords)
            for interior in geom.interiors:
                num_coords += len(interior.coords)
        elif geom.geom_type == "MultiPolygon":
            for poly in geom.geoms:
                num_coords += len(poly.exterior.coords)
                for interior in poly.interiors:
                    num_coords += len(interior.coords)

        if num_coords > settings.MAX_GEOM_VERTICES:
            logger.warning(
                f"Geometry rejected: vertex count ({num_coords}) exceeds limit ({settings.MAX_GEOM_VERTICES})"
            )
            return False
        return True


sanitizer = SecuritySanitizer()
