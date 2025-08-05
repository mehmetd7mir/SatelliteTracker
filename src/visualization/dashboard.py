"""
SatelliteTracker - Streamlit Dashboard
-----------------------------------------
Interactive web dashboard for tracking satellites.

Run with:
    streamlit run src/visualization/dashboard.py

Author: Mehmet Demir
"""

import sys
import os

# add project root to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

import numpy as np
from datetime import datetime

from src.tracking.tle_parser import TLEParser, DEFAULT_TLES
from src.tracking.satellite_tracker import SatelliteTracker, SKYFIELD_AVAILABLE
from src.utils.orbital import analyze_orbit


def setup_page():
    """Configure streamlit page."""
    st.set_page_config(
        page_title="SatelliteTracker",
        page_icon="🛰️",
        layout="wide"
    )
    st.title("🛰️ SatelliteTracker Dashboard")
    st.markdown("Real-time satellite tracking and orbit analysis")


def load_satellites(use_offline=True):
    """Load satellite data from TLE."""
    parser = TLEParser()

    if use_offline:
        satellites = parser.parse_string(DEFAULT_TLES)
    else:
        satellites = parser.fetch_from_celestrak("stations")
        if not satellites:
            satellites = parser.parse_string(DEFAULT_TLES)

    return satellites


def show_satellite_info(tracker, sat_name, tle_data):
    """Display satellite position and orbit info."""

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Current Position")
        pos = tracker.get_position(sat_name)

        if pos:
            st.metric("Latitude", f"{pos.latitude:.4f}°")
            st.metric("Longitude", f"{pos.longitude:.4f}°")
            st.metric("Altitude", f"{pos.altitude_km:.1f} km")
            st.metric("Velocity", f"{pos.velocity_km_s:.2f} km/s")

            if pos.is_sunlit:
                st.success("☀️ Sunlit")
            else:
                st.info("🌑 In shadow")
        else:
            st.error("Could not get position")

    with col2:
        st.subheader("Orbit Info")
        orbit = analyze_orbit(
            mean_motion=tle_data.mean_motion,
            eccentricity=tle_data.eccentricity,
            inclination=tle_data.inclination
        )

        st.metric("Orbit Type", orbit.orbit_type)
        st.metric("Period", f"{orbit.period_minutes:.1f} min")
        st.metric("Apogee", f"{orbit.apogee_km:.1f} km")
        st.metric("Perigee", f"{orbit.perigee_km:.1f} km")
        st.metric("Semi-major Axis", f"{orbit.semi_major_axis_km:.1f} km")


def show_ground_track(tracker, sat_name):
    """Show ground track on a map."""
    st.subheader("Ground Track")

    hours = st.slider("Track duration (hours)", 0.5, 6.0, 1.5, 0.5)

    track = tracker.get_ground_track(sat_name, duration_hours=hours)

    if track and len(track.latitudes) > 0:
        # make data for streamlit map
        import pandas as pd

        df = pd.DataFrame({
            "lat": track.latitudes,
            "lon": track.longitudes
        })

        st.map(df, zoom=1)
        st.caption(f"Ground track: {len(track.latitudes)} points over {hours} hours")
    else:
        st.warning("Could not generate ground track")


def show_tle_details(tle_data):
    """Show raw TLE data and orbital elements."""
    st.subheader("📋 TLE Data")

    with st.expander("View raw TLE"):
        st.code(f"{tle_data.name}\n{tle_data.line1}\n{tle_data.line2}")

    # orbital elements in a nice table
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Orbital Elements**")
        st.text(f"Inclination: {tle_data.inclination:.4f}°")
        st.text(f"RAAN: {tle_data.raan:.4f}°")
        st.text(f"Eccentricity: {tle_data.eccentricity:.7f}")

    with col2:
        st.markdown("**More Elements**")
        st.text(f"Arg. Perigee: {tle_data.arg_perigee:.4f}°")
        st.text(f"Mean Anomaly: {tle_data.mean_anomaly:.4f}°")
        st.text(f"Mean Motion: {tle_data.mean_motion:.4f} rev/day")

    with col3:
        st.markdown("**Identification**")
        st.text(f"NORAD ID: {tle_data.norad_id}")
        st.text(f"Classification: {tle_data.classification}")
        st.text(f"Rev Number: {tle_data.rev_number}")


def main():
    """Main dashboard function."""
    if not STREAMLIT_AVAILABLE:
        print("Streamlit not installed. Run: pip install streamlit")
        return

    if not SKYFIELD_AVAILABLE:
        st.error("Skyfield not installed! Run: pip install skyfield")
        return

    setup_page()

    # sidebar controls
    st.sidebar.header("⚙️ Settings")
    use_offline = st.sidebar.checkbox("Use offline data", value=True)

    # load satellites
    satellites = load_satellites(use_offline)

    if not satellites:
        st.error("No satellite data loaded")
        return

    # select satellite
    sat_names = [s.name for s in satellites]
    selected_name = st.sidebar.selectbox("Select Satellite", sat_names)

    # find selected satellite data
    selected_tle = None
    for s in satellites:
        if s.name == selected_name:
            selected_tle = s
            break

    if not selected_tle:
        st.error("Satellite not found")
        return

    # create tracker and add satellite
    tracker = SatelliteTracker()
    tracker.add_satellite_from_tle(
        selected_tle.name,
        selected_tle.line1,
        selected_tle.line2
    )

    # show info
    show_satellite_info(tracker, selected_tle.name, selected_tle)
    st.divider()

    # show ground track
    show_ground_track(tracker, selected_tle.name)
    st.divider()

    # show TLE details
    show_tle_details(selected_tle)

    # footer
    st.divider()
    st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")


if __name__ == "__main__":
    if not STREAMLIT_AVAILABLE:
        print("Run with: streamlit run src/visualization/dashboard.py")
    else:
        main()
