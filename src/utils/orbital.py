"""
Orbital Mechanics Utilities
-----------------------------
Basic orbital calculations using Kepler's laws.

Nothing too fancy here, just the fundamental equations
for calculating orbit properties from TLE parameters.

Author: Mehmet Demir
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional


# earth constants
EARTH_RADIUS_KM = 6371.0
EARTH_MU = 398600.4418  # gravitational parameter (km^3/s^2)
EARTH_J2 = 1.08263e-3   # J2 perturbation coefficient


@dataclass
class OrbitInfo:
    """Calculated orbit properties."""
    semi_major_axis_km: float
    period_minutes: float
    apogee_km: float      # highest point (altitude)
    perigee_km: float      # lowest point (altitude)
    velocity_avg_km_s: float
    is_leo: bool           # low earth orbit
    is_meo: bool           # medium earth orbit
    is_geo: bool           # geostationary orbit
    orbit_type: str


def mean_motion_to_period(mean_motion_rev_day: float) -> float:
    """
    Convert mean motion (rev/day) to orbital period (minutes).

    Mean motion is how many times satellite goes around Earth per day.
    So period is just 1440 / mean_motion (1440 = minutes in a day).
    """
    if mean_motion_rev_day <= 0:
        raise ValueError("mean motion must be positive")

    return 1440.0 / mean_motion_rev_day


def period_to_semi_major_axis(period_minutes: float) -> float:
    """
    Calculate semi-major axis from period using Kepler's third law.

    T^2 = (4 * pi^2 / mu) * a^3
    so: a = (mu * T^2 / (4 * pi^2))^(1/3)
    """
    period_seconds = period_minutes * 60.0
    a_cubed = EARTH_MU * (period_seconds ** 2) / (4 * np.pi ** 2)
    return a_cubed ** (1.0 / 3.0)


def calculate_apogee_perigee(
    semi_major_axis_km: float,
    eccentricity: float
) -> tuple:
    """
    Calculate apogee and perigee altitudes.

    apogee = a * (1 + e) - R_earth  (highest point)
    perigee = a * (1 - e) - R_earth  (lowest point)
    """
    apogee = semi_major_axis_km * (1 + eccentricity) - EARTH_RADIUS_KM
    perigee = semi_major_axis_km * (1 - eccentricity) - EARTH_RADIUS_KM
    return apogee, perigee


def calculate_velocity(semi_major_axis_km: float) -> float:
    """
    Average orbital velocity using vis-viva equation (circular approx).

    v = sqrt(mu / a)
    """
    return np.sqrt(EARTH_MU / semi_major_axis_km)


def classify_orbit(altitude_km: float) -> str:
    """
    Classify orbit based on average altitude.

    LEO: 160 - 2000 km (ISS, most satellites)
    MEO: 2000 - 35786 km (GPS, navigation)
    GEO: ~35786 km (communication, weather)
    HEO: highly elliptical
    """
    if altitude_km < 2000:
        return "LEO"
    elif altitude_km < 35000:
        return "MEO"
    elif 35000 <= altitude_km <= 36500:
        return "GEO"
    else:
        return "HEO"


def analyze_orbit(
    mean_motion: float,
    eccentricity: float,
    inclination: float = 0.0
) -> OrbitInfo:
    """
    Calculate all orbit properties from TLE parameters.

    This takes the raw values from a TLE and gives you
    all the useful orbit information.

    Args:
        mean_motion: revolutions per day
        eccentricity: orbit eccentricity (0 = circular, 1 = escape)
        inclination: orbit inclination in degrees

    Returns:
        OrbitInfo with all calculated properties
    """
    period = mean_motion_to_period(mean_motion)
    semi_major = period_to_semi_major_axis(period)
    apogee, perigee = calculate_apogee_perigee(semi_major, eccentricity)
    velocity = calculate_velocity(semi_major)

    # average altitude for classification
    avg_altitude = (apogee + perigee) / 2.0
    orbit_type = classify_orbit(avg_altitude)

    return OrbitInfo(
        semi_major_axis_km=semi_major,
        period_minutes=period,
        apogee_km=apogee,
        perigee_km=perigee,
        velocity_avg_km_s=velocity,
        is_leo=(orbit_type == "LEO"),
        is_meo=(orbit_type == "MEO"),
        is_geo=(orbit_type == "GEO"),
        orbit_type=orbit_type
    )


def calculate_ground_trace_shift(period_minutes: float) -> float:
    """
    How much the ground track shifts west per orbit.

    Earth rotates 360 degrees in ~1436 minutes (sidereal day).
    So each orbit, the ground track shifts by:
        shift = 360 * period / 1436 degrees
    """
    sidereal_day_minutes = 1436.07
    return 360.0 * period_minutes / sidereal_day_minutes


def calculate_coverage_radius(altitude_km: float) -> float:
    """
    Estimate the coverage radius on Earth surface (footprint).

    Simple geometric calculation:
    radius = R_earth * arccos(R_earth / (R_earth + alt))
    """
    ratio = EARTH_RADIUS_KM / (EARTH_RADIUS_KM + altitude_km)
    if ratio >= 1.0:
        return 0.0
    angle_rad = np.arccos(ratio)
    return EARTH_RADIUS_KM * angle_rad


def calculate_eclipse_fraction(
    semi_major_axis_km: float,
    inclination_deg: float
) -> float:
    """
    Estimate fraction of orbit spent in Earth's shadow.

    This is a simplified version that assumes circular orbit.
    Real calculation needs sun position but this gives rough estimate.
    """
    # angular size of Earth as seen from orbit
    sin_rho = EARTH_RADIUS_KM / semi_major_axis_km
    if sin_rho >= 1.0:
        return 1.0
    rho = np.arcsin(sin_rho)

    # fraction in shadow (simplified)
    eclipse_fraction = rho / np.pi
    return eclipse_fraction


# quick test
if __name__ == "__main__":
    # ISS orbit: mean motion ~15.5 rev/day, eccentricity ~0.0007
    info = analyze_orbit(
        mean_motion=15.49,
        eccentricity=0.0007,
        inclination=51.64
    )

    print("ISS Orbit Analysis:")
    print(f"  Type: {info.orbit_type}")
    print(f"  Period: {info.period_minutes:.1f} min")
    print(f"  Semi-major axis: {info.semi_major_axis_km:.1f} km")
    print(f"  Apogee: {info.apogee_km:.1f} km")
    print(f"  Perigee: {info.perigee_km:.1f} km")
    print(f"  Velocity: {info.velocity_avg_km_s:.2f} km/s")

    # GPS orbit
    print("\nGPS Orbit Analysis:")
    gps = analyze_orbit(mean_motion=2.0056, eccentricity=0.005)
    print(f"  Type: {gps.orbit_type}")
    print(f"  Period: {gps.period_minutes:.1f} min")
    print(f"  Altitude: {(gps.apogee_km + gps.perigee_km)/2:.0f} km")
