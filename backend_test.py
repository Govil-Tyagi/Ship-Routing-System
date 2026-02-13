import requests
import sys
import json
from datetime import datetime

class MarineRoutingAPITester:
    def __init__(self, base_url="https://safe-sea-navigator.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.successful_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.successful_tests.append(name)
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and len(response_data) > 0:
                        print(f"   Response preview: {json.dumps(list(response_data.keys())[:3])}...")
                    elif isinstance(response_data, list) and len(response_data) > 0:
                        print(f"   Response: {len(response_data)} items")
                except:
                    pass
            else:
                self.failed_tests.append({
                    "test_name": name,
                    "expected": expected_status,
                    "actual": response.status_code,
                    "error": response.text[:200] if response.text else "No response body"
                })
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Error: {response.text[:200]}...")

            return success, response.json() if response.headers.get('content-type', '').startswith('application/json') else {}

        except requests.exceptions.RequestException as e:
            self.failed_tests.append({
                "test_name": name,
                "expected": expected_status,
                "actual": "Request Error",
                "error": str(e)
            })
            print(f"❌ Failed - Request Error: {str(e)}")
            return False, {}
        except Exception as e:
            self.failed_tests.append({
                "test_name": name,
                "expected": expected_status,
                "actual": "Unknown Error",
                "error": str(e)
            })
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test health check endpoint"""
        success, response = self.run_test("Health Check", "GET", "", 200)
        return success

    def test_get_ports(self):
        """Test getting all ports (public endpoint)"""
        success, response = self.run_test("Get Ports", "GET", "ports", 200)
        if success:
            # Check for Indian ports
            port_names = [port.get('name', '').lower() for port in response]
            indian_ports = ['mumbai', 'chennai', 'kolkata', 'cochin', 'visakhapatnam', 'kandla', 'mangalore', 'tuticorin']
            
            found_indian_ports = [port for port in indian_ports if any(port in name for name in port_names)]
            print(f"   Found Indian ports: {found_indian_ports}")
            
            if len(found_indian_ports) >= 5:  # Expecting at least 5 Indian ports
                print(f"✅ Indian ports successfully added to system")
                return True
            else:
                print(f"⚠️  Only {len(found_indian_ports)} Indian ports found, expected at least 5")
                
        return success

    def test_get_vessels(self):
        """Test getting all vessel types (public endpoint)"""
        success, response = self.run_test("Get Vessels", "GET", "vessels", 200)
        if success and len(response) >= 4:
            vessel_types = [v.get('type') for v in response]
            print(f"   Available vessels: {vessel_types}")
        return success

    def test_get_danger_zones(self):
        """Test getting danger zones (public endpoint)"""
        success, response = self.run_test("Get Danger Zones", "GET", "danger-zones", 200)
        return success

    def test_signup(self, email, username, password, full_name=None):
        """Test user signup"""
        user_data = {
            "email": email,
            "username": username,
            "password": password,
            "full_name": full_name
        }
        
        success, response = self.run_test("User Signup", "POST", "auth/signup", 201, user_data)
        if success:
            print(f"   Created user: {response.get('username')} ({response.get('email')})")
        return success, response

    def test_login(self, email, password):
        """Test user login and get token"""
        login_data = {
            "email": email,
            "password": password
        }
        
        success, response = self.run_test("User Login", "POST", "auth/login", 200, login_data)
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            user_info = response.get('user', {})
            print(f"   Logged in as: {user_info.get('username')} ({user_info.get('email')})")
            print(f"   Token acquired: {self.token[:20]}...")
            return True
        return False

    def test_protected_route_without_token(self):
        """Test protected route returns 401 without token"""
        # Temporarily remove token
        old_token = self.token
        self.token = None
        
        route_data = {
            "source_lat": 18.9388,
            "source_lon": 72.8354,
            "dest_lat": 13.0827,
            "dest_lon": 80.2707,
            "vessel_type": "cargo_ship"
        }
        
        success, response = self.run_test("Protected Route Without Token", "POST", "calculate-route", 401, route_data)
        
        # Restore token
        self.token = old_token
        return success

    def test_calculate_route_mumbai_to_chennai(self):
        """Test route calculation from Mumbai to Chennai (protected)"""
        route_data = {
            "source_lat": 18.9388,  # Mumbai
            "source_lon": 72.8354,
            "dest_lat": 13.0827,    # Chennai
            "dest_lon": 80.2707,
            "vessel_type": "cargo_ship",
            "fuel_priority": 0.33,
            "time_priority": 0.33,
            "safety_priority": 0.34
        }
        
        success, response = self.run_test("Calculate Route Mumbai to Chennai", "POST", "calculate-route", 200, route_data)
        
        if success:
            print(f"   Route success: {response.get('success')}")
            print(f"   Total distance: {response.get('total_distance', 0):.1f} km")
            print(f"   Total time: {response.get('total_time', 0):.1f} hours")
            print(f"   Waypoints: {response.get('waypoints', 0)}")
            
            # Validate route response structure
            if response.get('success') and response.get('path') and len(response.get('path', [])) > 0:
                print(f"✅ Route calculation successful with valid path")
                return True
            else:
                print(f"⚠️  Route calculation returned success=False or empty path")
        
        return success

    def test_get_current_user(self):
        """Test getting current user profile (protected)"""
        success, response = self.run_test("Get Current User", "GET", "auth/me", 200)
        if success:
            print(f"   User profile: {response.get('username')} ({response.get('email')})")
        return success

    def test_route_history(self):
        """Test getting route history (protected)"""
        success, response = self.run_test("Get Route History", "GET", "route-history", 200)
        if success:
            routes_count = len(response.get('routes', []))
            print(f"   Found {routes_count} routes in history")
        return success

    def test_weather_simulation(self):
        """Test weather simulation (protected)"""
        success, response = self.run_test("Simulate Weather", "POST", "simulate-weather", 200)
        if success:
            print(f"   Weather update: {response.get('message', '')}")
            zones_count = len(response.get('danger_zones', []))
            print(f"   Updated danger zones: {zones_count}")
        return success

    def test_weather_reset(self):
        """Test weather reset (protected)"""
        success, response = self.run_test("Reset Weather", "POST", "reset-weather", 200)
        if success:
            print(f"   Weather reset: {response.get('message', '')}")
        return success

def main():
    print("🚢 Marine Routing System - Backend API Tests")
    print("=" * 50)
    
    tester = MarineRoutingAPITester()
    
    # Test user credentials
    test_email = f"test_user_{datetime.now().strftime('%H%M%S')}@marine.com"
    test_username = f"test_user_{datetime.now().strftime('%H%M%S')}"
    test_password = "test123456"
    
    # Known test user from agent context
    known_test_email = "test@marine.com"
    known_test_password = "test123456"
    
    success_count = 0
    total_tests = 0
    
    print("\n📍 Phase 1: Public Endpoints")
    print("-" * 30)
    
    # Test public endpoints
    if tester.test_health_check():
        success_count += 1
    total_tests += 1
    
    if tester.test_get_ports():
        success_count += 1
    total_tests += 1
    
    if tester.test_get_vessels():
        success_count += 1
    total_tests += 1
    
    if tester.test_get_danger_zones():
        success_count += 1
    total_tests += 1
    
    print("\n🔐 Phase 2: Authentication")
    print("-" * 30)
    
    # Try existing test user first
    print(f"\nTrying to login with known test user: {known_test_email}")
    if tester.test_login(known_test_email, known_test_password):
        success_count += 1
        print("✅ Logged in with existing test user")
    else:
        print("⚠️  Known test user login failed, creating new user...")
        # Create new test user
        signup_success, signup_response = tester.test_signup(test_email, test_username, test_password, "Test User")
        if signup_success:
            success_count += 1
        total_tests += 1
        
        # Login with new user
        if tester.test_login(test_email, test_password):
            success_count += 1
        total_tests += 1
    
    total_tests += 1  # For login test
    
    print("\n🔒 Phase 3: Protected Route Authorization")
    print("-" * 30)
    
    if tester.test_protected_route_without_token():
        success_count += 1
    total_tests += 1
    
    print("\n🧭 Phase 4: Route Calculation")
    print("-" * 30)
    
    if tester.test_calculate_route_mumbai_to_chennai():
        success_count += 1
    total_tests += 1
    
    print("\n👤 Phase 5: User Profile & History")
    print("-" * 30)
    
    if tester.test_get_current_user():
        success_count += 1
    total_tests += 1
    
    if tester.test_route_history():
        success_count += 1
    total_tests += 1
    
    print("\n🌤️  Phase 6: Weather Simulation")
    print("-" * 30)
    
    if tester.test_weather_simulation():
        success_count += 1
    total_tests += 1
    
    if tester.test_weather_reset():
        success_count += 1
    total_tests += 1
    
    # Final results
    print("\n" + "=" * 50)
    print("🏁 TEST SUMMARY")
    print("=" * 50)
    print(f"Tests Run: {total_tests}")
    print(f"Tests Passed: {success_count}")
    print(f"Tests Failed: {total_tests - success_count}")
    print(f"Success Rate: {success_count/total_tests*100:.1f}%")
    
    if tester.failed_tests:
        print(f"\n❌ Failed Tests:")
        for failed in tester.failed_tests:
            print(f"  - {failed['test_name']}: Expected {failed['expected']}, got {failed['actual']}")
            print(f"    Error: {failed['error']}")
    
    if tester.successful_tests:
        print(f"\n✅ Successful Tests:")
        for test in tester.successful_tests:
            print(f"  - {test}")
    
    return 0 if success_count == total_tests else 1

if __name__ == "__main__":
    sys.exit(main())