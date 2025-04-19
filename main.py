"""
SatelliteTracker - Main Entry Point
-------------------------------------
Track satellites in real-time and visualize them.

Usage:
    python main.py                    # track ISS
    python main.py --satellite GPS    # track GPS satellites
    python main.py --list            # list available categories
    
Author: Mehmet Demir
"""

import argparse
from datetime import datetime

# import our modules
from src.tracking.tle_parser import TLEParser, DEFAULT_TLES
from src.tracking.satellite_tracker import SatelliteTracker, SKYFIELD_AVAILABLE
from src.prediction.pass_predictor import PassPredictor


def main():
    parser = argparse.ArgumentParser(
        description="Real-time Satellite Tracking System"
    )
    parser.add_argument(
        "--satellite", "-s",
        type=str,
        default="ISS",
        help="Satellite name to track (default: ISS)"
    )
    parser.add_argument(
        "--category", "-c",
        type=str,
        default="stations",
        help="CelesTrak category (stations, starlink, gps)"
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use offline sample data"
    )
    parser.add_argument(
        "--passes",
        action="store_true",
        help="Show upcoming passes"
    )
    parser.add_argument(
        "--lat",
        type=float,
        default=41.0,
        help="Observer latitude (default: Istanbul 41.0)"
    )
    parser.add_argument(
        "--lon",
        type=float,
        default=29.0,
        help="Observer longitude (default: Istanbul 29.0)"
    )
    parser.add_argument(
        "--visualize", "-v",
        action="store_true",
        help="Show 3D visualization"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available satellite categories"
    )
    
    args = parser.parse_args()
    
    # list categories
    if args.list:
        print("Available CelesTrak categories:")
        print("  - stations (ISS, Tiangong, etc)")
        print("  - starlink (SpaceX Starlink)")
        print("  - gps (GPS satellites)")
        print("  - weather (Weather satellites)")
        print("  - science (Science missions)")
        return
    
    print("="*50)
    print("  SatelliteTracker")
    print("  Real-time Satellite Tracking System")
    print("="*50)
    print()
    
    # check dependencies
    if not SKYFIELD_AVAILABLE:
        print("[ERROR] Skyfield not installed!")
        print("Run: pip install skyfield")
        return
    
    # load TLE data
    tle_parser = TLEParser()
    
    if args.offline:
        print("[INFO] Using offline sample data...")
        satellites = tle_parser.parse_string(DEFAULT_TLES)
    else:
        print(f"[INFO] Fetching TLE data from CelesTrak ({args.category})...")
        satellites = tle_parser.fetch_from_celestrak(args.category)
    
    if not satellites:
        print("[WARNING] No satellites loaded, using offline data")
        satellites = tle_parser.parse_string(DEFAULT_TLES)
    
    print(f"[OK] Loaded {len(satellites)} satellites")
    print()
    
    # find requested satellite
    target_sat = None
    for sat in satellites:
        if args.satellite.upper() in sat.name.upper():
            target_sat = sat
            break
    
    if not target_sat:
        print(f"[ERROR] Satellite '{args.satellite}' not found")
        print("Available satellites:")
        for sat in satellites[:10]:
            print(f"  - {sat.name}")
        return
    
    print(f"Tracking: {target_sat.name}")
    print(f"NORAD ID: {target_sat.norad_id}")
    print()
    
    # create tracker
    tracker = SatelliteTracker()
    tracker.add_satellite_from_tle(
        target_sat.name,
        target_sat.line1,
        target_sat.line2
    )
    
    # get current position
    pos = tracker.get_position(target_sat.name)
    
    if pos:
        print("Current Position:")
        print(f"  Latitude:  {pos.latitude:.4f} deg")
        print(f"  Longitude: {pos.longitude:.4f} deg")
        print(f"  Altitude:  {pos.altitude_km:.2f} km")
        print(f"  Velocity:  {pos.velocity_km_s:.2f} km/s")
        print(f"  Sunlit:    {'Yes' if pos.is_sunlit else 'No'}")
        print(f"  Time:      {pos.timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print()
    
    # show passes if requested
    if args.passes:
        print(f"Upcoming passes over ({args.lat}, {args.lon}):")
        print()
        
        predictor = PassPredictor(
            observer_lat=args.lat,
            observer_lon=args.lon,
            min_elevation=10.0
        )
        predictor.add_satellite(
            target_sat.name,
            target_sat.line1,
            target_sat.line2
        )
        
        passes = predictor.find_passes(target_sat.name, days=3)
        
        if passes:
            for i, p in enumerate(passes[:5]):
                print(f"Pass {i+1}:")
                print(f"  Rise:     {p.aos_time.strftime('%Y-%m-%d %H:%M')} (Az: {p.aos_azimuth:.0f})")
                print(f"  Max:      {p.max_elevation_time.strftime('%H:%M')} (El: {p.max_elevation_deg:.1f})")
                print(f"  Set:      {p.los_time.strftime('%H:%M')} (Az: {p.los_azimuth:.0f})")
                print(f"  Duration: {p.duration_seconds/60:.1f} min")
                print()
        else:
            print("  No passes found in next 3 days")
    
    # visualize if requested
    if args.visualize:
        try:
            from src.visualization.globe import GlobeVisualizer
            
            print("Creating 3D visualization...")
            
            viz = GlobeVisualizer()
            
            # add satellite
            if pos:
                viz.add_satellite(
                    target_sat.name,
                    pos.latitude,
                    pos.longitude,
                    pos.altitude_km
                )
            
            # add ground track
            track = tracker.get_ground_track(target_sat.name, duration_hours=1.5)
            if track:
                viz.add_ground_track(
                    track.latitudes,
                    track.longitudes,
                    f"{target_sat.name} Track"
                )
            
            # add observer location
            viz.add_location("Observer", args.lat, args.lon)
            
            viz.show(f"Tracking: {target_sat.name}")
            
        except ImportError:
            print("[WARNING] Plotly not installed, cannot visualize")
            print("Run: pip install plotly")


if __name__ == "__main__":
    main()
