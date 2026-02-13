"""
Ocean Grid Generator for Marine Routing System
Generates a 2D latitude-longitude grid covering the Mediterranean Sea.
Each grid node connects to 8 neighbors (N, S, E, W, NE, NW, SE, SW).
"""
import math
from typing import List, Dict, Tuple, Optional
from models import GridNode, Coordinate, DangerZone
import numpy as np


class OceanGrid:
    """
    Ocean grid system for A* pathfinding.
    Generates navigable ocean points and manages connectivity.
    """
    
    # Extended bounds covering Mediterranean + Indian Ocean
    DEFAULT_BOUNDS = {
        "min_lat": 5.0,   # Extended south for Indian Ocean
        "max_lat": 46.0,
        "min_lon": -6.0,
        "max_lon": 95.0   # Extended east for Bay of Bengal
    }
    
    # 8 directions: (row_delta, col_delta, name)
    DIRECTIONS = [
        (-1, 0, "N"),   # North
        (1, 0, "S"),    # South
        (0, 1, "E"),    # East
        (0, -1, "W"),   # West
        (-1, 1, "NE"),  # Northeast
        (-1, -1, "NW"), # Northwest
        (1, 1, "SE"),   # Southeast
        (1, -1, "SW"),  # Southwest
    ]
    
    # Simple land mask for Mediterranean + Indian Ocean (approximate polygons)
    # This helps identify which grid cells are land vs water
    LAND_POLYGONS = [
        # Spain coast (simplified)
        [(42.5, -2.0), (42.5, 3.0), (38.0, 0.0), (36.5, -2.0)],
        # France coast
        [(43.5, 3.0), (44.5, 7.5), (43.0, 7.5), (43.0, 5.0)],
        # Italy boot
        [(46.0, 7.0), (46.0, 14.0), (44.0, 12.5), (43.0, 13.5), (42.0, 14.5),
         (41.5, 16.0), (40.0, 18.5), (38.0, 16.0), (37.5, 15.0), (38.5, 12.5),
         (40.0, 9.0), (43.5, 7.5)],
        # Balkans coast (simplified)
        [(46.0, 14.0), (46.0, 20.0), (42.0, 19.5), (39.5, 20.0), (35.5, 26.0),
         (38.0, 24.0), (38.5, 22.0), (40.5, 22.5), (42.0, 19.0)],
        # Turkey
        [(36.0, 26.0), (37.0, 27.0), (37.5, 30.0), (36.5, 36.0), (41.5, 36.0),
         (42.0, 28.0), (40.0, 26.0)],
        # North Africa coast
        [(37.5, -1.0), (37.0, 10.0), (33.0, 11.0), (32.0, 25.0), (31.0, 32.0),
         (30.0, 32.0), (30.0, -6.0)],
        # Sicily
        [(38.5, 12.5), (38.0, 15.5), (37.0, 15.0), (37.5, 12.5)],
        # Sardinia
        [(41.5, 8.0), (41.5, 10.0), (39.0, 9.5), (38.8, 8.0)],
        # Corsica
        [(43.0, 9.0), (43.0, 9.6), (41.3, 9.5), (41.3, 8.5)],
        # Cyprus
        [(35.7, 32.0), (35.7, 34.6), (34.5, 34.0), (34.5, 32.3)],
        # Crete
        [(35.7, 23.5), (35.7, 26.3), (34.9, 26.0), (34.9, 23.5)],
        # Middle East (simplified)
        [(30.0, 32.0), (32.0, 35.0), (33.0, 36.0), (37.0, 42.0), (30.0, 48.0),
         (24.0, 51.0), (22.0, 55.0), (17.0, 54.0), (12.5, 44.0), (11.0, 43.0),
         (12.0, 41.0), (26.0, 35.0)],
        # Arabian Peninsula (simplified)
        [(30.0, 35.0), (30.0, 48.0), (24.0, 51.0), (22.0, 56.0), (17.0, 54.0),
         (12.5, 44.0), (17.0, 42.0), (20.0, 40.0), (28.0, 35.0)],
        # India (simplified)
        [(35.0, 70.0), (35.0, 78.0), (32.0, 77.0), (28.0, 77.0), (24.0, 73.0),
         (23.0, 69.0), (20.0, 68.5), (18.0, 72.5), (15.0, 73.5), (14.0, 74.5),
         (11.0, 75.5), (8.0, 77.0), (8.0, 78.5), (10.0, 80.0), (13.0, 80.5),
         (16.0, 82.0), (19.0, 85.0), (21.0, 87.0), (22.0, 88.5), (24.0, 89.0),
         (27.0, 89.0), (28.0, 88.0), (27.0, 85.0), (26.0, 84.0), (28.0, 80.0),
         (30.0, 78.0)],
        # Sri Lanka
        [(10.0, 79.5), (10.0, 82.0), (6.0, 81.5), (6.0, 79.5)],
        # East Africa coast (simplified)
        [(12.0, 41.0), (11.0, 43.0), (5.0, 42.0), (2.0, 41.0), (-1.0, 41.5),
         (-5.0, 39.5), (-10.0, 40.0), (-15.0, 40.5), (-15.0, 35.0), (-5.0, 35.0),
         (5.0, 35.0), (12.0, 37.0)],
        # Myanmar/Thailand coast
        [(28.0, 92.0), (25.0, 95.0), (20.0, 93.0), (16.0, 94.0), (10.0, 98.0),
         (8.0, 98.5), (6.0, 100.0), (6.0, 95.0), (10.0, 92.0), (20.0, 90.0),
         (26.0, 90.0)],
    ]
    
    def __init__(
        self,
        resolution: float = 0.5,  # degrees between grid points
        bounds: Optional[Dict] = None
    ):
        """
        Initialize the ocean grid.
        
        Args:
            resolution: Grid resolution in degrees (smaller = finer grid)
            bounds: Dictionary with min_lat, max_lat, min_lon, max_lon
        """
        self.resolution = resolution
        self.bounds = bounds or self.DEFAULT_BOUNDS
        
        # Calculate grid dimensions
        self.rows = int((self.bounds["max_lat"] - self.bounds["min_lat"]) / resolution) + 1
        self.cols = int((self.bounds["max_lon"] - self.bounds["min_lon"]) / resolution) + 1
        
        # Initialize grid
        self.grid: List[List[GridNode]] = []
        self.danger_zones: List[DangerZone] = []
        
        self._generate_grid()
    
    def _generate_grid(self):
        """Generate the 2D grid of ocean nodes."""
        self.grid = []
        
        for row in range(self.rows):
            grid_row = []
            lat = self.bounds["max_lat"] - (row * self.resolution)
            
            for col in range(self.cols):
                lon = self.bounds["min_lon"] + (col * self.resolution)
                
                # Check if point is water
                is_water = self._is_water(lat, lon)
                
                node = GridNode(
                    lat=lat,
                    lon=lon,
                    row=row,
                    col=col,
                    is_water=is_water,
                    is_blocked=not is_water,
                    danger_level=0.0
                )
                grid_row.append(node)
            
            self.grid.append(grid_row)
    
    def _is_water(self, lat: float, lon: float) -> bool:
        """
        Check if a coordinate is water (not land).
        Uses simple point-in-polygon test for land masses.
        """
        for polygon in self.LAND_POLYGONS:
            if self._point_in_polygon(lat, lon, polygon):
                return False
        return True
    
    def _point_in_polygon(self, lat: float, lon: float, polygon: List[Tuple[float, float]]) -> bool:
        """Ray casting algorithm for point-in-polygon test."""
        n = len(polygon)
        inside = False
        
        p1_lat, p1_lon = polygon[0]
        for i in range(1, n + 1):
            p2_lat, p2_lon = polygon[i % n]
            
            if lon > min(p1_lon, p2_lon):
                if lon <= max(p1_lon, p2_lon):
                    if lat <= max(p1_lat, p2_lat):
                        if p1_lon != p2_lon:
                            lat_intersect = (lon - p1_lon) * (p2_lat - p1_lat) / (p2_lon - p1_lon) + p1_lat
                        if p1_lat == p2_lat or lat <= lat_intersect:
                            inside = not inside
            
            p1_lat, p1_lon = p2_lat, p2_lon
        
        return inside
    
    def get_node(self, lat: float, lon: float) -> Optional[GridNode]:
        """Get the grid node closest to given coordinates."""
        row, col = self.coord_to_index(lat, lon)
        
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.grid[row][col]
        return None
    
    def coord_to_index(self, lat: float, lon: float) -> Tuple[int, int]:
        """Convert lat/lon to grid row/col indices."""
        row = int((self.bounds["max_lat"] - lat) / self.resolution)
        col = int((lon - self.bounds["min_lon"]) / self.resolution)
        return row, col
    
    def index_to_coord(self, row: int, col: int) -> Tuple[float, float]:
        """Convert grid row/col to lat/lon coordinates."""
        lat = self.bounds["max_lat"] - (row * self.resolution)
        lon = self.bounds["min_lon"] + (col * self.resolution)
        return lat, lon
    
    def get_neighbors(self, row: int, col: int) -> List[Tuple[int, int, str]]:
        """
        Get all valid neighboring nodes (8-connectivity).
        Returns list of (row, col, direction_name) tuples.
        """
        neighbors = []
        
        for dr, dc, direction in self.DIRECTIONS:
            new_row = row + dr
            new_col = col + dc
            
            # Check bounds
            if 0 <= new_row < self.rows and 0 <= new_col < self.cols:
                node = self.grid[new_row][new_col]
                # Only include water nodes that aren't blocked
                if node.is_water and not node.is_blocked:
                    neighbors.append((new_row, new_col, direction))
        
        return neighbors
    
    def apply_danger_zones(self, danger_zones: List[DangerZone]):
        """
        Apply danger zones to the grid, updating node danger levels.
        Restricted zones block nodes completely.
        """
        self.danger_zones = danger_zones
        
        # Reset all danger levels first
        for row in self.grid:
            for node in row:
                node.danger_level = 0.0
                if node.is_water:
                    node.is_blocked = False
        
        # Apply each danger zone
        for zone in danger_zones:
            polygon = [(c.lat, c.lon) for c in zone.coordinates]
            
            for row in self.grid:
                for node in row:
                    if not node.is_water:
                        continue
                    
                    if self._point_in_polygon(node.lat, node.lon, polygon):
                        if zone.is_restricted:
                            node.is_blocked = True
                            node.danger_level = 1.0
                        else:
                            # Stack danger levels (max cap at 1.0)
                            node.danger_level = min(1.0, node.danger_level + zone.severity)
    
    def get_grid_info(self) -> Dict:
        """Get grid metadata and statistics."""
        water_count = sum(1 for row in self.grid for node in row if node.is_water)
        blocked_count = sum(1 for row in self.grid for node in row if node.is_blocked)
        danger_count = sum(1 for row in self.grid for node in row if node.danger_level > 0)
        
        return {
            "rows": self.rows,
            "cols": self.cols,
            "resolution": self.resolution,
            "bounds": self.bounds,
            "total_nodes": self.rows * self.cols,
            "water_nodes": water_count,
            "blocked_nodes": blocked_count,
            "danger_nodes": danger_count
        }
    
    def find_nearest_water_node(self, lat: float, lon: float) -> Optional[GridNode]:
        """Find the nearest navigable water node to given coordinates."""
        row, col = self.coord_to_index(lat, lon)
        
        # Check the target node first
        if 0 <= row < self.rows and 0 <= col < self.cols:
            node = self.grid[row][col]
            if node.is_water and not node.is_blocked:
                return node
        
        # Search in expanding rings
        for radius in range(1, max(self.rows, self.cols)):
            for dr in range(-radius, radius + 1):
                for dc in range(-radius, radius + 1):
                    if abs(dr) != radius and abs(dc) != radius:
                        continue
                    
                    nr, nc = row + dr, col + dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        node = self.grid[nr][nc]
                        if node.is_water and not node.is_blocked:
                            return node
        
        return None
