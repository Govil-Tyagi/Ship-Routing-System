"""
Models for Marine Routing System
Defines all data structures for vessels, ports, routes, and danger zones.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Tuple
from enum import Enum
import uuid
from datetime import datetime, timezone


class VesselType(str, Enum):
    CARGO_SHIP = "cargo_ship"
    OIL_TANKER = "oil_tanker"
    FISHING_BOAT = "fishing_boat"
    HIGH_SPEED_BOAT = "high_speed_boat"


class DangerType(str, Enum):
    STORM = "storm"
    HIGH_WAVES = "high_waves"
    PIRACY = "piracy"
    MILITARY = "military"


class Coordinate(BaseModel):
    """Latitude and Longitude coordinate"""
    lat: float
    lon: float


class Port(BaseModel):
    """Port definition with name and coordinates"""
    name: str
    coordinate: Coordinate


class VesselConfig(BaseModel):
    """Vessel configuration with performance characteristics"""
    type: VesselType
    name: str
    fuel_consumption_rate: float  # L/km
    max_speed: float  # km/h
    storm_tolerance: float  # 0-1, higher = better tolerance
    risk_sensitivity: float  # multiplier for risk cost
    image_url: Optional[str] = None


class DangerZone(BaseModel):
    """Danger zone definition"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: DangerType
    name: str
    coordinates: List[Coordinate]  # Polygon vertices
    severity: float = Field(ge=0, le=1, default=0.5)  # 0-1 severity level
    is_restricted: bool = False  # If True, completely blocked


class GridNode(BaseModel):
    """Single node in the ocean grid"""
    lat: float
    lon: float
    row: int
    col: int
    is_water: bool = True
    is_blocked: bool = False
    danger_level: float = 0.0  # 0-1


class WeightConfig(BaseModel):
    """Weight configuration for cost calculation"""
    fuel_priority: float = Field(ge=0, le=1, default=0.33)
    time_priority: float = Field(ge=0, le=1, default=0.33)
    safety_priority: float = Field(ge=0, le=1, default=0.34)


class RouteRequest(BaseModel):
    """Request for route calculation"""
    source: Coordinate
    destination: Coordinate
    vessel_type: VesselType
    weights: WeightConfig = Field(default_factory=WeightConfig)


class RoutePoint(BaseModel):
    """Point along the calculated route"""
    lat: float
    lon: float
    cumulative_distance: float  # km from start
    cumulative_time: float  # hours from start
    cumulative_fuel: float  # L from start
    local_danger: float  # danger level at this point


class RouteResult(BaseModel):
    """Complete route calculation result"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    success: bool
    path: List[RoutePoint]
    total_distance: float  # km
    total_time: float  # hours
    total_fuel: float  # L
    average_risk: float  # 0-1
    total_cost: float  # normalized cost
    vessel_type: VesselType
    source_port: Optional[str] = None
    destination_port: Optional[str] = None
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    message: Optional[str] = None


class WeatherUpdate(BaseModel):
    """Weather update event"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    danger_zones: List[DangerZone]
    message: str


# Predefined vessel configurations
VESSEL_CONFIGS = {
    VesselType.CARGO_SHIP: VesselConfig(
        type=VesselType.CARGO_SHIP,
        name="Cargo Ship",
        fuel_consumption_rate=0.8,  # Heavy but efficient
        max_speed=35.0,  # ~19 knots
        storm_tolerance=0.7,  # Good storm handling
        risk_sensitivity=1.0,
        image_url="https://images.unsplash.com/photo-1770926605147-3c5d37cf8c47"
    ),
    VesselType.OIL_TANKER: VesselConfig(
        type=VesselType.OIL_TANKER,
        name="Oil Tanker",
        fuel_consumption_rate=1.2,  # Very heavy
        max_speed=28.0,  # ~15 knots
        storm_tolerance=0.8,  # Very stable
        risk_sensitivity=1.5,  # High value cargo
        image_url="https://images.unsplash.com/photo-1655763161700-8f284f0ceca9"
    ),
    VesselType.FISHING_BOAT: VesselConfig(
        type=VesselType.FISHING_BOAT,
        name="Fishing Boat",
        fuel_consumption_rate=0.3,  # Light vessel
        max_speed=25.0,  # ~13 knots
        storm_tolerance=0.4,  # Low tolerance
        risk_sensitivity=0.8,
        image_url="https://images.unsplash.com/photo-1596556864711-a9549fc3022c"
    ),
    VesselType.HIGH_SPEED_BOAT: VesselConfig(
        type=VesselType.HIGH_SPEED_BOAT,
        name="High Speed Boat",
        fuel_consumption_rate=0.6,  # Moderate
        max_speed=70.0,  # ~38 knots
        storm_tolerance=0.3,  # Very low tolerance
        risk_sensitivity=0.5,
        image_url="https://images.unsplash.com/photo-1645074685419-65072e107ffb"
    ),
}


# Predefined ports in Mediterranean
MEDITERRANEAN_PORTS = {
    "barcelona": Port(name="Barcelona", coordinate=Coordinate(lat=41.3851, lon=2.1734)),
    "marseille": Port(name="Marseille", coordinate=Coordinate(lat=43.2965, lon=5.3698)),
    "genoa": Port(name="Genoa", coordinate=Coordinate(lat=44.4056, lon=8.9463)),
    "naples": Port(name="Naples", coordinate=Coordinate(lat=40.8518, lon=14.2681)),
    "valletta": Port(name="Valletta", coordinate=Coordinate(lat=35.8989, lon=14.5146)),
    "tunis": Port(name="Tunis", coordinate=Coordinate(lat=36.8065, lon=10.1815)),
    "algiers": Port(name="Algiers", coordinate=Coordinate(lat=36.7538, lon=3.0588)),
    "alexandria": Port(name="Alexandria", coordinate=Coordinate(lat=31.2001, lon=29.9187)),
    "piraeus": Port(name="Piraeus", coordinate=Coordinate(lat=37.9475, lon=23.6372)),
    "istanbul": Port(name="Istanbul", coordinate=Coordinate(lat=41.0082, lon=28.9784)),
}
