"""
Weather Simulator Module for Marine Routing
Simulates dynamic weather changes that affect danger zones.
"""
import random
import math
from typing import List, Tuple
from models import DangerZone, DangerType, Coordinate, WeatherUpdate
from danger_zone import get_default_danger_zones, create_storm_zone
import uuid
from datetime import datetime, timezone


class WeatherSimulator:
    """
    Simulates dynamic weather conditions in the Mediterranean.
    Can generate random weather events and update existing zones.
    """
    
    # Mediterranean bounds for random weather generation
    BOUNDS = {
        "min_lat": 32.0,
        "max_lat": 43.0,
        "min_lon": 0.0,
        "max_lon": 30.0
    }
    
    def __init__(self, base_zones: List[DangerZone] = None):
        """
        Initialize weather simulator.
        
        Args:
            base_zones: Initial danger zones (static zones)
        """
        self.base_zones = base_zones or get_default_danger_zones()
        self.dynamic_zones: List[DangerZone] = []
        self.update_counter = 0
    
    def get_current_zones(self) -> List[DangerZone]:
        """Get all current danger zones (base + dynamic)."""
        return self.base_zones + self.dynamic_zones
    
    def simulate_weather_change(self) -> WeatherUpdate:
        """
        Simulate a weather change event.
        
        Returns:
            WeatherUpdate with new zone configuration
        """
        self.update_counter += 1
        
        # Randomly decide what kind of change to make
        change_type = random.choice(["add_storm", "move_storm", "clear_storm", "intensity_change"])
        
        if change_type == "add_storm" and len(self.dynamic_zones) < 3:
            # Add a new storm zone
            zone = self._generate_random_storm()
            self.dynamic_zones.append(zone)
            message = f"New storm system '{zone.name}' forming"
            
        elif change_type == "move_storm" and self.dynamic_zones:
            # Move an existing dynamic storm
            idx = random.randint(0, len(self.dynamic_zones) - 1)
            zone = self.dynamic_zones[idx]
            self._move_zone(zone)
            message = f"Storm '{zone.name}' is moving"
            
        elif change_type == "clear_storm" and self.dynamic_zones:
            # Remove a dynamic storm
            zone = self.dynamic_zones.pop(random.randint(0, len(self.dynamic_zones) - 1))
            message = f"Storm '{zone.name}' has dissipated"
            
        else:
            # Change intensity of a base zone
            if self.base_zones:
                zone = random.choice(self.base_zones)
                old_severity = zone.severity
                zone.severity = max(0.2, min(0.9, zone.severity + random.uniform(-0.2, 0.2)))
                if zone.severity > old_severity:
                    message = f"Conditions worsening in '{zone.name}'"
                else:
                    message = f"Conditions improving in '{zone.name}'"
            else:
                message = "Weather conditions stable"
        
        return WeatherUpdate(
            danger_zones=self.get_current_zones(),
            message=message
        )
    
    def _generate_random_storm(self) -> DangerZone:
        """Generate a random storm zone within Mediterranean bounds."""
        center_lat = random.uniform(self.BOUNDS["min_lat"] + 2, self.BOUNDS["max_lat"] - 2)
        center_lon = random.uniform(self.BOUNDS["min_lon"] + 2, self.BOUNDS["max_lon"] - 2)
        radius = random.uniform(1.0, 2.0)
        severity = random.uniform(0.4, 0.8)
        
        storm_names = [
            "Alpha Storm", "Beta Storm", "Gamma Storm", 
            "Mediterranean Low", "Cyclone Delta", "Storm Epsilon"
        ]
        name = f"{random.choice(storm_names)} {self.update_counter}"
        
        return create_storm_zone(center_lat, center_lon, radius, name, severity)
    
    def _move_zone(self, zone: DangerZone):
        """Move a zone slightly (simulate storm movement)."""
        # Calculate movement vector
        delta_lat = random.uniform(-0.5, 0.5)
        delta_lon = random.uniform(-0.5, 0.5)
        
        # Move all coordinates
        new_coords = []
        for coord in zone.coordinates:
            new_lat = coord.lat + delta_lat
            new_lon = coord.lon + delta_lon
            
            # Keep within bounds
            new_lat = max(self.BOUNDS["min_lat"], min(self.BOUNDS["max_lat"], new_lat))
            new_lon = max(self.BOUNDS["min_lon"], min(self.BOUNDS["max_lon"], new_lon))
            
            new_coords.append(Coordinate(lat=new_lat, lon=new_lon))
        
        zone.coordinates = new_coords
    
    def reset_to_default(self):
        """Reset weather to default state (clear dynamic zones)."""
        self.dynamic_zones = []
        self.base_zones = get_default_danger_zones()
        
        return WeatherUpdate(
            danger_zones=self.get_current_zones(),
            message="Weather reset to default conditions"
        )
    
    def add_custom_zone(self, zone: DangerZone):
        """Add a custom danger zone."""
        self.dynamic_zones.append(zone)
        
        return WeatherUpdate(
            danger_zones=self.get_current_zones(),
            message=f"Added custom zone: {zone.name}"
        )


# Global weather simulator instance
weather_simulator = WeatherSimulator()


def get_weather_simulator() -> WeatherSimulator:
    """Get the global weather simulator instance."""
    return weather_simulator
