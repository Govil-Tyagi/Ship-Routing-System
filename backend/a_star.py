"""
A* Pathfinding Algorithm for Marine Routing
Implements real grid-based traversal with proper cost calculation.
"""
import heapq
from typing import List, Dict, Tuple, Optional
from models import (
    GridNode, Coordinate, VesselConfig, WeightConfig, 
    RoutePoint, RouteResult, VesselType, VESSEL_CONFIGS
)
from grid_generator import OceanGrid
from cost_function import calculate_g_cost, calculate_heuristic, haversine_distance
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class AStarRouter:
    """
    A* pathfinding implementation for marine routing.
    
    Uses f(n) = g(n) + h(n) where:
    - g(n) includes travel_time_cost, fuel_cost, safety_risk_cost
    - h(n) is Haversine distance to destination (admissible heuristic)
    """
    
    def __init__(self, grid: OceanGrid):
        """
        Initialize the A* router with an ocean grid.
        
        Args:
            grid: OceanGrid instance with navigable nodes
        """
        self.grid = grid
    
    def find_route(
        self,
        source: Coordinate,
        destination: Coordinate,
        vessel_type: VesselType,
        weights: WeightConfig
    ) -> RouteResult:
        """
        Find optimal route using A* algorithm.
        
        Args:
            source: Starting coordinate
            destination: Target coordinate
            vessel_type: Type of vessel for cost calculation
            weights: Weight priorities for fuel/time/safety
        
        Returns:
            RouteResult with path and statistics
        """
        # Get vessel configuration
        vessel = VESSEL_CONFIGS[vessel_type]
        
        # Find nearest navigable nodes for source and destination
        start_node = self.grid.find_nearest_water_node(source.lat, source.lon)
        goal_node = self.grid.find_nearest_water_node(destination.lat, destination.lon)
        
        if not start_node:
            return RouteResult(
                success=False,
                path=[],
                total_distance=0,
                total_time=0,
                total_fuel=0,
                average_risk=0,
                total_cost=0,
                vessel_type=vessel_type,
                message="Could not find navigable water near source"
            )
        
        if not goal_node:
            return RouteResult(
                success=False,
                path=[],
                total_distance=0,
                total_time=0,
                total_fuel=0,
                average_risk=0,
                total_cost=0,
                vessel_type=vessel_type,
                message="Could not find navigable water near destination"
            )
        
        logger.info(f"Starting A* from ({start_node.lat:.2f}, {start_node.lon:.2f}) "
                   f"to ({goal_node.lat:.2f}, {goal_node.lon:.2f})")
        
        # A* data structures
        # Priority queue entries: (f_cost, counter, row, col)
        # Counter is used to break ties deterministically
        open_set = []
        counter = 0
        
        # Track best g-cost to each node
        g_costs: Dict[Tuple[int, int], float] = {}
        
        # Track parent nodes for path reconstruction
        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        
        # Track accumulated distance, time, fuel for each node
        node_stats: Dict[Tuple[int, int], Tuple[float, float, float]] = {}
        
        # Initialize start node
        start_key = (start_node.row, start_node.col)
        goal_key = (goal_node.row, goal_node.col)
        
        g_costs[start_key] = 0
        node_stats[start_key] = (0, 0, 0)  # distance, time, fuel
        
        h_cost = calculate_heuristic(start_node, goal_node)
        f_cost = h_cost
        
        heapq.heappush(open_set, (f_cost, counter, start_node.row, start_node.col))
        counter += 1
        
        # Track visited nodes
        closed_set = set()
        
        # A* main loop
        iterations = 0
        max_iterations = 100000  # Safety limit
        
        while open_set and iterations < max_iterations:
            iterations += 1
            
            # Get node with lowest f-cost
            _, _, current_row, current_col = heapq.heappop(open_set)
            current_key = (current_row, current_col)
            
            # Skip if already processed
            if current_key in closed_set:
                continue
            
            closed_set.add(current_key)
            current_node = self.grid.grid[current_row][current_col]
            
            # Check if we reached the goal
            if current_key == goal_key:
                logger.info(f"A* found path in {iterations} iterations")
                return self._reconstruct_path(
                    came_from, node_stats, start_key, goal_key,
                    vessel_type, weights
                )
            
            # Explore neighbors
            neighbors = self.grid.get_neighbors(current_row, current_col)
            
            for neighbor_row, neighbor_col, direction in neighbors:
                neighbor_key = (neighbor_row, neighbor_col)
                
                if neighbor_key in closed_set:
                    continue
                
                neighbor_node = self.grid.grid[neighbor_row][neighbor_col]
                
                # Calculate g-cost to this neighbor
                new_g, step_dist, step_time, step_fuel = calculate_g_cost(
                    current_node, neighbor_node, vessel, weights, g_costs[current_key]
                )
                
                # Check if this is a better path
                if neighbor_key not in g_costs or new_g < g_costs[neighbor_key]:
                    # Update best path to this node
                    g_costs[neighbor_key] = new_g
                    came_from[neighbor_key] = current_key
                    
                    # Track accumulated stats
                    curr_dist, curr_time, curr_fuel = node_stats[current_key]
                    node_stats[neighbor_key] = (
                        curr_dist + step_dist,
                        curr_time + step_time,
                        curr_fuel + step_fuel
                    )
                    
                    # Calculate f-cost and add to open set
                    h = calculate_heuristic(neighbor_node, goal_node)
                    f = new_g + h
                    
                    heapq.heappush(open_set, (f, counter, neighbor_row, neighbor_col))
                    counter += 1
        
        # No path found
        logger.warning(f"A* failed after {iterations} iterations")
        return RouteResult(
            success=False,
            path=[],
            total_distance=0,
            total_time=0,
            total_fuel=0,
            average_risk=0,
            total_cost=0,
            vessel_type=vessel_type,
            message=f"No navigable path found after {iterations} iterations"
        )
    
    def _reconstruct_path(
        self,
        came_from: Dict[Tuple[int, int], Tuple[int, int]],
        node_stats: Dict[Tuple[int, int], Tuple[float, float, float]],
        start_key: Tuple[int, int],
        goal_key: Tuple[int, int],
        vessel_type: VesselType,
        weights: WeightConfig
    ) -> RouteResult:
        """
        Reconstruct the path from A* results.
        
        Args:
            came_from: Parent pointers
            node_stats: Accumulated stats for each node
            start_key: Start node key
            goal_key: Goal node key
            vessel_type: Type of vessel
            weights: Weight configuration
        
        Returns:
            Complete RouteResult with path
        """
        # Reconstruct path from goal to start
        path_keys = []
        current = goal_key
        
        while current != start_key:
            path_keys.append(current)
            current = came_from[current]
        path_keys.append(start_key)
        
        # Reverse to get start-to-goal order
        path_keys.reverse()
        
        # Build route points
        path = []
        total_danger = 0.0
        
        for key in path_keys:
            row, col = key
            node = self.grid.grid[row][col]
            dist, time, fuel = node_stats[key]
            
            point = RoutePoint(
                lat=node.lat,
                lon=node.lon,
                cumulative_distance=round(dist, 2),
                cumulative_time=round(time, 3),
                cumulative_fuel=round(fuel, 2),
                local_danger=node.danger_level
            )
            path.append(point)
            total_danger += node.danger_level
        
        # Get final stats
        final_dist, final_time, final_fuel = node_stats[goal_key]
        avg_risk = total_danger / len(path) if path else 0
        
        # Calculate total cost (normalized)
        vessel = VESSEL_CONFIGS[vessel_type]
        base_cost = (
            weights.fuel_priority * final_fuel +
            weights.time_priority * final_time * 10 +
            weights.safety_priority * avg_risk * 1000
        )
        
        return RouteResult(
            success=True,
            path=path,
            total_distance=round(final_dist, 2),
            total_time=round(final_time, 2),
            total_fuel=round(final_fuel, 2),
            average_risk=round(avg_risk, 3),
            total_cost=round(base_cost, 2),
            vessel_type=vessel_type,
            message=f"Route found with {len(path)} waypoints"
        )
