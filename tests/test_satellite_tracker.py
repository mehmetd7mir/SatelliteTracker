"""
Tests for satellite tracker module.
"""

import pytest

try:
    from skyfield.api import load
    SKYFIELD_AVAILABLE = True
except ImportError:
    SKYFIELD_AVAILABLE = False

from src.tracking.satellite_tracker import SatelliteTracker, SatellitePosition


ISS_LINE1 = "1 25544U 98067A   24001.50000000  .00016717  00000-0  30000-3 0  9999"
ISS_LINE2 = "2 25544  51.6400 247.4627 0006703 170.5510 189.5640 15.49541000  1000"


@pytest.mark.skipif(not SKYFIELD_AVAILABLE, reason="skyfield not installed")
class TestSatelliteTracker:

    def setup_method(self):
        self.tracker = SatelliteTracker()
        self.tracker.add_satellite_from_tle("ISS", ISS_LINE1, ISS_LINE2)

    def test_add_satellite(self):
        assert "ISS" in self.tracker.satellites

    def test_get_position(self):
        pos = self.tracker.get_position("ISS")
        assert pos is not None
        assert -90 <= pos.latitude <= 90
        assert -180 <= pos.longitude <= 180

    def test_iss_altitude(self):
        pos = self.tracker.get_position("ISS")
        assert 200 < pos.altitude_km < 600

    def test_unknown_satellite(self):
        pos = self.tracker.get_position("DOES_NOT_EXIST")
        assert pos is None

    def test_ground_track(self):
        track = self.tracker.get_ground_track("ISS", duration_hours=0.5)
        assert track is not None
        assert len(track.latitudes) > 0
