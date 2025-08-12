"""
Tests for satellite comparator.
"""

from src.tracking.tle_parser import TLEParser, DEFAULT_TLES
from src.analysis.comparator import compare_satellites


class TestComparator:
    """Test satellite comparison tool."""

    def setup_method(self):
        parser = TLEParser()
        self.satellites = parser.parse_string(DEFAULT_TLES)

    def test_returns_list(self):
        """Should return a list of dicts."""
        results = compare_satellites(self.satellites)
        assert isinstance(results, list)
        assert len(results) == len(self.satellites)

    def test_has_required_fields(self):
        """Each result should have name, orbit_type, etc."""
        results = compare_satellites(self.satellites)

        for r in results:
            assert "name" in r
            assert "orbit_type" in r
            assert "period_min" in r
            assert "velocity_km_s" in r
            assert "coverage_km" in r

    def test_iss_is_leo(self):
        """ISS should be classified as LEO."""
        results = compare_satellites(self.satellites)
        iss = [r for r in results if "ISS" in r["name"]]
        assert len(iss) == 1
        assert iss[0]["orbit_type"] == "LEO"

    def test_gps_is_meo(self):
        """GPS should be classified as MEO."""
        results = compare_satellites(self.satellites)
        gps = [r for r in results if "GPS" in r["name"]]
        assert len(gps) == 1
        assert gps[0]["orbit_type"] == "MEO"

    def test_coverage_positive(self):
        """All coverage values should be positive."""
        results = compare_satellites(self.satellites)
        for r in results:
            assert r["coverage_km"] > 0
