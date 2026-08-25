import geopandas as gpd
from shapely.geometry import Polygon
from tabulate import tabulate
from src.spatial.geometry import geo_engine
from src.spatial.classifier import zoning_classifier
from src.config import settings
from src.observability.logger import logger


class EvaluationHarness:
    """Automated evaluation suite validating geodesic precision, rule accuracy, and edge-cases."""

    def __init__(self):
        self.results = []

    def eval_geodesic_precision(self) -> dict:
        """Tests geometric area computation against a known synthetic ground-truth polygon."""
        # Square of 1,000 ft x 1,000 ft in EPSG:2277 coordinates
        # Expected sqft: 1,000,000. Expected acres: 1,000,000 / 43,560 = 22.95684113865932
        poly = Polygon([(0, 0), (1000, 0), (1000, 1000), (0, 1000), (0, 0)])
        gdf = gpd.GeoDataFrame([{"geometry": poly}], crs="EPSG:2277")

        computed_gdf = geo_engine.compute_lot_size_acres(gdf)
        computed_acres = computed_gdf["calculated_area_acres"].iloc[0]
        expected_acres = 1000000.0 / 43560.0

        diff = abs(computed_acres - expected_acres)
        passed = diff < 1e-6

        return {
            "eval_name": "Geodesic Area Precision (1000x1000 ft)",
            "expected": round(expected_acres, 6),
            "actual": round(computed_acres, 6),
            "status": "PASSED" if passed else "FAILED",
            "details": f"Absolute Error: {diff:.8f} acres",
        }

    def eval_zoning_regex_accuracy(self) -> dict:
        """Tests residential regex classification across 12 boundary test cases."""
        test_cases = [
            ("R-1", "Single Family", True),
            ("R-2", "Duplex", True),
            ("RM", "Multi-Family", True),
            ("Residential - Estates", None, True),
            ("RESIDENTIAL LOW", None, True),
            ("r-3", "Mobile Home", True),
            ("B-1", "Neighborhood Business", False),
            ("B-2", "Arterial Business", False),
            ("C-1", "Commercial", False),
            ("COMMERCIAL-R", "Commercial Retail", False), # Starts with 'C', not 'R'
            ("AG", "Agriculture", False),
            ("I-1", "Light Industrial", False),
        ]

        errors = []
        for code, name, expected in test_cases:
            res = zoning_classifier.is_residential(code, name)
            if res != expected:
                errors.append(f"Failed for code='{code}', name='{name}': got {res}, expected {expected}")

        passed = len(errors) == 0
        return {
            "eval_name": "Zoning Regex False-Positive / Negative Test",
            "expected": "100% Correct Match",
            "actual": f"{len(test_cases) - len(errors)}/{len(test_cases)} Passed",
            "status": "PASSED" if passed else "FAILED",
            "details": "; ".join(errors) if errors else "Zero false classifications",
        }

    def eval_concave_point_on_surface(self) -> dict:
        """Tests that concave 'L' shaped polygons yield an interior point."""
        # L-shaped polygon: centroid falls at (2.5, 2.5) which is OUTSIDE the geometry
        l_poly = Polygon([(0, 0), (6, 0), (6, 2), (2, 2), (2, 6), (0, 6), (0, 0)])
        point = geo_engine.get_point_on_surface(l_poly)
        
        is_inside = l_poly.contains(point)
        return {
            "eval_name": "Concave Polygon Point-on-Surface Interior Check",
            "expected": "Point strictly within polygon",
            "actual": "Inside" if is_inside else "Outside",
            "status": "PASSED" if is_inside else "FAILED",
            "details": f"Point coords: ({point.x:.2f}, {point.y:.2f})",
        }

    def run_all(self):
        print("\n" + "=" * 80)
        print(" 🧪 RUNNING AUTOMATED EVALUATION HARNESS (EVALS)")
        print("=" * 80)
        
        eval_results = [
            self.eval_geodesic_precision(),
            self.eval_zoning_regex_accuracy(),
            self.eval_concave_point_on_surface(),
        ]
        
        print(tabulate(eval_results, headers="keys", tablefmt="fancy_grid"))
        all_passed = all(r["status"] == "PASSED" for r in eval_results)
        print(f"\nFinal Eval Status: {'✅ ALL EVALS PASSED' if all_passed else '❌ EVALS FAILED'}\n")
        return all_passed


if __name__ == "__main__":
    harness = EvaluationHarness()
    harness.run_all()
