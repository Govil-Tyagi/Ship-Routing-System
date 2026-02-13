"""
Cost Function Module for Marine Routing A* Algorithm
Calculates g(n) cost including travel_time, fuel, and safety costs.
"""
import math
from typing import Tuple
from models import VesselConfig, WeightConfig, GridNode


# Earth radius in kilometers
EARTH_RADIUS_KM = 6371.0


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth.
    Uses the Haversine formula for accurate distance calculation.
    
    Args:
        lat1, lon1: First point coordinates in degrees
        lat2, lon2: Second point coordinates in degrees
    
    Returns:
        Distance in kilometers
    """
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = (math.sin(delta_lat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * 
         math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return EARTH_RADIUS_KM * c


def calculate_travel_time(distance_km: float, vessel: VesselConfig, danger_level: float) -> float:
    """
    Calculate travel time between two nodes.
    
    Travel time is affected by:
    - Base speed of vessel
    - Danger level (storms reduce speed)
    
    Args:
        distance_km: Distance to travel
        vessel: Vessel configuration
        danger_level: Danger level at destination (0-1)
    
    Returns:
        Time in hours
    """
    # Speed reduction factor based on danger and vessel tolerance
    # More danger = slower travel, but tolerant vessels are less affected
    speed_reduction = 1.0 - (danger_level * (1.0 - vessel.storm_tolerance))
    effective_speed = vessel.max_speed * max(0.3, speed_reduction)  # Min 30% speed
    
    return distance_km / effective_speed


def calculate_fuel_cost(distance_km: float, vessel: VesselConfig, danger_level: float) -> float:
    """
    Calculate fuel consumption between two nodes.
    
    Fuel consumption is affected by:
    - Base consumption rate
    - Distance
    - Danger level (rough conditions increase consumption)
    
    Args:
        distance_km: Distance to travel
        vessel: Vessel configuration  
        danger_level: Danger level at destination (0-1)
    
    Returns:
        Fuel in liters
    """
    # Fuel multiplier based on conditions
    # Rough conditions (high danger) increase fuel consumption
    fuel_multiplier = 1.0 + (danger_level * 0.5)  # Up to 50% more fuel
    
    return distance_km * vessel.fuel_consumption_rate * fuel_multiplier


def calculate_safety_risk(danger_level: float, vessel: VesselConfig) -> float:
    """
    Calculate safety risk cost for traversing a dangerous area.
    
    Risk is based on:
    - Danger level of the node
    - Vessel's risk sensitivity
    - Vessel's storm tolerance
    
    Args:
        danger_level: Danger level at node (0-1)
        vessel: Vessel configuration
    
    Returns:
        Risk cost (normalized 0-1, then scaled)
    """
    if danger_level == 0:
        return 0.0
    
    # Base risk from danger level
    base_risk = danger_level
    
    # Adjust by vessel tolerance (inverse relationship)
    tolerance_factor = 1.0 - vessel.storm_tolerance
    
    # Apply vessel's risk sensitivity
    risk = base_risk * (1.0 + tolerance_factor) * vessel.risk_sensitivity
    
    return min(1.0, risk)


def calculate_g_cost(
    from_node: GridNode,
    to_node: GridNode,
    vessel: VesselConfig,
    weights: WeightConfig,
    current_g: float
) -> Tuple[float, float, float, float]:
    """
    Calculate the g(n) cost from current node to neighbor.
    
    g(n) = current_g + weighted_sum(travel_time_cost, fuel_cost, safety_risk_cost)
    
    The weights control the trade-off between:
    - Speed (minimize time)
    - Economy (minimize fuel)
    - Safety (minimize risk)
    
    Args:
        from_node: Current node
        to_node: Neighbor node being evaluated
        vessel: Vessel configuration
        weights: Weight configuration for priorities
        current_g: Current accumulated g cost
    
    Returns:
        Tuple of (new_g_cost, distance, time, fuel)
    """
    # Calculate base distance
    distance = haversine_distance(
        from_node.lat, from_node.lon,
        to_node.lat, to_node.lon
    )
    
    # Calculate individual cost components
    time = calculate_travel_time(distance, vessel, to_node.danger_level)
    fuel = calculate_fuel_cost(distance, vessel, to_node.danger_level)
    risk = calculate_safety_risk(to_node.danger_level, vessel)
    
    # Normalize costs to similar scales for fair comparison
    # Time: normalize by assuming typical segment is 50km at max speed
    time_normalized = time / (50.0 / vessel.max_speed)
    
    # Fuel: normalize by typical segment consumption
    fuel_normalized = fuel / (50.0 * vessel.fuel_consumption_rate)
    
    # Risk is already 0-1
    
    # Calculate weighted cost
    # Note: Weights are expected to sum to ~1.0 but we normalize anyway
    total_weight = weights.fuel_priority + weights.time_priority + weights.safety_priority
    if total_weight == 0:
        total_weight = 1.0
    
    weighted_cost = (
        (weights.time_priority / total_weight) * time_normalized +
        (weights.fuel_priority / total_weight) * fuel_normalized +
        (weights.safety_priority / total_weight) * risk * 10.0  # Scale up risk impact
    )
    
    # Scale to make costs reasonable
    step_cost = weighted_cost * distance
    
    return current_g + step_cost, distance, time, fuel


def calculate_heuristic(node: GridNode, goal: GridNode) -> float:
    """
    Calculate h(n) - admissible heuristic using Haversine distance.
    
    This is admissible because it represents the straight-line distance,
    which is always <= actual path cost (shortest possible distance).
    
    Args:
        node: Current node
        goal: Goal node
    
    Returns:
        Heuristic cost estimate
    """
    return haversine_distance(node.lat, node.lon, goal.lat, goal.lon)
