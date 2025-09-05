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

    def setup_method(self):
        self.predictor = PassPredictor(
            observer_lat=41.0, observer_lon=29.0, min_elevation=10.0
        )
        self.predictor.add_satellite("ISS", ISS_LINE1, ISS_LINE2)

    def test_predictor_creation(self):
        assert self.predictor.observer_lat == 41.0

    def test_find_passes(self):
        passes = self.predictor.find_passes("ISS", days=1)
        assert isinstance(passes, list)

    def test_unknown_satellite(self):
        passes = self.predictor.find_passes("UNKNOWN_SAT", days=1)
        assert passes == []
