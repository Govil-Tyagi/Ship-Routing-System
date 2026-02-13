#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Marine Routing System
Tests all endpoints including A* route calculation, weather simulation, and data retrieval.
"""
import requests
import sys
import json
from datetime import datetime
import time

class MarineRoutingAPITester:
    def __init__(self, base_url="https://safe-sea-navigator.preview.emergentagent.com"):
        self.base_url = base_url
        self.api = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.results = []
        
        # Test data
        self.barcelona_coords = {"lat": 41.3851, "lon": 2.1734}
        self.alexandria_coords = {"lat": 31.2001, "lon": 29.9187}
        
    def log_test(self, name, success, details="", response_data=None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            
        result = {
            "name": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        if response_data and success:
            # Store sample response for verification
            if isinstance(response_data, dict):
                result["sample_response"] = {k: str(v)[:100] if isinstance(v, (list, dict)) else v 
                                           for k, v in list(response_data.items())[:5]}
        
        self.results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")
        if details:
            print(f"   Details: {details}")
    
    def test_health_check(self):
        """Test basic API connectivity"""
        try:
            response = requests.get(f"{self.api}/", timeout=10)
            success = response.status_code == 200
            data = response.json() if success else {}
            
            details = f"Status: {response.status_code}"
            if success and "status" in data:
                details += f", Message: {data.get('message', 'N/A')}"
                
            self.log_test("Health Check", success, details, data)
            return success
            
        except Exception as e:
            self.log_test("Health Check", False, f"Connection error: {str(e)}")
            return False
    
    def test_get_ports(self):
        """Test ports endpoint - should return Mediterranean ports"""
        try:
            response = requests.get(f"{self.api}/ports", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                # Verify response structure
                if not isinstance(data, list):
                    success = False
                    details = f"Expected list, got {type(data)}"
                elif len(data) == 0:
                    success = False 
                    details = "No ports returned"
                else:
                    # Check for expected ports
                    port_names = [p.get('name', '') for p in data]
                    expected_ports = ['Barcelona', 'Alexandria', 'Marseille']
                    found_ports = [p for p in expected_ports if p in port_names]
                    
                    details = f"Found {len(data)} ports: {', '.join(port_names[:5])}"
                    if len(found_ports) >= 2:
                        details += f" (includes {', '.join(found_ports)})"
                    else:
                        success = False
                        details += " - Missing expected Mediterranean ports"
            else:
                details = f"HTTP {response.status_code}"
                data = None
                
            self.log_test("GET /api/ports", success, details, data)
            return success, data if success else []
            
        except Exception as e:
            self.log_test("GET /api/ports", False, f"Error: {str(e)}")
            return False, []
    
    def test_get_vessels(self):
        """Test vessels endpoint - should return 4 vessel types"""
        try:
            response = requests.get(f"{self.api}/vessels", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                if not isinstance(data, list):
                    success = False
                    details = f"Expected list, got {type(data)}"
                elif len(data) != 4:
                    success = False
                    details = f"Expected 4 vessels, got {len(data)}"
                else:
                    vessel_types = [v.get('type', '') for v in data]
                    expected = ['cargo_ship', 'oil_tanker', 'fishing_boat', 'high_speed_boat']
                    missing = [t for t in expected if t not in vessel_types]
                    
                    if missing:
                        success = False
                        details = f"Missing vessel types: {missing}"
                    else:
                        details = f"All 4 vessels found: {', '.join(vessel_types)}"
                        
                        # Check vessel properties
                        sample = data[0]
                        required_fields = ['type', 'name', 'fuel_consumption_rate', 'max_speed']
                        missing_fields = [f for f in required_fields if f not in sample]
                        if missing_fields:
                            success = False
                            details += f" - Missing fields: {missing_fields}"
            else:
                details = f"HTTP {response.status_code}"
                data = None
                
            self.log_test("GET /api/vessels", success, details, data)
            return success, data if success else []
            
        except Exception as e:
            self.log_test("GET /api/vessels", False, f"Error: {str(e)}")
            return False, []
    
    def test_get_danger_zones(self):
        """Test danger zones endpoint"""
        try:
            response = requests.get(f"{self.api}/danger-zones", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                if not isinstance(data, list):
                    success = False
                    details = f"Expected list, got {type(data)}"
                elif len(data) == 0:
                    success = False
                    details = "No danger zones returned"
                else:
                    # Check for expected danger zone properties
                    sample = data[0]
                    required_fields = ['id', 'type', 'name', 'coordinates', 'severity', 'color']
                    missing_fields = [f for f in required_fields if f not in sample]
                    
                    if missing_fields:
                        success = False
                        details = f"Missing fields: {missing_fields}"
                    else:
                        zone_types = list(set([z.get('type', '') for z in data]))
                        details = f"{len(data)} zones with types: {', '.join(zone_types)}"
                        
                        # Verify colors are present
                        colors = [z.get('color', '') for z in data]
                        if not all(colors):
                            success = False
                            details += " - Missing colors"
            else:
                details = f"HTTP {response.status_code}"
                data = None
                
            self.log_test("GET /api/danger-zones", success, details, data)
            return success, data if success else []
            
        except Exception as e:
            self.log_test("GET /api/danger-zones", False, f"Error: {str(e)}")
            return False, []
    
    def test_calculate_route(self, vessel_type="cargo_ship"):
        """Test route calculation - CRITICAL: Must NOT be straight line"""
        try:
            payload = {
                "source_lat": self.barcelona_coords["lat"],
                "source_lon": self.barcelona_coords["lon"], 
                "dest_lat": self.alexandria_coords["lat"],
                "dest_lon": self.alexandria_coords["lon"],
                "vessel_type": vessel_type,
                "fuel_priority": 0.33,
                "time_priority": 0.33,
                "safety_priority": 0.34
            }
            
            response = requests.post(f"{self.api}/calculate-route", json=payload, timeout=30)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                
                # Verify response structure
                required_fields = ['success', 'path', 'total_distance', 'total_time', 'waypoints']
                missing_fields = [f for f in required_fields if f not in data]
                
                if missing_fields:
                    success = False
                    details = f"Missing fields: {missing_fields}"
                elif not data.get('success', False):
                    success = False
                    details = f"Route calculation failed: {data.get('message', 'Unknown error')}"
                elif not isinstance(data.get('path', []), list) or len(data['path']) < 2:
                    success = False
                    details = f"Invalid path: {len(data.get('path', []))} waypoints"
                else:
                    path = data['path']
                    waypoints = data.get('waypoints', len(path))
                    
                    # CRITICAL CHECK: Route should NOT be a straight line
                    # A proper A* route should have multiple waypoints (>10 for Barcelona-Alexandria)
                    if waypoints < 10:
                        success = False
                        details = f"Route too simple: {waypoints} waypoints (expected >10 for A* pathfinding)"
                    else:
                        # Verify path contains proper waypoint data
                        first_point = path[0]
                        last_point = path[-1]
                        
                        required_point_fields = ['lat', 'lon', 'cumulative_distance', 'cumulative_fuel']
                        missing_point_fields = [f for f in required_point_fields if f not in first_point]
                        
                        if missing_point_fields:
                            success = False
                            details = f"Path points missing fields: {missing_point_fields}"
                        else:
                            details = (f"Route calculated: {waypoints} waypoints, "
                                     f"{data['total_distance']:.0f}km, "
                                     f"{data['total_time']:.1f}h, "
                                     f"{data['total_fuel']:.0f}L fuel")
                            
                            # Additional verification: check path actually traverses multiple grid points
                            lat_range = max([p['lat'] for p in path]) - min([p['lat'] for p in path])
                            lon_range = max([p['lon'] for p in path]) - min([p['lon'] for p in path])
                            
                            if lat_range < 1.0 or lon_range < 1.0:
                                success = False
                                details += " - WARNING: Route may be too direct (insufficient grid traversal)"
            else:
                details = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    if 'detail' in error_data:
                        details += f" - {error_data['detail']}"
                except:
                    pass
                data = None
                
            self.log_test("POST /api/calculate-route", success, details, data)
            return success, data if success else None
            
        except Exception as e:
            self.log_test("POST /api/calculate-route", False, f"Error: {str(e)}")
            return False, None
    
    def test_simulate_weather(self):
        """Test weather simulation"""
        try:
            response = requests.post(f"{self.api}/simulate-weather", timeout=15)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                required_fields = ['message', 'timestamp', 'danger_zones']
                missing_fields = [f for f in required_fields if f not in data]
                
                if missing_fields:
                    success = False
                    details = f"Missing fields: {missing_fields}"
                elif not isinstance(data.get('danger_zones', []), list):
                    success = False
                    details = "Danger zones not returned as list"
                else:
                    zones = data['danger_zones']
                    details = f"Weather simulated: {data['message']}, {len(zones)} danger zones"
            else:
                details = f"HTTP {response.status_code}"
                data = None
                
            self.log_test("POST /api/simulate-weather", success, details, data)
            return success, data if success else None
            
        except Exception as e:
            self.log_test("POST /api/simulate-weather", False, f"Error: {str(e)}")
            return False, None
    
    def test_reset_weather(self):
        """Test weather reset"""
        try:
            response = requests.post(f"{self.api}/reset-weather", timeout=15)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                required_fields = ['message', 'danger_zones']
                missing_fields = [f for f in required_fields if f not in data]
                
                if missing_fields:
                    success = False
                    details = f"Missing fields: {missing_fields}"
                else:
                    zones = data['danger_zones']
                    details = f"Weather reset: {len(zones)} default danger zones"
            else:
                details = f"HTTP {response.status_code}"
                data = None
                
            self.log_test("POST /api/reset-weather", success, details, data)
            return success
            
        except Exception as e:
            self.log_test("POST /api/reset-weather", False, f"Error: {str(e)}")
            return False
    
    def test_route_with_different_vessels(self):
        """Test route calculation with different vessel types"""
        vessels = ['cargo_ship', 'oil_tanker', 'fishing_boat', 'high_speed_boat']
        all_passed = True
        
        for vessel in vessels:
            success, route_data = self.test_calculate_route(vessel)
            if not success:
                all_passed = False
            else:
                # Brief wait to avoid overwhelming the server
                time.sleep(0.5)
        
        return all_passed
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("=" * 60)
        print("🚢 MARINE ROUTING SYSTEM - BACKEND API TESTS")
        print("=" * 60)
        print(f"Testing API: {self.api}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Basic connectivity
        if not self.test_health_check():
            print("\n❌ CRITICAL: Cannot connect to API server!")
            return False
        
        print()
        
        # Data endpoints
        print("📋 Testing Data Endpoints...")
        ports_success, ports_data = self.test_get_ports()
        vessels_success, vessels_data = self.test_get_vessels()
        zones_success, zones_data = self.test_get_danger_zones()
        
        print()
        
        # Core functionality
        print("🎯 Testing Core Routing Functionality...")
        route_success, route_data = self.test_calculate_route()
        
        print()
        
        # Weather simulation
        print("🌩️ Testing Weather Simulation...")
        weather_sim_success = self.test_simulate_weather()
        weather_reset_success = self.test_reset_weather()
        
        print()
        
        # Multi-vessel testing
        print("🚢 Testing Multiple Vessel Types...")
        multi_vessel_success = self.test_route_with_different_vessels()
        
        # Results summary
        print()
        print("=" * 60)
        print(f"📊 TEST RESULTS: {self.tests_passed}/{self.tests_run} PASSED")
        print("=" * 60)
        
        # Categorize results
        critical_tests = ['Health Check', 'POST /api/calculate-route']
        critical_failures = [r for r in self.results if not r['success'] and r['name'] in critical_tests]
        
        if critical_failures:
            print("❌ CRITICAL FAILURES:")
            for failure in critical_failures:
                print(f"   - {failure['name']}: {failure['details']}")
        
        other_failures = [r for r in self.results if not r['success'] and r['name'] not in critical_tests]
        if other_failures:
            print(f"\n⚠️ OTHER ISSUES ({len(other_failures)}):")
            for failure in other_failures:
                print(f"   - {failure['name']}: {failure['details']}")
        
        # Success highlights
        successes = [r for r in self.results if r['success']]
        if successes:
            print(f"\n✅ WORKING FEATURES ({len(successes)}):")
            for success in successes:
                print(f"   - {success['name']}")
        
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"\n🎯 Overall Success Rate: {success_rate:.1f}%")
        
        # Return overall status
        return len(critical_failures) == 0
    
    def get_test_summary(self):
        """Get test summary for reporting"""
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "success_rate": (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0,
            "critical_failures": [r for r in self.results if not r['success'] and r['name'] in ['Health Check', 'POST /api/calculate-route']],
            "all_results": self.results
        }

def main():
    """Main test execution"""
    tester = MarineRoutingAPITester()
    
    try:
        success = tester.run_all_tests()
        summary = tester.get_test_summary()
        
        # Save detailed results
        with open('/app/backend_test_results.json', 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: /app/backend_test_results.json")
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())