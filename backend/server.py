"""
Marine Routing System - FastAPI Backend
Main server with A* routing endpoints, authentication, and real-time weather updates.
"""
from fastapi import FastAPI, APIRouter, HTTPException, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone

# Import routing modules
from models import (
    Coordinate, VesselType, WeightConfig,
    VESSEL_CONFIGS, MEDITERRANEAN_PORTS
)
from grid_generator import OceanGrid
from a_star import AStarRouter
from danger_zone import get_danger_zone_color, get_danger_zone_opacity
from weather_simulator import get_weather_simulator
from auth import (
    UserCreate, UserLogin, TokenResponse, UserResponse,
    hash_password, verify_password, create_access_token, get_current_user
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="Marine Routing System", version="1.0.0")

# Create router with /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize global grid and router
# Using 0.5 degree resolution for extended map (Mediterranean + Indian Ocean)
GRID_RESOLUTION = 0.5
ocean_grid = OceanGrid(resolution=GRID_RESOLUTION)
router_instance = AStarRouter(ocean_grid)

# Apply default danger zones
weather_sim = get_weather_simulator()
ocean_grid.apply_danger_zones(weather_sim.get_current_zones())


# ============ Models for API ============

class RouteRequestAPI(BaseModel):
    """API request model for route calculation."""
    source_lat: float
    source_lon: float
    dest_lat: float
    dest_lon: float
    vessel_type: str
    fuel_priority: float = 0.33
    time_priority: float = 0.33
    safety_priority: float = 0.34


class PortInfo(BaseModel):
    """Port information for API response."""
    id: str
    name: str
    lat: float
    lon: float


class VesselInfo(BaseModel):
    """Vessel information for API response."""
    type: str
    name: str
    fuel_consumption_rate: float
    max_speed: float
    storm_tolerance: float
    risk_sensitivity: float
    image_url: Optional[str]


class DangerZoneInfo(BaseModel):
    """Danger zone information for API response."""
    id: str
    type: str
    name: str
    coordinates: List[Dict[str, float]]
    severity: float
    is_restricted: bool
    color: str
    opacity: float


class GridInfo(BaseModel):
    """Grid metadata for API response."""
    rows: int
    cols: int
    resolution: float
    bounds: Dict[str, float]
    water_nodes: int
    danger_nodes: int


# ============ Auth Endpoints (Public) ============

@api_router.post("/auth/signup", response_model=UserResponse, status_code=201)
async def signup(user_data: UserCreate):
    """
    Register a new user account.
    """
    # Check if email already exists
    existing_user = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )
    
    # Check if username already exists
    existing_username = await db.users.find_one({"username": user_data.username}, {"_id": 0})
    if existing_username:
        raise HTTPException(
            status_code=409,
            detail="Username already taken"
        )
    
    # Create user document
    user_id = str(uuid.uuid4())
    hashed_pwd = hash_password(user_data.password)
    created_at = datetime.now(timezone.utc).isoformat()
    
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "username": user_data.username,
        "hashed_password": hashed_pwd,
        "full_name": user_data.full_name,
        "created_at": created_at
    }
    
    await db.users.insert_one(user_doc)
    
    return UserResponse(
        id=user_id,
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        created_at=created_at
    )


@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """
    Authenticate user and issue JWT token.
    """
    # Find user by email
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Verify password
    if not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Generate token
    access_token = create_access_token(
        user_id=user["id"],
        email=user["email"],
        username=user["username"]
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": user["id"],
            "email": user["email"],
            "username": user["username"],
            "full_name": user.get("full_name")
        }
    )


