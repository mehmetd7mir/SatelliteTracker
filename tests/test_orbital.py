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
    calculate_coverage_radius,
)


def test_iss_period():
    period = mean_motion_to_period(15.49)
    assert 90 < period < 95


def test_gps_period():
    period = mean_motion_to_period(2.0)
    assert 700 < period < 740


def test_zero_motion_raises():
    with pytest.raises(ValueError):
        mean_motion_to_period(0)


def test_iss_altitude():
    period = mean_motion_to_period(15.49)
    sma = period_to_semi_major_axis(period)
    assert 6700 < sma < 6900


def test_circular_orbit():
    apogee, perigee = calculate_apogee_perigee(7000, 0.0)
    assert abs(apogee - perigee) < 0.01


def test_orbit_classification():
    assert classify_orbit(400) == "LEO"
    assert classify_orbit(20000) == "MEO"
    assert classify_orbit(35786) == "GEO"


def test_iss_orbit_analysis():
    info = analyze_orbit(15.49, 0.0007, 51.64)
    assert info.orbit_type == "LEO"
    assert 7.0 < info.velocity_avg_km_s < 8.0


def test_coverage_higher_wider():
    low = calculate_coverage_radius(400)
    high = calculate_coverage_radius(20000)
    assert high > low
