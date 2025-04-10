"""
TLE Parser Module
------------------
Parse Two-Line Element (TLE) data for satellite tracking.

TLE is standard format for satellite orbital parameters.
It contain all info needed to calculate satellite position.

Example TLE:
    ISS (ZARYA)
    1 25544U 98067A   21275.52628472  .00001878  00000-0  42329-4 0  9999
    2 25544  51.6442 208.5455 0003660  56.4240  60.5765 15.48919755305637

Author: Mehmet Demir
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import requests


@dataclass
class TLEData:
    """Container for parsed TLE data"""
    name: str
    norad_id: int
    classification: str
    launch_year: int
    launch_number: int
    piece: str
    epoch_year: int
    epoch_day: float
    mean_motion_dot: float
    mean_motion_ddot: float
    bstar: float
    inclination: float
    raan: float  # Right Ascension of Ascending Node
    eccentricity: float
    arg_perigee: float
    mean_anomaly: float
    mean_motion: float
    rev_number: int
    line1: str
    line2: str


class TLEParser:
    """
    Parse TLE data from string or file.
    
    TLE format is bit weird but we handle it.
    Line 1 has orbital parameters, Line 2 has more.
    
    Example:
        parser = TLEParser()
        tle = parser.parse_lines(name, line1, line2)
        print(f"Satellite: {tle.name}")
        print(f"Inclination: {tle.inclination} degrees")
    """
    
    def __init__(self):
        self.tle_sources = {
            "celestrak": "https://celestrak.org/NORAD/elements/gp.php",
            "stations": "https://celestrak.org/NORAD/elements/stations.txt",
            "starlink": "https://celestrak.org/NORAD/elements/starlink.txt",
            "gps": "https://celestrak.org/NORAD/elements/gps-ops.txt",
        }
    
    def parse_lines(self, name: str, line1: str, line2: str) -> TLEData:
        """
        Parse TLE from three lines.
        
        Args:
            name: satellite name
            line1: first TLE line (starts with 1)
            line2: second TLE line (starts with 2)
        
        Returns:
            TLEData object with all parameters
        """
        # clean lines
        name = name.strip()
        line1 = line1.strip()
        line2 = line2.strip()
        
        # validate line numbers
        if not line1.startswith("1") or not line2.startswith("2"):
            raise ValueError("Invalid TLE format - lines must start with 1 and 2")
        
        # parse line 1
        norad_id = int(line1[2:7])
        classification = line1[7]
        launch_year = int(line1[9:11])
        launch_number = int(line1[11:14])
        piece = line1[14:17].strip()
        epoch_year = int(line1[18:20])
        epoch_day = float(line1[20:32])
        mean_motion_dot = float(line1[33:43])
        
        # mean motion second derivative (weird format)
        mm_ddot_str = line1[44:52].strip()
        if mm_ddot_str:
            mantissa = float("0." + mm_ddot_str[:-2].replace(" ", "").replace("+", "").replace("-", ""))
            exp = int(mm_ddot_str[-2:])
            mean_motion_ddot = mantissa * (10 ** exp)
            if "-" in mm_ddot_str[:1]:
                mean_motion_ddot = -mean_motion_ddot
        else:
            mean_motion_ddot = 0.0
        
        # bstar drag term (also weird format)
        bstar_str = line1[53:61].strip()
        if bstar_str:
            mantissa = float("0." + bstar_str[:-2].replace(" ", "").replace("+", "").replace("-", ""))
            exp = int(bstar_str[-2:])
            bstar = mantissa * (10 ** exp)
            if "-" in bstar_str[:1]:
                bstar = -bstar
        else:
            bstar = 0.0
        
        # parse line 2
        inclination = float(line2[8:16])
        raan = float(line2[17:25])
        eccentricity = float("0." + line2[26:33])
        arg_perigee = float(line2[34:42])
        mean_anomaly = float(line2[43:51])
        mean_motion = float(line2[52:63])
        rev_number = int(line2[63:68])
        
        return TLEData(
            name=name,
            norad_id=norad_id,
            classification=classification,
            launch_year=launch_year,
            launch_number=launch_number,
            piece=piece,
            epoch_year=epoch_year,
            epoch_day=epoch_day,
            mean_motion_dot=mean_motion_dot,
            mean_motion_ddot=mean_motion_ddot,
            bstar=bstar,
            inclination=inclination,
            raan=raan,
            eccentricity=eccentricity,
            arg_perigee=arg_perigee,
            mean_anomaly=mean_anomaly,
            mean_motion=mean_motion,
            rev_number=rev_number,
            line1=line1,
            line2=line2
        )
    
    def parse_string(self, tle_string: str) -> List[TLEData]:
        """
        Parse multiple TLEs from string.
        
        Format is:
            NAME
            1 ...
            2 ...
            NAME
            1 ...
            2 ...
        """
        lines = tle_string.strip().split("\n")
        satellites = []
        
        i = 0
        while i < len(lines) - 2:
            name = lines[i].strip()
            line1 = lines[i + 1].strip()
            line2 = lines[i + 2].strip()
            
            # check if this is valid TLE
            if line1.startswith("1") and line2.startswith("2"):
                try:
                    tle = self.parse_lines(name, line1, line2)
                    satellites.append(tle)
                except Exception as e:
                    print(f"Error parsing {name}: {e}")
                i += 3
            else:
                i += 1
        
        return satellites
    
    def parse_file(self, filepath: str) -> List[TLEData]:
        """Parse TLE file."""
        with open(filepath, "r") as f:
            return self.parse_string(f.read())
    
    def fetch_from_celestrak(self, category: str = "stations") -> List[TLEData]:
        """
        Download fresh TLE data from CelesTrak.
        
        Categories: stations, starlink, gps, weather, etc.
        """
        url = self.tle_sources.get(category)
        if not url:
            # try as direct category
            url = f"https://celestrak.org/NORAD/elements/{category}.txt"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return self.parse_string(response.text)
        except Exception as e:
            print(f"Failed to fetch TLE data: {e}")
            return []
    
    def get_iss(self) -> Optional[TLEData]:
        """Get ISS TLE data (convenience method)."""
        satellites = self.fetch_from_celestrak("stations")
        for sat in satellites:
            if "ISS" in sat.name.upper():
                return sat
        return None


# some default TLEs for testing when offline
DEFAULT_TLES = """ISS (ZARYA)
1 25544U 98067A   24001.50000000  .00016717  00000-0  30000-3 0  9999
2 25544  51.6400 247.4627 0006703 170.5510 189.5640 15.49541000  1000
STARLINK-1007
1 44713U 19074A   24001.50000000  .00001000  00000-0  10000-3 0  9999
2 44713  53.0000 200.0000 0001500  90.0000 270.0000 15.05000000  1000
GPS BIIR-2
1 24876U 97035A   24001.50000000  .00000010  00000-0  10000-3 0  9999
2 24876  55.0000 100.0000 0050000 250.0000 100.0000  2.00562000  1000"""


# test
if __name__ == "__main__":
    parser = TLEParser()
    
    # test with default TLEs
    satellites = parser.parse_string(DEFAULT_TLES)
    
    print(f"Parsed {len(satellites)} satellites:\n")
    for sat in satellites:
        print(f"  {sat.name}")
        print(f"    NORAD ID: {sat.norad_id}")
        print(f"    Inclination: {sat.inclination:.2f} deg")
        print(f"    Mean Motion: {sat.mean_motion:.4f} rev/day")
        print()
