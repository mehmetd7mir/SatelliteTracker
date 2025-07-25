"""
Satellite Comparison Tool
---------------------------
Compare orbital properties of multiple satellites side by side.

Useful for understanding the differences between LEO, MEO, GEO orbits.

Author: Mehmet Demir
"""

from typing import List, Dict
from src.tracking.tle_parser import TLEParser, TLEData, DEFAULT_TLES
from src.utils.orbital import analyze_orbit, OrbitInfo, calculate_coverage_radius


def compare_satellites(satellites: List[TLEData]) -> List[Dict]:
    """
    Compare multiple satellites and return their properties.

    Args:
        satellites: list of TLEData objects

    Returns:
        list of dictionaries with satellite properties
    """
    results = []

    for sat in satellites:
        orbit = analyze_orbit(
            mean_motion=sat.mean_motion,
            eccentricity=sat.eccentricity,
            inclination=sat.inclination
        )

        avg_alt = (orbit.apogee_km + orbit.perigee_km) / 2.0
        coverage = calculate_coverage_radius(avg_alt)

        results.append({
            "name": sat.name,
            "norad_id": sat.norad_id,
            "orbit_type": orbit.orbit_type,
            "period_min": round(orbit.period_minutes, 1),
            "apogee_km": round(orbit.apogee_km, 1),
            "perigee_km": round(orbit.perigee_km, 1),
            "velocity_km_s": round(orbit.velocity_avg_km_s, 2),
            "inclination": round(sat.inclination, 2),
            "eccentricity": sat.eccentricity,
            "coverage_km": round(coverage, 1)
        })

    return results


def print_comparison(satellites: List[TLEData]):
    """Print formatted comparison table."""
    results = compare_satellites(satellites)

    # header
    print(f"{'Satellite':<20} {'Type':<5} {'Period':<10} {'Apogee':<10} "
          f"{'Perigee':<10} {'Velocity':<10} {'Incl.':<8}")
    print("-" * 85)

    for r in results:
        print(f"{r['name']:<20} {r['orbit_type']:<5} "
              f"{r['period_min']:<10} {r['apogee_km']:<10} "
              f"{r['perigee_km']:<10} {r['velocity_km_s']:<10} "
              f"{r['inclination']:<8}")


# test
if __name__ == "__main__":
    parser = TLEParser()
    sats = parser.parse_string(DEFAULT_TLES)

    print("Satellite Comparison\n")
    print_comparison(sats)
