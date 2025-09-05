"""
Tests for satellite comparator.
"""

from src.tracking.tle_parser import TLEParser, DEFAULT_TLES
from src.analysis.comparator import compare_satellites


class TestComparator:

    def setup_method(self):
        parser = TLEParser()
        self.satellites = parser.parse_string(DEFAULT_TLES)

    def test_returns_list(self):
        results = compare_satellites(self.satellites)
        assert isinstance(results, list)
        assert len(results) == len(self.satellites)

    def test_iss_is_leo(self):
        results = compare_satellites(self.satellites)
        iss = [r for r in results if "ISS" in r["name"]]
        assert iss[0]["orbit_type"] == "LEO"

    def test_gps_is_meo(self):
        results = compare_satellites(self.satellites)
        gps = [r for r in results if "GPS" in r["name"]]
        assert gps[0]["orbit_type"] == "MEO"
