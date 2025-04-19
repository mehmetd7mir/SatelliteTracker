"""
3D Globe Visualization
-----------------------
Visualize satellites on 3D Earth using Plotly.

Creates interactive globe with:
    - Satellite positions as markers
    - Ground tracks as lines
    - Country borders
    - Day/night terminator

Author: Mehmet Demir
"""

from typing import List, Optional, Tuple
import numpy as np

try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("Plotly not installed. Run: pip install plotly")


def create_sphere(radius: float = 1.0, resolution: int = 50) -> Tuple:
    """Create sphere mesh for Earth."""
    u = np.linspace(0, 2 * np.pi, resolution)
    v = np.linspace(0, np.pi, resolution)
    
    x = radius * np.outer(np.cos(u), np.sin(v))
    y = radius * np.outer(np.sin(u), np.sin(v))
    z = radius * np.outer(np.ones(np.size(u)), np.cos(v))
    
    return x, y, z


def latlon_to_xyz(lat: float, lon: float, alt_km: float = 0.0) -> Tuple[float, float, float]:
    """Convert lat/lon to 3D coordinates."""
    earth_radius = 6371  # km
    r = (earth_radius + alt_km) / earth_radius  # normalized radius
    
    lat_rad = np.radians(lat)
    lon_rad = np.radians(lon)
    
    x = r * np.cos(lat_rad) * np.cos(lon_rad)
    y = r * np.cos(lat_rad) * np.sin(lon_rad)
    z = r * np.sin(lat_rad)
    
    return x, y, z


class GlobeVisualizer:
    """
    Create 3D globe with satellites.
    
    Example:
        viz = GlobeVisualizer()
        viz.add_satellite("ISS", lat=45.0, lon=-73.5, alt_km=420)
        viz.add_ground_track(lats, lons, "ISS Track")
        fig = viz.create_figure()
        fig.show()
    """
    
    def __init__(self):
        if not PLOTLY_AVAILABLE:
            raise ImportError("Plotly required")
        
        self.satellites = []
        self.ground_tracks = []
        self.markers = []
    
    def add_satellite(
        self,
        name: str,
        lat: float,
        lon: float,
        alt_km: float,
        color: str = "red",
        size: int = 10
    ):
        """Add satellite marker."""
        x, y, z = latlon_to_xyz(lat, lon, alt_km)
        self.satellites.append({
            "name": name,
            "x": x,
            "y": y,
            "z": z,
            "lat": lat,
            "lon": lon,
            "alt": alt_km,
            "color": color,
            "size": size
        })
    
    def add_ground_track(
        self,
        lats: List[float],
        lons: List[float],
        name: str = "Track",
        color: str = "yellow"
    ):
        """Add ground track line."""
        xs, ys, zs = [], [], []
        for lat, lon in zip(lats, lons):
            x, y, z = latlon_to_xyz(lat, lon, 10)  # slightly above surface
            xs.append(x)
            ys.append(y)
            zs.append(z)
        
        self.ground_tracks.append({
            "name": name,
            "x": xs,
            "y": ys,
            "z": zs,
            "color": color
        })
    
    def add_location(
        self,
        name: str,
        lat: float,
        lon: float,
        color: str = "green"
    ):
        """Add ground location marker."""
        x, y, z = latlon_to_xyz(lat, lon, 5)
        self.markers.append({
            "name": name,
            "x": x,
            "y": y,
            "z": z,
            "color": color
        })
    
    def create_figure(self, title: str = "Satellite Tracker") -> go.Figure:
        """Create the 3D globe figure."""
        fig = go.Figure()
        
        # add Earth sphere
        x, y, z = create_sphere()
        
        # create colorscale for Earth (blue oceans, green land approximation)
        fig.add_trace(go.Surface(
            x=x, y=y, z=z,
            colorscale=[[0, "rgb(50, 100, 180)"], [1, "rgb(30, 80, 150)"]],
            showscale=False,
            opacity=0.9,
            name="Earth"
        ))
        
        # add satellites
        for sat in self.satellites:
            fig.add_trace(go.Scatter3d(
                x=[sat["x"]],
                y=[sat["y"]],
                z=[sat["z"]],
                mode="markers+text",
                marker=dict(size=sat["size"], color=sat["color"]),
                text=[sat["name"]],
                textposition="top center",
                name=sat["name"],
                hovertemplate=(
                    f"<b>{sat['name']}</b><br>"
                    f"Lat: {sat['lat']:.2f}<br>"
                    f"Lon: {sat['lon']:.2f}<br>"
                    f"Alt: {sat['alt']:.0f} km<extra></extra>"
                )
            ))
        
        # add ground tracks
        for track in self.ground_tracks:
            fig.add_trace(go.Scatter3d(
                x=track["x"],
                y=track["y"],
                z=track["z"],
                mode="lines",
                line=dict(color=track["color"], width=3),
                name=track["name"]
            ))
        
        # add ground markers
        for marker in self.markers:
            fig.add_trace(go.Scatter3d(
                x=[marker["x"]],
                y=[marker["y"]],
                z=[marker["z"]],
                mode="markers+text",
                marker=dict(size=8, color=marker["color"], symbol="diamond"),
                text=[marker["name"]],
                textposition="top center",
                name=marker["name"]
            ))
        
        # layout
        fig.update_layout(
            title=title,
            scene=dict(
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                zaxis=dict(visible=False),
                aspectmode="data",
                bgcolor="black"
            ),
            paper_bgcolor="black",
            margin=dict(l=0, r=0, t=50, b=0),
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                font=dict(color="white")
            )
        )
        
        return fig
    
    def show(self, title: str = "Satellite Tracker"):
        """Show the figure in browser."""
        fig = self.create_figure(title)
        fig.show()