@api_router.get("/auth/me")
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get current authenticated user's profile.
    """
    user = await db.users.find_one({"id": current_user["sub"]}, {"_id": 0, "hashed_password": 0})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


# ============ Public Endpoints ============

@api_router.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Marine Routing System API", "status": "online"}


@api_router.get("/ports", response_model=List[PortInfo])
async def get_ports():
    """Get all available ports."""
    ports = []
    for port_id, port in MEDITERRANEAN_PORTS.items():
        ports.append(PortInfo(
            id=port_id,
            name=port.name,
            lat=port.coordinate.lat,
            lon=port.coordinate.lon
        ))
    return ports


@api_router.get("/vessels", response_model=List[VesselInfo])
async def get_vessels():
    """Get all available vessel types."""
    vessels = []
    for vessel_type, config in VESSEL_CONFIGS.items():
        vessels.append(VesselInfo(
            type=config.type.value,
            name=config.name,
            fuel_consumption_rate=config.fuel_consumption_rate,
            max_speed=config.max_speed,
            storm_tolerance=config.storm_tolerance,
            risk_sensitivity=config.risk_sensitivity,
            image_url=config.image_url
        ))
    return vessels


@api_router.get("/danger-zones", response_model=List[DangerZoneInfo])
async def get_danger_zones():
    """Get current danger zones."""
    zones = weather_sim.get_current_zones()
    result = []
    
    for zone in zones:
        result.append(DangerZoneInfo(
            id=zone.id,
            type=zone.type.value,
            name=zone.name,
            coordinates=[{"lat": c.lat, "lon": c.lon} for c in zone.coordinates],
            severity=zone.severity,
            is_restricted=zone.is_restricted,
            color=get_danger_zone_color(zone),
            opacity=get_danger_zone_opacity(zone)
        ))
    
    return result


@api_router.get("/grid-info", response_model=GridInfo)
async def get_grid_info():
    """Get ocean grid metadata."""
    info = ocean_grid.get_grid_info()
    return GridInfo(
        rows=info["rows"],
        cols=info["cols"],
        resolution=info["resolution"],
        bounds=info["bounds"],
        water_nodes=info["water_nodes"],
        danger_nodes=info["danger_nodes"]
    )


# ============ Protected Endpoints (Require Login) ============

@api_router.post("/calculate-route")
async def calculate_route(
    request: RouteRequestAPI,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Calculate optimal route using A* algorithm.
    REQUIRES AUTHENTICATION.
    
    The route considers:
    - Fuel consumption based on vessel type
    - Travel time based on speed and conditions
    - Safety risk from danger zones
    - User-defined priority weights
    """
    try:
        # Validate vessel type
        try:
            vessel_type = VesselType(request.vessel_type)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid vessel type: {request.vessel_type}"
            )
        
        # Create source and destination coordinates
        source = Coordinate(lat=request.source_lat, lon=request.source_lon)
        destination = Coordinate(lat=request.dest_lat, lon=request.dest_lon)
        
        # Create weight configuration
        weights = WeightConfig(
            fuel_priority=request.fuel_priority,
            time_priority=request.time_priority,
            safety_priority=request.safety_priority
        )
        
        logger.info(f"User {current_user['username']} calculating route from "
                   f"({source.lat:.2f}, {source.lon:.2f}) to ({destination.lat:.2f}, {destination.lon:.2f})")
        
        # Calculate route
        result = router_instance.find_route(source, destination, vessel_type, weights)
        
        # Convert to API response format
        response = {
            "success": result.success,
            "path": [
                {
                    "lat": p.lat,
                    "lon": p.lon,
                    "cumulative_distance": p.cumulative_distance,
                    "cumulative_time": p.cumulative_time,
                    "cumulative_fuel": p.cumulative_fuel,
                    "local_danger": p.local_danger
                }
                for p in result.path
            ],
            "total_distance": result.total_distance,
            "total_time": result.total_time,
            "total_fuel": result.total_fuel,
            "average_risk": result.average_risk,
            "total_cost": result.total_cost,
            "vessel_type": result.vessel_type.value,
            "message": result.message,
            "waypoints": len(result.path)
        }
        
        # Store route in database for history
        route_doc = {
            "id": str(uuid.uuid4()),
            "user_id": current_user["sub"],
            "username": current_user["username"],
            "source": {"lat": source.lat, "lon": source.lon},
            "destination": {"lat": destination.lat, "lon": destination.lon},
            "vessel_type": vessel_type.value,
            "total_distance": result.total_distance,
            "total_time": result.total_time,
            "total_fuel": result.total_fuel,
            "average_risk": result.average_risk,
            "calculated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.route_history.insert_one(route_doc)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Route calculation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/simulate-weather")
async def simulate_weather(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Simulate a weather change event.
    REQUIRES AUTHENTICATION.
    """
    try:
        # Simulate weather change
        update = weather_sim.simulate_weather_change()
        
        # Apply new zones to grid
        ocean_grid.apply_danger_zones(update.danger_zones)
        
        # Format response
        zones = []
        for zone in update.danger_zones:
            zones.append({
                "id": zone.id,
                "type": zone.type.value,
                "name": zone.name,
                "coordinates": [{"lat": c.lat, "lon": c.lon} for c in zone.coordinates],
                "severity": zone.severity,
                "is_restricted": zone.is_restricted,
                "color": get_danger_zone_color(zone),
                "opacity": get_danger_zone_opacity(zone)
            })
        
        return {
            "message": update.message,
            "timestamp": update.timestamp.isoformat(),
            "danger_zones": zones
        }
        
    except Exception as e:
        logger.error(f"Weather simulation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/reset-weather")
async def reset_weather(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Reset weather to default conditions. REQUIRES AUTHENTICATION."""
    try:
        update = weather_sim.reset_to_default()
        ocean_grid.apply_danger_zones(update.danger_zones)
        
        zones = []
        for zone in update.danger_zones:
            zones.append({
                "id": zone.id,
                "type": zone.type.value,
                "name": zone.name,
                "coordinates": [{"lat": c.lat, "lon": c.lon} for c in zone.coordinates],
                "severity": zone.severity,
                "is_restricted": zone.is_restricted,
                "color": get_danger_zone_color(zone),
                "opacity": get_danger_zone_opacity(zone)
            })
        
        return {
            "message": update.message,
            "timestamp": update.timestamp.isoformat(),
            "danger_zones": zones
        }
        
    except Exception as e:
        logger.error(f"Weather reset error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/route-history")
async def get_route_history(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get user's route calculation history. REQUIRES AUTHENTICATION."""
    try:
        history = await db.route_history.find(
            {"user_id": current_user["sub"]}, 
            {"_id": 0}
        ).sort("calculated_at", -1).limit(10).to_list(10)
        
        return {"routes": history}
        
    except Exception as e:
        logger.error(f"Route history error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Include router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
