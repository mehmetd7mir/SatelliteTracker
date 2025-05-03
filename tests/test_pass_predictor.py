"""
Tests for pass predictor module.
"""

import pytest

try:
    from skyfield.api import load
    SKYFIELD_AVAILABLE = True
except ImportError:
    SKYFIELD_AVAILABLE = False

from src.prediction.pass_predictor import PassPredictor, SatellitePass


ISS_LINE1 = "1 25544U 98067A   24001.50000000  .00016717  00000-0  30000-3 0  9999"
ISS_LINE2 = "2 25544  51.6400 247.4627 0006703 170.5510 189.5640 15.49541000  1000"


@pytest.mark.skipif(not SKYFIELD_AVAILABLE, reason="skyfield not installed")
class TestPassPredictor:
    """Test satellite pass prediction."""

    def setup_method(self):
        # Istanbul coordinates
        self.predictor = PassPredictor(
            observer_lat=41.0,
            observer_lon=29.0,
            min_elevation=10.0
        )
        self.predictor.add_satellite("ISS", ISS_LINE1, ISS_LINE2)

    def test_predictor_creation(self):
        """Should create predictor with observer location."""
        assert self.predictor.observer_lat == 41.0
        assert self.predictor.observer_lon == 29.0

    def test_add_satellite(self):
        """Should be able to add satellite."""
        assert "ISS" in self.predictor.satellites

    def test_find_passes_returns_list(self):
        """find_passes should return a list."""
        passes = self.predictor.find_passes("ISS", days=1)
        assert isinstance(passes, list)

    def test_pass_has_required_fields(self):
        """Each pass should have AOS, LOS, max elevation."""
        passes = self.predictor.find_passes("ISS", days=3)

        if len(passes) > 0:
            p = passes[0]
            assert hasattr(p, 'aos_time')
            assert hasattr(p, 'los_time')
            assert hasattr(p, 'max_elevation_deg')
            assert hasattr(p, 'duration_seconds')

    def test_pass_max_elevation_positive(self):
        """Max elevation should be positive."""
        passes = self.predictor.find_passes("ISS", days=3)

        for p in passes:
            assert p.max_elevation_deg > 0

    def test_pass_duration_positive(self):
        """Duration should be positive number."""
        passes = self.predictor.find_passes("ISS", days=3)

        for p in passes:
            assert p.duration_seconds > 0

    def test_pass_azimuth_range(self):
        """Azimuth should be 0-360."""
        passes = self.predictor.find_passes("ISS", days=3)

        for p in passes:
            assert 0 <= p.aos_azimuth <= 360
            assert 0 <= p.los_azimuth <= 360

    def test_unknown_satellite_passes(self):
        """Should return empty list for unknown satellite."""
        passes = self.predictor.find_passes("UNKNOWN_SAT", days=1)
        assert passes == []
