"""
Tests for orbital mechanics utilities.
"""

import pytest
import numpy as np
from src.utils.orbital import (
    mean_motion_to_period,
    period_to_semi_major_axis,
    calculate_apogee_perigee,
    calculate_velocity,
    classify_orbit,
    analyze_orbit,
    calculate_ground_trace_shift,
    calculate_coverage_radius,
    calculate_eclipse_fraction,
    EARTH_RADIUS_KM
)


class TestPeriodCalculation:
    """Test orbital period calculations."""

    def test_iss_period(self):
        """ISS has ~92 minute period."""
        period = mean_motion_to_period(15.49)
        assert 90 < period < 95

    def test_gps_period(self):
        """GPS has ~12 hour (720 min) period."""
        period = mean_motion_to_period(2.0)
        assert 700 < period < 740

    def test_geo_period(self):
        """GEO satellite has ~24 hour period."""
        period = mean_motion_to_period(1.0)
        assert 1430 < period < 1450

    def test_zero_motion_raises(self):
        """Zero mean motion should raise error."""
        with pytest.raises(ValueError):
            mean_motion_to_period(0)

    def test_negative_motion_raises(self):
        """Negative mean motion should raise error."""
        with pytest.raises(ValueError):
            mean_motion_to_period(-5.0)


class TestSemiMajorAxis:
    """Test semi-major axis calculation."""

    def test_iss_altitude(self):
        """ISS semi-major axis ~6770 km."""
        period = mean_motion_to_period(15.49)
        sma = period_to_semi_major_axis(period)
        # ISS is at ~400 km altitude, so SMA = 6371 + 400
        assert 6700 < sma < 6900

    def test_gps_altitude(self):
        """GPS semi-major axis ~26560 km."""
        period = mean_motion_to_period(2.0)
        sma = period_to_semi_major_axis(period)
        assert 26000 < sma < 27000


class TestApogeePerigee:
    """Test apogee and perigee calculation."""

    def test_circular_orbit(self):
        """Circular orbit (e=0): apogee == perigee."""
        apogee, perigee = calculate_apogee_perigee(7000, 0.0)
        assert abs(apogee - perigee) < 0.01

    def test_elliptical_orbit(self):
        """Elliptical orbit: apogee > perigee."""
        apogee, perigee = calculate_apogee_perigee(7000, 0.1)
        assert apogee > perigee

    def test_altitudes_positive(self):
        """Both altitudes should be positive for normal orbits."""
        apogee, perigee = calculate_apogee_perigee(7000, 0.01)
        assert apogee > 0
        assert perigee > 0


class TestOrbitClassification:
    """Test orbit type classification."""

    def test_leo(self):
        assert classify_orbit(400) == "LEO"

    def test_meo(self):
        assert classify_orbit(20000) == "MEO"

    def test_geo(self):
        assert classify_orbit(35786) == "GEO"

    def test_heo(self):
        assert classify_orbit(40000) == "HEO"

    def test_leo_boundary(self):
        assert classify_orbit(1999) == "LEO"


class TestAnalyzeOrbit:
    """Test the full orbit analysis function."""

    def test_iss_orbit(self):
        """ISS should be LEO."""
        info = analyze_orbit(15.49, 0.0007, 51.64)
        assert info.is_leo is True
        assert info.orbit_type == "LEO"
        assert 90 < info.period_minutes < 95

    def test_gps_orbit(self):
        """GPS should be MEO."""
        info = analyze_orbit(2.0, 0.005, 55.0)
        assert info.is_meo is True
        assert info.orbit_type == "MEO"

    def test_velocity_reasonable(self):
        """LEO velocity should be around 7-8 km/s."""
        info = analyze_orbit(15.49, 0.0007)
        assert 7.0 < info.velocity_avg_km_s < 8.0


class TestGroundTraceShift:
    """Test ground trace shift calculation."""

    def test_iss_shift(self):
        """ISS shifts about 23 degrees per orbit."""
        shift = calculate_ground_trace_shift(92.5)
        assert 22 < shift < 24

    def test_geo_no_shift(self):
        """GEO satellite should shift ~360 deg (stays same spot)."""
        shift = calculate_ground_trace_shift(1436)
        assert abs(shift - 360) < 1


class TestCoverageRadius:
    """Test coverage radius calculation."""

    def test_iss_coverage(self):
        """ISS coverage radius should be reasonable."""
        radius = calculate_coverage_radius(400)
        assert radius > 0
        assert radius < 3000  # shouldn't cover half the earth

    def test_higher_orbit_wider(self):
        """Higher orbit = wider coverage."""
        low = calculate_coverage_radius(400)
        high = calculate_coverage_radius(20000)
        assert high > low

    def test_zero_altitude(self):
        """Zero altitude = zero coverage."""
        radius = calculate_coverage_radius(0)
        assert radius == 0.0


class TestEclipseFraction:
    """Test eclipse fraction calculation."""

    def test_fraction_between_0_and_1(self):
        """Eclipse fraction should be between 0 and 1."""
        frac = calculate_eclipse_fraction(7000, 51.6)
        assert 0 < frac < 1

    def test_higher_orbit_less_eclipse(self):
        """Higher orbit should have less eclipse."""
        low = calculate_eclipse_fraction(7000, 0)
        high = calculate_eclipse_fraction(42000, 0)
        assert high < low
