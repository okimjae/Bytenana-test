import pytest
from shapely.geometry import Polygon
from src.ingestion.sanitizer import sanitizer
from src.config import settings


def test_texas_bounds_sanitization():
    """Validates that coordinates inside Texas are accepted and outside coordinates are rejected."""
    # Austin / Buda coordinates (Lon: -97.84, Lat: 30.08) -> Inside Texas
    inside_poly = Polygon([(-97.85, 30.08), (-97.84, 30.08), (-97.84, 30.09), (-97.85, 30.09), (-97.85, 30.08)])
    assert sanitizer.is_within_texas_bounds(inside_poly) is True

    # London coordinates (Lon: 0.12, Lat: 51.50) -> Outside Texas
    outside_poly = Polygon([(0.10, 51.50), (0.12, 51.50), (0.12, 51.52), (0.10, 51.52), (0.10, 51.50)])
    assert sanitizer.is_within_texas_bounds(outside_poly) is False


def test_vertex_count_security_guard():
    """Validates rejection of anomalous high-vertex polygons (Geom Bomb attack prevention)."""
    # Simple polygon
    simple_poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])
    assert sanitizer.validate_vertex_count(simple_poly) is True