def create_ground_track_map(
    lats: List[float],
    lons: List[float],
    sat_lat: float,
    sat_lon: float,
    sat_name: str = "Satellite"
) -> go.Figure:
    """
    Create 2D map with ground track (simpler than 3D).
    """
    fig = go.Figure()
    
    # ground track
    fig.add_trace(go.Scattergeo(
        lat=lats,
        lon=lons,
        mode="lines",
        line=dict(width=2, color="yellow"),
        name="Ground Track"
    ))
    
    # current position
    fig.add_trace(go.Scattergeo(
        lat=[sat_lat],
        lon=[sat_lon],
        mode="markers+text",
        marker=dict(size=15, color="red", symbol="star"),
        text=[sat_name],
        textposition="top center",
        name=sat_name
    ))
    
    fig.update_layout(
        title=f"{sat_name} Ground Track",
        geo=dict(
            showland=True,
            landcolor="rgb(50, 100, 50)",
            showocean=True,
            oceancolor="rgb(30, 60, 120)",
            showlakes=True,
            lakecolor="rgb(30, 60, 120)",
            showcountries=True,
            countrycolor="rgb(100, 100, 100)",
            projection_type="natural earth"
        ),
        paper_bgcolor="rgb(20, 20, 30)",
        font=dict(color="white")
    )
    
    return fig


# test
if __name__ == "__main__":
    if PLOTLY_AVAILABLE:
        viz = GlobeVisualizer()
        
        # add ISS
        viz.add_satellite("ISS", lat=45.0, lon=-73.5, alt_km=420, color="red")
        
        # add sample ground track
        lats = [45 + i*0.5 for i in range(50)]
        lons = [-73 + i*2 for i in range(50)]
        viz.add_ground_track(lats, lons, "ISS Track", "yellow")
        
        # add ground station
        viz.add_location("Istanbul", lat=41.0, lon=29.0)
        
        print("Creating 3D globe visualization...")
        viz.show("Satellite Tracker Demo")
    else:
        print("Plotly not available")
