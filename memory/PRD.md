# Marine Routing System - Product Requirements Document

## Original Problem Statement
Build a real A* based marine routing system using Python (FastAPI). The system must NOT draw a straight line between source and destination. It must generate a navigable ocean grid and compute optimal path using A* search with travel_time_cost, fuel_cost, and safety_risk_cost.

## Architecture

### Backend (Python/FastAPI)
```
/app/backend/
├── server.py          # Main FastAPI application
├── models.py          # Pydantic models for all data structures
├── grid_generator.py  # Ocean grid with 8-neighbor connectivity
├── cost_function.py   # g(n) calculation with time/fuel/safety costs
├── a_star.py         # A* pathfinding implementation
├── danger_zone.py    # Danger zone definitions and utilities
└── weather_simulator.py # Dynamic weather simulation
```

### Frontend (React + Leaflet)
- Dark nautical theme
- Interactive map with Leaflet
- Vessel selection cards
- Priority weight sliders
- Route statistics overlay
- Animated vessel marker

## User Personas
1. **Maritime Logistics Planner** - Plans optimal shipping routes considering fuel, time, and safety
2. **Ship Captain** - Needs real-time route adjustments based on weather changes
3. **Shipping Company Manager** - Compares vessel types for route optimization

## Core Requirements (Static)
1. ✅ Ocean Grid System - 2D lat/lon grid with 8-neighbor connectivity
2. ✅ A* Implementation - f(n) = g(n) + h(n) with proper cost calculation
3. ✅ Danger Zone Modeling - Storm, piracy, military zones with severity levels
4. ✅ Vessel Types - 4 vessels with different performance characteristics
5. ✅ Dynamic Weights - Sliders for fuel/time/safety priorities
6. ✅ Map Visualization - Leaflet with dark theme, danger zones, routes
7. ✅ Real-Time Recalculation - Weather changes trigger route updates

## What's Been Implemented (January 2026)

### MVP Complete - All Features Implemented
- **Grid System**: Mediterranean Sea coverage (30°-46°N, -6°-36°E), 0.5° resolution
- **A* Routing**: Real pathfinding with 65 waypoints for Barcelona-Alexandria (~3228km)
- **Cost Function**: Weighted combination of time, fuel, and safety risk
- **Danger Zones**: 6 predefined zones (storms, piracy, military)
- **4 Vessel Types**: Cargo Ship, Oil Tanker, Fishing Boat, High Speed Boat
- **Weather Simulation**: Dynamic zone updates with route recalculation
- **Dark Nautical UI**: Professional command center aesthetic
- **Statistics Panel**: Distance, time, fuel usage, risk percentage
- **Vessel Animation**: Marker moves along calculated route

## API Endpoints
- GET `/api/ports` - List Mediterranean ports
- GET `/api/vessels` - List vessel configurations
- GET `/api/danger-zones` - Current danger zones
- GET `/api/grid-info` - Grid metadata
- POST `/api/calculate-route` - A* route calculation
- POST `/api/simulate-weather` - Trigger weather change
- POST `/api/reset-weather` - Reset to default zones
- GET `/api/route-history` - Recent calculations

## Prioritized Backlog
### P0 - Core (Implemented)
- [x] A* pathfinding with curved routes
- [x] Danger zone avoidance
- [x] Multi-vessel support
- [x] Priority weight controls

### P1 - Enhanced Features (Future)
- [ ] Real-time AIS vessel tracking integration
- [ ] Historical weather data integration
- [ ] Route comparison mode
- [ ] Export routes to navigation format (GPX/KML)

### P2 - Advanced Features (Future)
- [ ] Multi-stop route optimization
- [ ] Fuel station planning
- [ ] Port congestion data
- [ ] Emission calculations

## Test Results
- Backend: 100% (11/11 tests passed)
- Frontend: 95% (all features confirmed working)
- Overall: 98% success rate

## Next Tasks
1. Add route export functionality (GPX format)
2. Implement route comparison between vessels
3. Add real weather API integration
4. Enhanced mobile responsive design
