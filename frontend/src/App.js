import React, { useState, useEffect, useCallback, useRef } from 'react';
import { MapContainer, TileLayer, Polyline, Polygon, Marker, Popup, Tooltip, useMap } from 'react-leaflet';
import L from 'leaflet';
import axios from 'axios';
import { Toaster, toast } from 'sonner';
import { 
  Anchor, Ship, Fuel, Clock, LifeBuoy, AlertTriangle, 
  CloudLightning, Skull, ShieldAlert, Wind, RefreshCw,
  Navigation, Compass, MapPin
} from 'lucide-react';
import { Slider } from './components/ui/slider';
import { Button } from './components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Card, CardContent } from './components/ui/card';
import { Badge } from './components/ui/badge';
import '@/App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Custom vessel marker icon
const createVesselIcon = () => {
  return L.divIcon({
    className: 'vessel-marker-container',
    html: `<div class="vessel-marker"></div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12]
  });
};

// Port marker icon
const createPortIcon = (isSource) => {
  return L.divIcon({
    className: 'port-marker-container',
    html: `<div style="width: 14px; height: 14px; background: ${isSource ? '#10B981' : '#EF4444'}; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 8px ${isSource ? '#10B981' : '#EF4444'};"></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7]
  });
};

// Map bounds fitter component
function MapBoundsFitter({ route }) {
  const map = useMap();
  
  useEffect(() => {
    if (route && route.length > 0) {
      const bounds = L.latLngBounds(route.map(p => [p.lat, p.lon]));
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [route, map]);
  
  return null;
}

// Animated vessel marker component
function AnimatedVessel({ route, isAnimating }) {
  const [position, setPosition] = useState(null);
  const animationRef = useRef(null);
  const indexRef = useRef(0);
  
  useEffect(() => {
    if (!isAnimating || !route || route.length === 0) {
      if (animationRef.current) {
        clearInterval(animationRef.current);
      }
      setPosition(null);
      indexRef.current = 0;
      return;
    }
    
    setPosition([route[0].lat, route[0].lon]);
    indexRef.current = 0;
    
    animationRef.current = setInterval(() => {
      indexRef.current += 1;
      if (indexRef.current >= route.length) {
        indexRef.current = 0;
      }
      setPosition([route[indexRef.current].lat, route[indexRef.current].lon]);
    }, 200);
    
    return () => {
      if (animationRef.current) {
        clearInterval(animationRef.current);
      }
    };
  }, [route, isAnimating]);
  
  if (!position) return null;
  
  return (
    <Marker position={position} icon={createVesselIcon()}>
      <Tooltip permanent direction="top" offset={[0, -15]}>
        <div className="font-mono text-xs">
          {position[0].toFixed(2)}°N, {position[1].toFixed(2)}°E
        </div>
      </Tooltip>
    </Marker>
  );
}

function App() {
  // State
  const [ports, setPorts] = useState([]);
  const [vessels, setVessels] = useState([]);
  const [dangerZones, setDangerZones] = useState([]);
  const [selectedVessel, setSelectedVessel] = useState('cargo_ship');
  const [sourcePort, setSourcePort] = useState('barcelona');
  const [destPort, setDestPort] = useState('alexandria');
  const [priorities, setPriorities] = useState({
    fuel: 0.33,
    time: 0.33,
    safety: 0.34
  });
  const [route, setRoute] = useState(null);
  const [routeStats, setRouteStats] = useState(null);
  const [isCalculating, setIsCalculating] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);
  const [weatherAlert, setWeatherAlert] = useState(null);
  
  // Mediterranean center
  const mapCenter = [38.0, 15.0];
  const mapZoom = 5;
  
  // Load initial data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [portsRes, vesselsRes, zonesRes] = await Promise.all([
          axios.get(`${API}/ports`),
          axios.get(`${API}/vessels`),
          axios.get(`${API}/danger-zones`)
        ]);
        
        setPorts(portsRes.data);
        setVessels(vesselsRes.data);
        setDangerZones(zonesRes.data);
      } catch (error) {
        console.error('Failed to load initial data:', error);
        toast.error('Failed to connect to server');
      }
    };
    
    fetchData();
  }, []);
  
  // Calculate route
  const calculateRoute = useCallback(async () => {
    const source = ports.find(p => p.id === sourcePort);
    const dest = ports.find(p => p.id === destPort);
    
    if (!source || !dest) {
      toast.error('Please select both source and destination ports');
      return;
    }
    
    setIsCalculating(true);
    setIsAnimating(false);
    
    try {
      const response = await axios.post(`${API}/calculate-route`, {
        source_lat: source.lat,
        source_lon: source.lon,
        dest_lat: dest.lat,
        dest_lon: dest.lon,
        vessel_type: selectedVessel,
        fuel_priority: priorities.fuel,
        time_priority: priorities.time,
        safety_priority: priorities.safety
      });
      
      if (response.data.success) {
        setRoute(response.data.path);
        setRouteStats({
          distance: response.data.total_distance,
          time: response.data.total_time,
          fuel: response.data.total_fuel,
          risk: response.data.average_risk,
          cost: response.data.total_cost,
          waypoints: response.data.waypoints
        });
        toast.success(`Route calculated: ${response.data.waypoints} waypoints`);
        setIsAnimating(true);
      } else {
        toast.error(response.data.message || 'Failed to calculate route');
        setRoute(null);
        setRouteStats(null);
      }
    } catch (error) {
      console.error('Route calculation error:', error);
      toast.error('Failed to calculate route');
    } finally {
      setIsCalculating(false);
    }
  }, [sourcePort, destPort, selectedVessel, priorities, ports]);
  
  // Simulate weather change
  const simulateWeather = useCallback(async () => {
    try {
      const response = await axios.post(`${API}/simulate-weather`);
      setDangerZones(response.data.danger_zones);
      setWeatherAlert({
        message: response.data.message,
        timestamp: new Date(response.data.timestamp)
      });
      toast.warning(response.data.message, { icon: <CloudLightning size={18} /> });
      
      // Clear alert after 5 seconds
      setTimeout(() => setWeatherAlert(null), 5000);
      
      // Recalculate route if one exists
      if (route) {
        toast.info('Recalculating route due to weather change...');
        setTimeout(calculateRoute, 500);
      }
    } catch (error) {
      console.error('Weather simulation error:', error);
      toast.error('Failed to simulate weather');
    }
  }, [route, calculateRoute]);
  
  // Reset weather
  const resetWeather = useCallback(async () => {
    try {
      const response = await axios.post(`${API}/reset-weather`);
      setDangerZones(response.data.danger_zones);
      toast.success('Weather reset to default conditions');
    } catch (error) {
      console.error('Weather reset error:', error);
      toast.error('Failed to reset weather');
    }
  }, []);
  
  // Get danger zone icon
  const getDangerIcon = (type) => {
    switch (type) {
      case 'storm': return <CloudLightning size={14} />;
      case 'piracy': return <Skull size={14} />;
      case 'military': return <ShieldAlert size={14} />;
      case 'high_waves': return <Wind size={14} />;
      default: return <AlertTriangle size={14} />;
    }
  };
  
  // Get risk level
  const getRiskLevel = (risk) => {
    if (risk < 0.2) return { level: 'low', color: '#10B981', label: 'Low' };
    if (risk < 0.5) return { level: 'medium', color: '#F59E0B', label: 'Medium' };
    return { level: 'high', color: '#EF4444', label: 'High' };
  };
  
  // Handle priority change
  const handlePriorityChange = (key, value) => {
    const newValue = value[0] / 100;
    const total = Object.entries(priorities)
      .filter(([k]) => k !== key)
      .reduce((sum, [, v]) => sum + v, 0);
    
    // Normalize other values
    const remaining = 1 - newValue;
    const scale = total > 0 ? remaining / total : 0;
    
    const newPriorities = {};
    Object.entries(priorities).forEach(([k, v]) => {
      if (k === key) {
        newPriorities[k] = newValue;
      } else {
        newPriorities[k] = total > 0 ? v * scale : remaining / 2;
      }
    });
    
    setPriorities(newPriorities);
  };

  return (
    <div className="app-container" data-testid="marine-routing-app">
      <Toaster position="top-right" richColors />
      
      {/* Control Panel */}
      <div className="control-panel" data-testid="control-panel">
        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-sky-500/20 rounded">
            <Navigation className="text-sky-400" size={24} />
          </div>
          <div>
            <h1 className="font-heading text-xl font-bold text-slate-100">Marine Router</h1>
            <p className="text-xs text-slate-400">A* Pathfinding System</p>
          </div>
        </div>
        
        {/* Port Selection */}
        <div className="space-y-3">
          <div className="section-header">Route Selection</div>
          
          <div className="port-row">
            <div className="port-indicator source"></div>
            <Select value={sourcePort} onValueChange={setSourcePort} data-testid="source-port-select">
              <SelectTrigger className="flex-1 bg-slate-800 border-slate-700 text-slate-100">
                <SelectValue placeholder="Source Port" />
              </SelectTrigger>
              <SelectContent className="bg-slate-800 border-slate-700">
                {ports.map(port => (
                  <SelectItem key={port.id} value={port.id} className="text-slate-100 hover:bg-slate-700">
                    {port.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          <div className="port-row">
            <div className="port-indicator destination"></div>
            <Select value={destPort} onValueChange={setDestPort} data-testid="dest-port-select">
              <SelectTrigger className="flex-1 bg-slate-800 border-slate-700 text-slate-100">
                <SelectValue placeholder="Destination Port" />
              </SelectTrigger>
              <SelectContent className="bg-slate-800 border-slate-700">
                {ports.map(port => (
                  <SelectItem key={port.id} value={port.id} className="text-slate-100 hover:bg-slate-700">
                    {port.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        
        {/* Vessel Selection */}
        <div className="space-y-3">
          <div className="section-header">Vessel Type</div>
          <div className="vessel-grid">
            {vessels.map(vessel => (
              <Card 
                key={vessel.type}
                className={`cursor-pointer transition-all vessel-card ${selectedVessel === vessel.type ? 'ring-2 ring-sky-500 bg-sky-500/10' : 'bg-slate-800/50 hover:bg-slate-800'}`}
                onClick={() => setSelectedVessel(vessel.type)}
                data-testid={`vessel-card-${vessel.type}`}
              >
                <CardContent className="p-2">
                  <div className="aspect-video mb-2 rounded overflow-hidden bg-slate-900">
                    <img 
                      src={vessel.image_url} 
                      alt={vessel.name}
                      className="w-full h-full object-cover opacity-80"
                    />
                  </div>
                  <div className="text-xs font-medium text-slate-100 truncate">{vessel.name}</div>
                  <div className="text-[10px] text-slate-400 font-mono">{vessel.max_speed} km/h</div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
        
        {/* Priority Sliders */}
        <div className="space-y-4">
          <div className="section-header">Priority Weights</div>
          
          <div className="priority-slider">
            <div className="priority-label">
              <span><Fuel size={14} className="text-amber-400" /> Fuel Economy</span>
              <span>{Math.round(priorities.fuel * 100)}%</span>
            </div>
            <Slider
              value={[priorities.fuel * 100]}
              onValueChange={(v) => handlePriorityChange('fuel', v)}
              max={100}
              step={1}
              className="slider-track"
              data-testid="fuel-priority-slider"
            />
          </div>
          
          <div className="priority-slider">
            <div className="priority-label">
              <span><Clock size={14} className="text-sky-400" /> Time Priority</span>
              <span>{Math.round(priorities.time * 100)}%</span>
            </div>
            <Slider
              value={[priorities.time * 100]}
              onValueChange={(v) => handlePriorityChange('time', v)}
              max={100}
              step={1}
              className="slider-track"
              data-testid="time-priority-slider"
            />
          </div>
          
          <div className="priority-slider">
            <div className="priority-label">
              <span><LifeBuoy size={14} className="text-emerald-400" /> Safety Priority</span>
              <span>{Math.round(priorities.safety * 100)}%</span>
            </div>
            <Slider
              value={[priorities.safety * 100]}
              onValueChange={(v) => handlePriorityChange('safety', v)}
              max={100}
              step={1}
              className="slider-track"
              data-testid="safety-priority-slider"
            />
          </div>
        </div>
        
        {/* Action Buttons */}
        <div className="space-y-2 mt-4">
          <Button 
            className="w-full action-btn primary"
            onClick={calculateRoute}
            disabled={isCalculating}
            data-testid="calculate-route-btn"
          >
            {isCalculating ? (
              <>
                <div className="spinner w-4 h-4"></div>
                Calculating...
              </>
            ) : (
              <>
                <Compass size={16} />
                Calculate Route
              </>
            )}
          </Button>
          
          <div className="flex gap-2">
            <Button 
              className="flex-1 action-btn secondary"
              onClick={simulateWeather}
              data-testid="simulate-weather-btn"
            >
              <CloudLightning size={14} />
              Weather
            </Button>
            <Button 
              className="flex-1 action-btn secondary"
              onClick={resetWeather}
              data-testid="reset-weather-btn"
            >
              <RefreshCw size={14} />
              Reset
            </Button>
          </div>
        </div>
        
        {/* Legend */}
        <div className="space-y-2 mt-4 pt-4 border-t border-slate-700/50">
          <div className="section-header">Legend</div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="legend-item">
              <div className="legend-color route"></div>
              <span>Route</span>
            </div>
            <div className="legend-item">
              <div className="legend-color danger"></div>
              <span>Danger Zone</span>
            </div>
            <div className="legend-item">
              <div className="legend-color warning"></div>
              <span>High Waves</span>
            </div>
            <div className="legend-item">
              <div className="legend-color safe"></div>
              <span>Port</span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Map Container */}
      <div className="map-container" data-testid="map-container">
        <MapContainer 
          center={mapCenter} 
          zoom={mapZoom} 
          style={{ height: '100%', width: '100%' }}
          zoomControl={true}
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          />
          
          {/* Danger Zones */}
          {dangerZones.map(zone => (
            <Polygon
              key={zone.id}
              positions={zone.coordinates.map(c => [c.lat, c.lon])}
              pathOptions={{
                color: zone.color,
                fillColor: zone.color,
                fillOpacity: zone.opacity,
                weight: 2,
                dashArray: zone.is_restricted ? '5, 5' : undefined
              }}
              data-testid={`danger-zone-${zone.id}`}
            >
              <Tooltip>
                <div className="flex items-center gap-2">
                  {getDangerIcon(zone.type)}
                  <span className="font-medium">{zone.name}</span>
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  Severity: {Math.round(zone.severity * 100)}%
                  {zone.is_restricted && <Badge variant="destructive" className="ml-2">RESTRICTED</Badge>}
                </div>
              </Tooltip>
            </Polygon>
          ))}
          
          {/* Route Polyline */}
          {route && route.length > 0 && (
            <Polyline
              positions={route.map(p => [p.lat, p.lon])}
              pathOptions={{
                color: '#38BDF8',
                weight: 4,
                opacity: 0.9,
                lineCap: 'round',
                lineJoin: 'round'
              }}
              className="route-glow"
              data-testid="route-polyline"
            />
          )}
          
          {/* Port Markers */}
          {ports.map(port => {
            const isSource = port.id === sourcePort;
            const isDest = port.id === destPort;
            
            if (!isSource && !isDest) return null;
            
            return (
              <Marker 
                key={port.id} 
                position={[port.lat, port.lon]}
                icon={createPortIcon(isSource)}
              >
                <Popup>
                  <div className="flex items-center gap-2">
                    <Anchor size={16} className={isSource ? 'text-emerald-400' : 'text-red-400'} />
                    <span className="font-medium">{port.name}</span>
                  </div>
                  <div className="text-xs text-slate-400 mt-1 font-mono">
                    {port.lat.toFixed(4)}°N, {port.lon.toFixed(4)}°E
                  </div>
                </Popup>
              </Marker>
            );
          })}
          
          {/* Animated Vessel */}
          <AnimatedVessel route={route} isAnimating={isAnimating} />
          
          {/* Fit bounds to route */}
          {route && <MapBoundsFitter route={route} />}
        </MapContainer>
        
        {/* Stats Overlay */}
        {routeStats && (
          <div className="stats-overlay glass-panel rounded-lg p-4" data-testid="stats-overlay">
            <div className="flex items-center justify-between mb-3">
              <div className="section-header mb-0">Route Statistics</div>
              <Badge variant="outline" className="text-sky-400 border-sky-400/50">
                {routeStats.waypoints} pts
              </Badge>
            </div>
            
            <div className="grid grid-cols-2 gap-3">
              <div className="stat-card">
                <div className="stat-label">Distance</div>
                <div className="stat-value">
                  {routeStats.distance.toFixed(0)}
                  <span className="stat-unit">km</span>
                </div>
              </div>
              
              <div className="stat-card">
                <div className="stat-label">Est. Time</div>
                <div className="stat-value">
                  {routeStats.time.toFixed(1)}
                  <span className="stat-unit">hrs</span>
                </div>
              </div>
              
              <div className="stat-card">
                <div className="stat-label">Fuel Usage</div>
                <div className="stat-value">
                  {routeStats.fuel.toFixed(0)}
                  <span className="stat-unit">L</span>
                </div>
              </div>
              
              <div className="stat-card">
                <div className="stat-label">Avg Risk</div>
                <div className="risk-indicator">
                  <div className="risk-bar">
                    <div 
                      className={`risk-fill ${getRiskLevel(routeStats.risk).level}`}
                      style={{ width: `${routeStats.risk * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-xs font-mono" style={{ color: getRiskLevel(routeStats.risk).color }}>
                    {getRiskLevel(routeStats.risk).label}
                  </span>
                </div>
              </div>
            </div>
            
            <Button 
              variant="ghost" 
              size="sm"
              className="w-full mt-3 text-slate-400 hover:text-slate-100"
              onClick={() => setIsAnimating(!isAnimating)}
              data-testid="toggle-animation-btn"
            >
              <Ship size={14} className="mr-2" />
              {isAnimating ? 'Stop' : 'Start'} Animation
            </Button>
          </div>
        )}
        
        {/* Weather Alert */}
        {weatherAlert && (
          <div className="alert-overlay" data-testid="weather-alert">
            <div className="weather-alert">
              <AlertTriangle className="text-amber-400 flex-shrink-0" size={20} />
              <div>
                <div className="font-medium text-slate-100">{weatherAlert.message}</div>
                <div className="text-xs text-slate-400 mt-1">
                  Route will be recalculated automatically
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
