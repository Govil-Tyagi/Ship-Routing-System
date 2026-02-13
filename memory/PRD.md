# Marine Routing System - Product Requirements Document

## Original Problem Statement
Build a real A* based marine routing system using Python (FastAPI). The system must NOT draw a straight line between source and destination. It must generate a navigable ocean grid and compute optimal path using A* search with travel_time_cost, fuel_cost, and safety_risk_cost.

**Update (Jan 2026)**: Added JWT authentication (login/signup) and 8 Indian ports.

## Architecture

### Backend (Python/FastAPI)
```
/app/backend/
├── server.py          # Main FastAPI application with auth
├── auth.py            # JWT authentication module
├── models.py          # Pydantic models + Mediterranean + Indian ports
├── grid_generator.py  # Ocean grid covering Mediterranean + Indian Ocean
├── cost_function.py   # g(n) calculation with time/fuel/safety costs
├── a_star.py         # A* pathfinding implementation
├── danger_zone.py    # Danger zone definitions and utilities
└── weather_simulator.py # Dynamic weather simulation
```

### Frontend (React + Leaflet)
```
/app/frontend/src/
├── App.js             # Main app with protected routes
├── context/AuthContext.js  # Authentication context
├── pages/LoginPage.js      # Login page
├── pages/SignupPage.js     # Signup page
└── components/ui/     # Shadcn UI components
```

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
8. ✅ JWT Authentication - Login/Signup with protected routes
9. ✅ Indian Ports - 8 major Indian ports added

## What's Been Implemented (January 2026)

### Phase 1 - MVP Complete
- Grid System: Mediterranean Sea coverage
- A* Routing: Real pathfinding with multiple waypoints
- 4 Vessel Types: Cargo Ship, Oil Tanker, Fishing Boat, High Speed Boat
- Weather Simulation: Dynamic zone updates
- Dark Nautical UI: Professional command center aesthetic

### Phase 2 - Auth + Indian Ports
- JWT Authentication with bcrypt password hashing
- Login and Signup pages with dark theme
- Protected route calculation (requires login)
- Extended grid to cover Indian Ocean (5°N-46°N, -6°E-95°E)
- Added 8 Indian Ports:
  - Mumbai, Chennai, Kolkata, Cochin
  - Visakhapatnam, Kandla, Mangalore, Tuticorin

## API Endpoints

### Public Endpoints
- GET `/api/` - Health check
- GET `/api/ports` - List all ports (Mediterranean + Indian)
- GET `/api/vessels` - List vessel configurations
- GET `/api/danger-zones` - Current danger zones
- POST `/api/auth/signup` - Create new account
- POST `/api/auth/login` - Get JWT token

### Protected Endpoints (Require JWT)
- GET `/api/auth/me` - Get current user profile
- POST `/api/calculate-route` - A* route calculation
- POST `/api/simulate-weather` - Trigger weather change
- POST `/api/reset-weather` - Reset to default zones
- GET `/api/route-history` - User's route history

## Test Results
- Backend: 90.9% (minor 403/401 difference, no functional impact)
- Frontend: 95% (all features confirmed working)
- Indian ports routing: Mumbai to Chennai = 2993.9km, 49 waypoints

## Prioritized Backlog
### P0 - Core (Implemented)
- [x] A* pathfinding with curved routes
- [x] JWT authentication system
- [x] Indian ports integration
- [x] Protected route calculation

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

## Next Tasks
1. Add route export functionality (GPX format)
2. Implement route comparison between vessels
3. Add real weather API integration
4. Password reset functionality
