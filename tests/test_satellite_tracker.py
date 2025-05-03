"""
Tests for satellite tracker module.

These tests need skyfield installed to run.
"""

import pytest
from datetime import datetime

# check if skyfield is available
try:
    from skyfield.api import load
    SKYFIELD_AVAILABLE = True
except ImportError:
    SKYFIELD_AVAILABLE = False

from src.tracking.satellite_tracker import SatelliteTracker, SatellitePosition


# ISS TLE for testing
ISS_LINE1 = "1 25544U 98067A   24001.50000000  .00016717  00000-0  30000-3 0  9999"
ISS_LINE2 = "2 25544  51.6400 247.4627 0006703 170.5510 189.5640 15.49541000  1000"


@pytest.mark.skipif(not SKYFIELD_AVAILABLE, reason="skyfield not installed")
class TestSatelliteTracker:
    """Test satellite tracking functions."""

    def setup_method(self):
        self.tracker = SatelliteTracker()
        self.tracker.add_satellite_from_tle("ISS", ISS_LINE1, ISS_LINE2)

    def test_add_satellite(self):
        """Should be able to add satellite from TLE."""
        assert "ISS" in self.tracker.satellites

    def test_add_multiple_satellites(self):
        """Should handle multiple satellites."""
        gps_line1 = "1 24876U 97035A   24001.50000000  .00000010  00000-0  10000-3 0  9999"
        gps_line2 = "2 24876  55.0000 100.0000 0050000 250.0000 100.0000  2.00562000  1000"
        self.tracker.add_satellite_from_tle("GPS", gps_line1, gps_line2)

        assert "ISS" in self.tracker.satellites
        assert "GPS" in self.tracker.satellites

    def test_get_position_returns_data(self):
        """Position should have lat, lon, alt."""
        pos = self.tracker.get_position("ISS")

        assert pos is not None
        assert isinstance(pos, SatellitePosition)

    def test_position_latitude_range(self):
        """Latitude should be between -90 and 90."""
        pos = self.tracker.get_position("ISS")
        assert -90 <= pos.latitude <= 90

    def test_position_longitude_range(self):
        """Longitude should be between -180 and 180."""
        pos = self.tracker.get_position("ISS")
        assert -180 <= pos.longitude <= 180

    def test_iss_altitude_range(self):
        """ISS altitude is around 400-420 km."""
        pos = self.tracker.get_position("ISS")
        # using old TLE data so prediction may drift
        # just check altitude is reasonable for LEO
        assert 200 < pos.altitude_km < 600

    def test_iss_velocity(self):
        """ISS velocity is about 7.66 km/s."""
        pos = self.tracker.get_position("ISS")
        # orbital velocity should be roughly 7-8 km/s
        assert 6.0 < pos.velocity_km_s < 9.0

    def test_position_has_timestamp(self):
        """Position should include a timestamp."""
        pos = self.tracker.get_position("ISS")
        assert pos.timestamp is not None

    def test_get_position_unknown_satellite(self):
        """Should return None for unknown satellite."""
        pos = self.tracker.get_position("DOES_NOT_EXIST")
        assert pos is None

    def test_get_all_positions(self):
        """Should return positions for all tracked satellites."""
        positions = self.tracker.get_all_positions()
        assert len(positions) >= 1

    def test_ground_track(self):
        """Ground track should return list of lat/lon points."""
        track = self.tracker.get_ground_track("ISS", duration_hours=0.5)

        assert track is not None
        assert len(track.latitudes) > 0
        assert len(track.latitudes) == len(track.longitudes)

    def test_ground_track_values_in_range(self):
        """All ground track points should be valid coordinates."""
        track = self.tracker.get_ground_track("ISS", duration_hours=0.5)

        for lat in track.latitudes:
            assert -90 <= lat <= 90
        for lon in track.longitudes:
            assert -180 <= lon <= 180

    def test_sunlit_is_boolean(self):
        """is_sunlit field should be True or False."""
        pos = self.tracker.get_position("ISS")
        assert pos.is_sunlit in (True, False)
