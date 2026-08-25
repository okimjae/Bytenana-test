import pytest
from src.spatial.classifier import zoning_classifier


@pytest.mark.parametrize(
    "code,name,expected",
    [
        ("R-1", "Single Family", True),
        ("R-2", "Two Family", True),
        ("RM", "Multi-Family", True),
        ("Residential Estates", None, True),
        ("residential - medium", None, True),
        ("B-1", "Business", False),
        ("C-2", "Commercial", False),
        ("COMMERCIAL-R", "Commercial Retail", False),
        ("AG", "Agriculture", False),
        ("I-1", "Industrial", False),
        (None, None, False),
    ],
)
def test_zoning_classifier_rules(code, name, expected):
    assert zoning_classifier.is_residential(code, name) == expected
