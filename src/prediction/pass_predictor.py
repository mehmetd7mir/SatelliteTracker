"""
Pass Predictor Module
----------------------
Predict when satellites will pass over a location.

A "pass" is when satellite rises above horizon and then sets.
For ISS watching or ground station scheduling this is important.

Features:
    - Find next pass over location
    - Calculate pass duration
    - Find maximum elevation
    - AOS (Acquisition of Signal) and LOS (Loss of Signal) times

Author: Mehmet Demir
"""

from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

try:
    from skyfield.api import load, EarthSatellite, wgs84
    from skyfield import almanac
    SKYFIELD_AVAILABLE = True
except ImportError:
    SKYFIELD_AVAILABLE = False


@dataclass
class SatellitePass:
    """Information about satellite pass"""
    satellite_name: str
    aos_time: datetime  # Acquisition of Signal (rise)
    los_time: datetime  # Loss of Signal (set)
    max_elevation_time: datetime
    max_elevation_deg: float
    aos_azimuth: float
    los_azimuth: float
    duration_seconds: float
    is_sunlit: bool


class PassPredictor:
    """
    Predict satellite passes over a location.
    
    Example:
        predictor = PassPredictor(lat=41.0, lon=29.0)  # Istanbul
        predictor.add_satellite("ISS", line1, line2)
        
        passes = predictor.find_passes("ISS", days=3)
        for p in passes:
            print(f"Pass at {p.aos_time}, max elevation {p.max_elevation_deg:.1f} deg")
    """
    
    def __init__(
        self,
        observer_lat: float,
        observer_lon: float,
        observer_alt: float = 0.0,
        min_elevation: float = 10.0
    ):
        """
        Initialize with observer location.
        
        Args:
            observer_lat: latitude in degrees
            observer_lon: longitude in degrees
            observer_alt: altitude in meters
            min_elevation: minimum elevation to count as visible pass
        """
        if not SKYFIELD_AVAILABLE:
            raise ImportError("Skyfield required")
        
        self.ts = load.timescale()
        self.observer_lat = observer_lat
        self.observer_lon = observer_lon
        self.observer_alt = observer_alt
        self.min_elevation = min_elevation
        
        # create observer location
        self.observer = wgs84.latlon(observer_lat, observer_lon, observer_alt)
        
        # satellites
        self.satellites = {}
        
        # try load ephemeris for sunlit check
        try:
            self.eph = load("de421.bsp")
        except Exception:
            self.eph = None
    
    def add_satellite(self, name: str, line1: str, line2: str):
        """Add satellite from TLE."""
        sat = EarthSatellite(line1, line2, name, self.ts)
        self.satellites[name] = sat
    
    def _find_events(
        self,
        sat: EarthSatellite,
        start_time: datetime,
        end_time: datetime
    ) -> List[Tuple[datetime, str, float]]:
        """Find rise, culminate, set events."""
        t0 = self.ts.utc(start_time.year, start_time.month, start_time.day,
                         start_time.hour, start_time.minute)
        t1 = self.ts.utc(end_time.year, end_time.month, end_time.day,
                         end_time.hour, end_time.minute)
        
        # find events
        difference = sat - self.observer
        
        # simple approach: sample at intervals and find crossings
        events = []
        step_minutes = 1
        
        prev_el = None
        prev_time = None
        max_el = -90
        max_el_time = None
        
        current = start_time
        in_pass = False
        pass_start = None
        pass_start_az = None
        
        while current < end_time:
            t = self.ts.utc(current.year, current.month, current.day,
                           current.hour, current.minute, current.second)
            
            topocentric = difference.at(t)
            alt, az, dist = topocentric.altaz()
            el = alt.degrees
            az_deg = az.degrees
            
            if prev_el is not None:
                # check for rise (crossing above min_elevation)
                if prev_el < self.min_elevation and el >= self.min_elevation:
                    in_pass = True
                    pass_start = current
                    pass_start_az = az_deg
                    max_el = el
                    max_el_time = current
                
                # check for set (crossing below min_elevation)
                if prev_el >= self.min_elevation and el < self.min_elevation:
                    if in_pass and pass_start:
                        events.append({
                            "aos_time": pass_start,
                            "los_time": current,
                            "max_el_time": max_el_time,
                            "max_el": max_el,
                            "aos_az": pass_start_az,
                            "los_az": az_deg
                        })
                    in_pass = False
                    pass_start = None
                    max_el = -90
            
            # track maximum elevation during pass
            if in_pass and el > max_el:
                max_el = el
                max_el_time = current
            
            prev_el = el
            prev_time = current
            current += timedelta(minutes=step_minutes)
        
        return events
    
    def find_passes(
        self,
        sat_name: str,
        days: int = 7,
        start_time: Optional[datetime] = None
    ) -> List[SatellitePass]:
        """
        Find all passes of satellite over observer location.
        
        Args:
            sat_name: satellite name
            days: how many days to search
            start_time: start of search (default: now)
        
        Returns:
            List of SatellitePass objects
        """
        if sat_name not in self.satellites:
            print(f"Satellite {sat_name} not found")
            return []
        
        sat = self.satellites[sat_name]
        
        if start_time is None:
            start_time = datetime.utcnow()
        
        end_time = start_time + timedelta(days=days)
        
        # find events
        events = self._find_events(sat, start_time, end_time)
        
        passes = []
        for event in events:
            # check if sunlit at max elevation
            is_sunlit = False
            if self.eph:
                try:
                    t = self.ts.utc(
                        event["max_el_time"].year,
                        event["max_el_time"].month,
                        event["max_el_time"].day,
                        event["max_el_time"].hour,
                        event["max_el_time"].minute
                    )
                    is_sunlit = sat.at(t).is_sunlit(self.eph)
                except Exception:
                    pass
            
            duration = (event["los_time"] - event["aos_time"]).total_seconds()
            
            sat_pass = SatellitePass(
                satellite_name=sat_name,
                aos_time=event["aos_time"],
                los_time=event["los_time"],
                max_elevation_time=event["max_el_time"],
                max_elevation_deg=event["max_el"],
                aos_azimuth=event["aos_az"],
                los_azimuth=event["los_az"],
                duration_seconds=duration,
                is_sunlit=is_sunlit
            )
            passes.append(sat_pass)
        
        return passes
    
    def get_next_pass(
        self,
        sat_name: str,
        min_max_elevation: float = 20.0
    ) -> Optional[SatellitePass]:
        """Get next good pass (with minimum max elevation)."""
        passes = self.find_passes(sat_name, days=7)
        
        for p in passes:
            if p.max_elevation_deg >= min_max_elevation:
                return p
        
        return None


# test
if __name__ == "__main__":
    if SKYFIELD_AVAILABLE:
        # Istanbul coordinates
        predictor = PassPredictor(lat=41.0, lon=29.0, min_elevation=10.0)
        
        # add ISS
        line1 = "1 25544U 98067A   24001.50000000  .00016717  00000-0  30000-3 0  9999"
        line2 = "2 25544  51.6400 247.4627 0006703 170.5510 189.5640 15.49541000  1000"
        predictor.add_satellite("ISS", line1, line2)
        
        # find passes
        passes = predictor.find_passes("ISS", days=3)
        
        print(f"Found {len(passes)} ISS passes over Istanbul:\n")
        for i, p in enumerate(passes[:5]):
            print(f"Pass {i+1}:")
            print(f"  AOS: {p.aos_time} (Az: {p.aos_azimuth:.1f})")
            print(f"  MAX: {p.max_elevation_time} (El: {p.max_elevation_deg:.1f})")
            print(f"  LOS: {p.los_time} (Az: {p.los_azimuth:.1f})")
            print(f"  Duration: {p.duration_seconds/60:.1f} minutes")
            print()
    else:
        print("Skyfield not available")
