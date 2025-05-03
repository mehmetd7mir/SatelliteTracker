"""
Tests for TLE parser module.
"""

import pytest
from src.tracking.tle_parser import TLEParser, TLEData, DEFAULT_TLES


# sample TLE data for tests (ISS)
SAMPLE_NAME = "ISS (ZARYA)"
SAMPLE_LINE1 = "1 25544U 98067A   24001.50000000  .00016717  00000-0  30000-3 0  9999"
SAMPLE_LINE2 = "2 25544  51.6400 247.4627 0006703 170.5510 189.5640 15.49541000  1000"


class TestTLEParser:
    """Test TLE parsing functions."""

    def setup_method(self):
        self.parser = TLEParser()

    def test_parse_single_tle(self):
        """Parse one TLE and check basic fields."""
        tle = self.parser.parse_lines(SAMPLE_NAME, SAMPLE_LINE1, SAMPLE_LINE2)

        assert tle.name == SAMPLE_NAME
        assert tle.norad_id == 25544
        assert tle.line1 == SAMPLE_LINE1
        assert tle.line2 == SAMPLE_LINE2

    def test_norad_id_parsed_correctly(self):
        """NORAD ID should be integer from line1."""
        tle = self.parser.parse_lines(SAMPLE_NAME, SAMPLE_LINE1, SAMPLE_LINE2)
        assert isinstance(tle.norad_id, int)
        assert tle.norad_id == 25544

    def test_orbital_parameters(self):
        """Check that orbital elements are in valid range."""
        tle = self.parser.parse_lines(SAMPLE_NAME, SAMPLE_LINE1, SAMPLE_LINE2)

        # inclination should be between 0 and 180
        assert 0 <= tle.inclination <= 180
        # ISS is around 51.6 degrees
        assert 51.0 < tle.inclination < 52.0

        # eccentricity should be between 0 and 1
        assert 0 <= tle.eccentricity < 1

        # mean motion (revolutions per day), LEO is around 15
        assert tle.mean_motion > 0
        assert 14.0 < tle.mean_motion < 16.0

    def test_raan_range(self):
        """RAAN should be 0-360 degrees."""
        tle = self.parser.parse_lines(SAMPLE_NAME, SAMPLE_LINE1, SAMPLE_LINE2)
        assert 0 <= tle.raan <= 360

    def test_parse_multiple_tles(self):
        """Parse DEFAULT_TLES string with multiple satellites."""
        satellites = self.parser.parse_string(DEFAULT_TLES)

        # should have 3 satellites (ISS, Starlink, GPS)
        assert len(satellites) == 3

        # check names
        names = [s.name for s in satellites]
        assert "ISS (ZARYA)" in names
        assert "STARLINK-1007" in names
        assert "GPS BIIR-2" in names

    def test_gps_satellite_orbit(self):
        """GPS satellites have ~12 hour orbit (mean motion ~2)."""
        satellites = self.parser.parse_string(DEFAULT_TLES)
        gps = [s for s in satellites if "GPS" in s.name][0]

        # GPS mean motion is about 2 rev/day
        assert 1.5 < gps.mean_motion < 2.5
        # GPS inclination is about 55 degrees
        assert 50 < gps.inclination < 60

    def test_invalid_tle_format(self):
        """Should raise error for bad TLE lines."""
        with pytest.raises(ValueError):
            self.parser.parse_lines(
                "BAD SAT",
                "X invalid line",
                "Y also invalid"
            )

    def test_parse_empty_string(self):
        """Empty string should return empty list."""
        result = self.parser.parse_string("")
        assert result == []

    def test_tle_data_has_all_fields(self):
        """TLEData should have all required fields."""
        tle = self.parser.parse_lines(SAMPLE_NAME, SAMPLE_LINE1, SAMPLE_LINE2)

        # check that important fields exist and not None
        assert tle.classification is not None
        assert tle.epoch_year is not None
        assert tle.epoch_day > 0
        assert tle.arg_perigee is not None
        assert tle.mean_anomaly is not None

    def test_launch_year(self):
        """ISS launched in 1998, launch_year should be 98."""
        tle = self.parser.parse_lines(SAMPLE_NAME, SAMPLE_LINE1, SAMPLE_LINE2)
        assert tle.launch_year == 98

    def test_tle_sources_configured(self):
        """Parser should have celestrak URLs."""
        assert "celestrak" in self.parser.tle_sources
        assert "stations" in self.parser.tle_sources
