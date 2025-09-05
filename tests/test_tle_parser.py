"""
Tests for TLE parser module.
"""

import pytest
from src.tracking.tle_parser import TLEParser, TLEData, DEFAULT_TLES


SAMPLE_NAME = "ISS (ZARYA)"
SAMPLE_LINE1 = "1 25544U 98067A   24001.50000000  .00016717  00000-0  30000-3 0  9999"
SAMPLE_LINE2 = "2 25544  51.6400 247.4627 0006703 170.5510 189.5640 15.49541000  1000"


class TestTLEParser:

    def setup_method(self):
        self.parser = TLEParser()

    def test_parse_single_tle(self):
        tle = self.parser.parse_lines(SAMPLE_NAME, SAMPLE_LINE1, SAMPLE_LINE2)
        assert tle.name == SAMPLE_NAME
        assert tle.norad_id == 25544

    def test_orbital_parameters(self):
        tle = self.parser.parse_lines(SAMPLE_NAME, SAMPLE_LINE1, SAMPLE_LINE2)
        assert 0 <= tle.inclination <= 180
        assert 0 <= tle.eccentricity < 1
        assert tle.mean_motion > 0

    def test_parse_multiple_tles(self):
        satellites = self.parser.parse_string(DEFAULT_TLES)
        assert len(satellites) == 3

    def test_invalid_tle_format(self):
        with pytest.raises(ValueError):
            self.parser.parse_lines("BAD", "X invalid", "Y invalid")

    def test_parse_empty_string(self):
        result = self.parser.parse_string("")
        assert result == []
