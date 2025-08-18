# SatelliteTracker - Architecture

## Overview

This project tracks satellites in real-time using TLE data and the Skyfield library.

## Data Flow

```
CelesTrak API  ──→  TLE Parser  ──→  Satellite Tracker  ──→  Dashboard
                                           │
   Local TLE  ────→                        ├──→  3D Globe
                                           └──→  Pass Predictor
```

## Modules

### `src/tracking/`
- **tle_parser.py** - Parses Two-Line Element (TLE) data. Supports fetching from CelesTrak API or loading from local files. Extracts all orbital elements.
- **satellite_tracker.py** - Calculates real-time satellite position using Skyfield's SGP4 propagator. Provides latitude, longitude, altitude, velocity, and sunlit status.

### `src/prediction/`
- **pass_predictor.py** - Predicts when a satellite will be visible from a ground location. Calculates AOS (rise), LOS (set), maximum elevation, and duration.

### `src/visualization/`
- **globe.py** - Interactive 3D Earth visualization using Plotly. Shows satellite positions and ground tracks on a globe.
- **dashboard.py** - Streamlit web dashboard for interactive satellite tracking. Includes map view, orbit info, and TLE details.

### `src/utils/`
- **orbital.py** - Orbital mechanics calculations using Kepler's laws. Computes period, semi-major axis, apogee/perigee, orbital velocity, coverage radius, and eclipse fraction.

### `src/analysis/`
- **comparator.py** - Compare orbital properties of multiple satellites side by side.

## Key Libraries

| Library | Purpose |
|---------|---------|
| **Skyfield** | SGP4 orbit propagation, position calculation |
| **NumPy** | Numerical computations |
| **Plotly** | 3D globe visualization |
| **Streamlit** | Web dashboard |
| **Pandas** | Data handling for ground tracks |

## Orbital Mechanics

The project uses these fundamental equations:

- **Kepler's Third Law**: T² = (4π²/μ) × a³
- **Vis-viva equation**: v = √(μ/a)
- **Apogee/Perigee**: a(1±e) - R_earth

Where μ is Earth's gravitational parameter and a is the semi-major axis.
