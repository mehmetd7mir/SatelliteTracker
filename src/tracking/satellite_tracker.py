"""
Satellite Tracker Module
-------------------------
Calculate real-time satellite positions using Skyfield.

Skyfield is high precision astronomy library that handle
all the complicated orbital mechanics for us.

Features:
    - Real-time position (lat, lon, alt)
    - Velocity calculation
    - Sun illumination status
    - Ground track generation

Author: Mehmet Demir
"""

from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np

try:
    from skyfield.api import load, EarthSatellite, wgs84
    from skyfield.timelib import Time
    SKYFIELD_AVAILABLE = True
except ImportError:
    SKYFIELD_AVAILABLE = False
    print("Skyfield not installed. Run: pip install skyfield")


@dataclass
class SatellitePosition:
    """Current satellite position data"""
    name: str
    latitude: float  # degrees
    longitude: float  # degrees
    altitude_km: float
    velocity_km_s: float
    is_sunlit: bool
    timestamp: datetime
    

@dataclass 
class GroundTrack:
    """Ground track for visualization"""
    latitudes: List[float]
    longitudes: List[float]
    altitudes: List[float]
    timestamps: List[datetime]


class SatelliteTracker:
    """
    Track satellites in real-time.
    
    Uses Skyfield for high precision orbital calculations.
    Can track multiple satellites at once.
    
    Example:
        tracker = SatelliteTracker()
        tracker.add_satellite_from_tle(name, line1, line2)
        
        pos = tracker.get_position("ISS")
        print(f"ISS is at {pos.latitude:.2f}, {pos.longitude:.2f}")
    """
    
    def __init__(self):
        if not SKYFIELD_AVAILABLE:
            raise ImportError("Skyfield required. Install: pip install skyfield")
        
        # load timescale
        self.ts = load.timescale()
        
        # store satellites
        self.satellites: Dict[str, EarthSatellite] = {}
        
        # load ephemeris for sun position (for illumination check)
        try:
            self.eph = load("de421.bsp")
            self.sun = self.eph["sun"]
            self.earth = self.eph["earth"]
        except Exception:
            print("Could not load ephemeris, sun illumination will not work")
            self.eph = None
            self.sun = None
            self.earth = None
    
    def add_satellite_from_tle(self, name: str, line1: str, line2: str):
        """
        Add satellite using TLE data.
        
        Args:
            name: satellite name
            line1: first TLE line
            line2: second TLE line
        """
        sat = EarthSatellite(line1, line2, name, self.ts)
        self.satellites[name] = sat
    
    def add_satellite(self, name: str, satellite: EarthSatellite):
        """Add pre-created satellite object."""
        self.satellites[name] = satellite
    
    def get_position(
        self,
        name: str,
        time: Optional[datetime] = None
    ) -> Optional[SatellitePosition]:
        """
        Get satellite position at given time.
        
        Args:
            name: satellite name
            time: datetime (default: now)
        
        Returns:
            SatellitePosition with lat, lon, alt, velocity
        """
        if name not in self.satellites:
            print(f"Satellite {name} not found")
            return None
        
        sat = self.satellites[name]
        
        # get time
        if time is None:
            t = self.ts.now()
            time = datetime.utcnow()
        else:
            t = self.ts.utc(time.year, time.month, time.day,
                           time.hour, time.minute, time.second)
        
        # calculate position
        geocentric = sat.at(t)
        subpoint = wgs84.subpoint(geocentric)
        
        lat = subpoint.latitude.degrees
        lon = subpoint.longitude.degrees
        alt = subpoint.elevation.km
        
        # calculate velocity
        velocity = geocentric.velocity.km_per_s
        speed = np.sqrt(sum(v**2 for v in velocity))
        
        # check if sunlit
        is_sunlit = False
        if self.sun and self.earth:
            try:
                is_sunlit = sat.at(t).is_sunlit(self.eph)
            except Exception:
                pass
        
        return SatellitePosition(
            name=name,
            latitude=lat,
            longitude=lon,
            altitude_km=alt,
            velocity_km_s=speed,
            is_sunlit=is_sunlit,
            timestamp=time
        )
    
    def get_all_positions(
        self,
        time: Optional[datetime] = None
    ) -> List[SatellitePosition]:
        """Get positions of all tracked satellites."""
        positions = []
        for name in self.satellites:
            pos = self.get_position(name, time)
            if pos:
                positions.append(pos)
        return positions
    
    def get_ground_track(
        self,
        name: str,
        duration_hours: float = 2.0,
        step_minutes: float = 1.0
    ) -> Optional[GroundTrack]:
        """
        Calculate ground track (path over Earth).
        
        Args:
            name: satellite name
            duration_hours: how long to predict
            step_minutes: time step
        
        Returns:
            GroundTrack with lat/lon arrays
        """
        if name not in self.satellites:
            return None
        
        sat = self.satellites[name]
        
        # generate time array
        now = datetime.utcnow()
        times = []
        current = now
        end = now + timedelta(hours=duration_hours)
        
        while current < end:
            times.append(current)
            current += timedelta(minutes=step_minutes)
        
        # calculate positions
        lats = []
        lons = []
        alts = []
        
        for time in times:
            t = self.ts.utc(time.year, time.month, time.day,
                           time.hour, time.minute, time.second)
            geocentric = sat.at(t)
            subpoint = wgs84.subpoint(geocentric)
            
            lats.append(subpoint.latitude.degrees)
            lons.append(subpoint.longitude.degrees)
            alts.append(subpoint.elevation.km)
        
        return GroundTrack(
            latitudes=lats,
            longitudes=lons,
            altitudes=alts,
            timestamps=times
        )
    
    def get_look_angle(
        self,
        sat_name: str,
        observer_lat: float,
        observer_lon: float,
        observer_alt: float = 0.0,
        time: Optional[datetime] = None
    ) -> Tuple[float, float, float]:
        """
        Calculate azimuth, elevation and range from observer.
        
        Args:
            sat_name: satellite name
            observer_lat: observer latitude
            observer_lon: observer longitude
            observer_alt: observer altitude (meters)
            time: observation time
        
        Returns:
            (azimuth_deg, elevation_deg, range_km)
        """
        if sat_name not in self.satellites:
            return (0, 0, 0)
        
        sat = self.satellites[sat_name]
        
        if time is None:
            t = self.ts.now()
        else:
            t = self.ts.utc(time.year, time.month, time.day,
                           time.hour, time.minute, time.second)
        
        # create observer location
        observer = wgs84.latlon(observer_lat, observer_lon, observer_alt)
        
        # calculate difference
        difference = sat - observer
        topocentric = difference.at(t)
        
        # get alt/az
        alt, az, distance = topocentric.altaz()
        
        return (az.degrees, alt.degrees, distance.km)
    
    def is_visible(
        self,
        sat_name: str,
        observer_lat: float,
        observer_lon: float,
        min_elevation: float = 10.0,
        time: Optional[datetime] = None
    ) -> bool:
        """Check if satellite is visible from observer location."""
        az, el, dist = self.get_look_angle(
            sat_name, observer_lat, observer_lon, 0, time
        )
        return el >= min_elevation


# test
if __name__ == "__main__":
    if SKYFIELD_AVAILABLE:
        tracker = SatelliteTracker()
        
        # add ISS
        line1 = "1 25544U 98067A   24001.50000000  .00016717  00000-0  30000-3 0  9999"
        line2 = "2 25544  51.6400 247.4627 0006703 170.5510 189.5640 15.49541000  1000"
        tracker.add_satellite_from_tle("ISS", line1, line2)
        
        # get position
        pos = tracker.get_position("ISS")
        if pos:
            print(f"ISS Current Position:")
            print(f"  Latitude:  {pos.latitude:.4f} deg")
            print(f"  Longitude: {pos.longitude:.4f} deg")
            print(f"  Altitude:  {pos.altitude_km:.2f} km")
            print(f"  Velocity:  {pos.velocity_km_s:.2f} km/s")
            print(f"  Sunlit:    {pos.is_sunlit}")
        
        # get ground track
        track = tracker.get_ground_track("ISS", duration_hours=1)
        if track:
            print(f"\nGround track: {len(track.latitudes)} points")
    else:
        print("Skyfield not available")
