"""
Danger Zone Module for Marine Routing
Defines and manages danger zones including storms, piracy, and military areas.
"""
from typing import List
from models import DangerZone, DangerType, Coordinate
import uuid


# Predefined danger zones for Mediterranean Sea
DEFAULT_DANGER_ZONES: List[DangerZone] = [
    # Storm zone near Sardinia
    DangerZone(
        id=str(uuid.uuid4()),
        type=DangerType.STORM,
        name="Sardinia Storm System",
        coordinates=[
            Coordinate(lat=41.0, lon=8.0),
            Coordinate(lat=41.0, lon=11.0),
            Coordinate(lat=39.0, lon=11.0),
            Coordinate(lat=39.0, lon=8.0),
        ],
        severity=0.6,
        is_restricted=False
    ),
    
    # High waves zone in central Mediterranean
    DangerZone(
        id=str(uuid.uuid4()),
        type=DangerType.HIGH_WAVES,
        name="Central Mediterranean Swells",
        coordinates=[
            Coordinate(lat=37.0, lon=13.0),
            Coordinate(lat=37.0, lon=17.0),
            Coordinate(lat=35.0, lon=17.0),
            Coordinate(lat=35.0, lon=13.0),
        ],
        severity=0.4,
        is_restricted=False
    ),
    
    # Piracy concern area near Libya coast
    DangerZone(
        id=str(uuid.uuid4()),
        type=DangerType.PIRACY,
        name="Libyan Coast Security Zone",
        coordinates=[
            Coordinate(lat=34.0, lon=11.0),
            Coordinate(lat=34.0, lon=20.0),
            Coordinate(lat=32.5, lon=20.0),
            Coordinate(lat=32.5, lon=11.0),
        ],
        severity=0.7,
        is_restricted=False
    ),
    
    # Military restricted area near Cyprus
    DangerZone(
        id=str(uuid.uuid4()),
        type=DangerType.MILITARY,
        name="Cyprus Military Exercise Zone",
        coordinates=[
            Coordinate(lat=35.5, lon=32.5),
            Coordinate(lat=35.5, lon=34.0),
            Coordinate(lat=34.5, lon=34.0),
            Coordinate(lat=34.5, lon=32.5),
        ],
        severity=1.0,
        is_restricted=True
    ),
    
    # Storm zone in Aegean Sea
    DangerZone(
        id=str(uuid.uuid4()),
        type=DangerType.STORM,
        name="Aegean Storm Front",
        coordinates=[
            Coordinate(lat=39.0, lon=24.0),
            Coordinate(lat=39.0, lon=27.0),
            Coordinate(lat=37.0, lon=27.0),
            Coordinate(lat=37.0, lon=24.0),
        ],
        severity=0.5,
        is_restricted=False
    ),
    
    # High wave zone near Strait of Sicily
    DangerZone(
        id=str(uuid.uuid4()),
        type=DangerType.HIGH_WAVES,
        name="Sicily Strait Turbulence",
        coordinates=[
            Coordinate(lat=38.0, lon=10.5),
            Coordinate(lat=38.0, lon=12.5),
            Coordinate(lat=36.5, lon=12.5),
            Coordinate(lat=36.5, lon=10.5),
        ],
        severity=0.35,
        is_restricted=False
    ),
]


def get_default_danger_zones() -> List[DangerZone]:
    """Get the default set of danger zones for the Mediterranean."""
    return DEFAULT_DANGER_ZONES.copy()


def create_storm_zone(
    center_lat: float,
    center_lon: float,
    radius_deg: float = 1.5,
    name: str = "Storm Zone",
    severity: float = 0.5
) -> DangerZone:
    """
    Create a circular storm zone.
    
    Args:
        center_lat: Center latitude
        center_lon: Center longitude  
        radius_deg: Radius in degrees
        name: Name of the zone
        severity: Danger severity 0-1
    
    Returns:
        DangerZone polygon approximating a circle
    """
    import math
    
    # Create polygon approximating circle (16 points)
    coordinates = []
    for i in range(16):
        angle = 2 * math.pi * i / 16
        lat = center_lat + radius_deg * math.sin(angle)
        lon = center_lon + radius_deg * math.cos(angle)
        coordinates.append(Coordinate(lat=lat, lon=lon))
    
    return DangerZone(
        type=DangerType.STORM,
        name=name,
        coordinates=coordinates,
        severity=severity,
        is_restricted=False
    )


def create_piracy_zone(
    coordinates: List[tuple],
    name: str = "Piracy Zone",
    severity: float = 0.7
) -> DangerZone:
    """
    Create a piracy danger zone.
    
    Args:
        coordinates: List of (lat, lon) tuples defining polygon
        name: Name of the zone
        severity: Danger severity 0-1
    
    Returns:
        DangerZone for piracy
    """
    return DangerZone(
        type=DangerType.PIRACY,
        name=name,
        coordinates=[Coordinate(lat=c[0], lon=c[1]) for c in coordinates],
        severity=severity,
        is_restricted=False
    )


def create_military_zone(
    coordinates: List[tuple],
    name: str = "Military Zone",
    is_restricted: bool = True
) -> DangerZone:
    """
    Create a military restricted zone.
    
    Args:
        coordinates: List of (lat, lon) tuples defining polygon
        name: Name of the zone
        is_restricted: If True, zone is completely blocked
    
    Returns:
        DangerZone for military area
    """
    return DangerZone(
        type=DangerType.MILITARY,
        name=name,
        coordinates=[Coordinate(lat=c[0], lon=c[1]) for c in coordinates],
        severity=1.0 if is_restricted else 0.8,
        is_restricted=is_restricted
    )


def get_danger_zone_color(zone: DangerZone) -> str:
    """
    Get the display color for a danger zone type.
    
    Args:
        zone: Danger zone
    
    Returns:
        CSS color string
    """
    if zone.is_restricted:
        return "#EF4444"  # Red - completely blocked
    
    colors = {
        DangerType.STORM: "#EF4444",      # Red
        DangerType.HIGH_WAVES: "#F59E0B",  # Orange  
        DangerType.PIRACY: "#EF4444",      # Red
        DangerType.MILITARY: "#EF4444",    # Red
    }
    
    return colors.get(zone.type, "#EF4444")


def get_danger_zone_opacity(zone: DangerZone) -> float:
    """
    Get the display opacity for a danger zone based on severity.
    
    Args:
        zone: Danger zone
    
    Returns:
        Opacity value 0-1
    """
    if zone.is_restricted:
        return 0.4
    
    # Scale opacity by severity (0.1 to 0.3)
    return 0.1 + (zone.severity * 0.2)
