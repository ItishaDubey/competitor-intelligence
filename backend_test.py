import requests
import sys
import json
from datetime import datetime

class CompetitiveIntelAPITester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.competitor_id = None
        self.report_id = None
        self.tests_run = 0
        self.tests_passed = 0
        
    def log(self, message):
        """Log test messages"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, expected_content=None):
        """Run a single API test"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ PASSED - Status: {response.status_code}")
                
                # Check expected content if provided
                if expected_content:
                    response_data = response.json() if response.text else {}
                    for key, value in expected_content.items():
                        if key in response_data and response_data[key] == value:
                            self.log(f"   ✓ Content check passed: {key} = {value}")
                        else:
                            self.log(f"   ⚠️  Content check failed: {key} expected {value}, got {response_data.get(key)}")
                
                return True, response.json() if response.text else {}
            else:
                self.log(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                if response.text:
                    self.log(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            self.log(f"❌ FAILED - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test health endpoint"""
        success, _ = self.run_test("Health Check", "GET", "/api/health", 200)
        return success

    def test_user_registration(self, name="Test User", email="test@example.com", password="testpassword123"):
        """Test user registration"""
        success, response = self.run_test(
            "User Registration",
            "POST",
            "/api/auth/register",
            200,
            data={"name": name, "email": email, "password": password}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            self.log(f"   ✓ Received access token and user ID: {self.user_id}")
            return True
        return False

    def test_user_login(self, email="test@example.com", password="testpassword123"):
        """Test user login"""
        success, response = self.run_test(
            "User Login",
            "POST", 
            "/api/auth/login",
            200,
            data={"email": email, "password": password}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            self.log(f"   ✓ Login successful with user ID: {self.user_id}")
            return True
        return False

    def test_get_current_user(self):
        """Test get current user"""
        if not self.token:
            self.log("❌ No token available for authenticated request")
            return False
            
        success, response = self.run_test("Get Current User", "GET", "/api/auth/me", 200)
        if success and 'id' in response:
            self.log(f"   ✓ User details retrieved: {response['name']} ({response['email']})")
            return True
        return False

    def test_create_competitor(self):
        """Test creating a competitor"""
        if not self.token:
            self.log("❌ No token available for authenticated request")
            return False
            
        competitor_data = {
            "name": "Test Competitor",
            "website": "https://example.com",
            "is_baseline": False,
            "pages_to_monitor": [
                {
                    "name": "Homepage",
                    "url": "https://example.com",
                    "track": ["content", "products", "pricing"]
                }
            ]
        }
        
        success, response = self.run_test(
            "Create Competitor",
            "POST",
            "/api/competitors",
            200,
            data=competitor_data
        )
        if success and 'id' in response:
            self.competitor_id = response['id']
            self.log(f"   ✓ Competitor created with ID: {self.competitor_id}")
            return True
        return False

    def test_get_competitors(self):
        """Test getting competitors list"""
        if not self.token:
            self.log("❌ No token available for authenticated request")
            return False
            
        success, response = self.run_test("Get Competitors List", "GET", "/api/competitors", 200)
        if success:
            self.log(f"   ✓ Retrieved {len(response)} competitors")
            return True
        return False

    def test_get_competitor_by_id(self):
        """Test getting a specific competitor"""
        if not self.token or not self.competitor_id:
            self.log("❌ No token or competitor ID available")
            return False
            
        success, response = self.run_test(
            "Get Competitor by ID",
            "GET",
            f"/api/competitors/{self.competitor_id}",
            200
        )
        if success and response.get('id') == self.competitor_id:
            self.log(f"   ✓ Retrieved competitor: {response['name']}")
            return True
        return False

    def test_update_competitor(self):
        """Test updating a competitor"""
        if not self.token or not self.competitor_id:
            self.log("❌ No token or competitor ID available")
            return False
            
        update_data = {
            "name": "Updated Test Competitor",
            "is_baseline": True
        }
        
        success, response = self.run_test(
            "Update Competitor",
            "PUT",
            f"/api/competitors/{self.competitor_id}",
            200,
            data=update_data
        )
        if success and response.get('name') == 'Updated Test Competitor':
            self.log(f"   ✓ Competitor updated successfully")
            return True
        return False

    def test_run_intelligence_scan(self):
        """Test running intelligence scan"""
        if not self.token:
            self.log("❌ No token available for authenticated request")
            return False
            
        success, response = self.run_test(
            "Run Intelligence Scan",
            "POST",
            "/api/reports/run",
            200
        )
        if success and response.get('status') == 'started':
            self.log(f"   ✓ Intelligence scan started: {response.get('message')}")
            return True
        return False

    def test_get_reports(self):
        """Test getting reports list"""
        if not self.token:
            self.log("❌ No token available for authenticated request")
            return False
            
        success, response = self.run_test("Get Reports List", "GET", "/api/reports", 200)
        if success:
            self.log(f"   ✓ Retrieved {len(response)} reports")
            if response and len(response) > 0:
                self.report_id = response[0]['id']
                self.log(f"   ✓ First report ID: {self.report_id}")
            return True
        return False

    def test_get_report_by_id(self):
        """Test getting a specific report"""
        if not self.token or not self.report_id:
            self.log("❌ No token or report ID available")
            return False
            
        success, response = self.run_test(
            "Get Report by ID",
            "GET",
            f"/api/reports/{self.report_id}",
            200
        )
        if success and response.get('id') == self.report_id:
            self.log(f"   ✓ Retrieved report with summary: {response.get('summary')}")
            return True
        return False

    def test_get_latest_summary(self):
        """Test getting latest report summary"""
        if not self.token:
            self.log("❌ No token available for authenticated request")
            return False
            
        success, response = self.run_test("Get Latest Summary", "GET", "/api/reports/latest/summary", 200)
        if success:
            has_report = response.get('has_report', False)
            self.log(f"   ✓ Latest summary retrieved - Has report: {has_report}")
            return True
        return False

    def test_get_dashboard_stats(self):
        """Test getting dashboard stats"""
        if not self.token:
            self.log("❌ No token available for authenticated request")
            return False
            
        success, response = self.run_test("Get Dashboard Stats", "GET", "/api/dashboard/stats", 200)
        if success:
            stats = {
                'competitors_tracked': response.get('competitors_tracked', 0),
                'total_reports': response.get('total_reports', 0),
                'active_monitors': response.get('active_monitors', 0)
            }
            self.log(f"   ✓ Dashboard stats: {stats}")
            return True
        return False

    def test_delete_competitor(self):
        """Test deleting a competitor"""
        if not self.token or not self.competitor_id:
            self.log("❌ No token or competitor ID available")
            return False
            
        success, response = self.run_test(
            "Delete Competitor",
            "DELETE",
            f"/api/competitors/{self.competitor_id}",
            200
        )
        if success and response.get('status') == 'deleted':
            self.log(f"   ✓ Competitor deleted successfully")
            return True
        return False

def main():
    tester = CompetitiveIntelAPITester()
    
    print("=" * 60)
    print("🚀 COMPETITIVE INTELLIGENCE API TESTING")
    print("=" * 60)
    
    # Test sequence
    tests = [
        ("Health Check", tester.test_health_check),
        ("User Registration", tester.test_user_registration),
        ("Get Current User", tester.test_get_current_user),
        ("Create Competitor", tester.test_create_competitor),
        ("Get Competitors", tester.test_get_competitors),
        ("Get Competitor by ID", tester.test_get_competitor_by_id),
        ("Update Competitor", tester.test_update_competitor),
        ("Get Dashboard Stats", tester.test_get_dashboard_stats),
        ("Run Intelligence Scan", tester.test_run_intelligence_scan),
        ("Get Reports", tester.test_get_reports),
        ("Get Latest Summary", tester.test_get_latest_summary),
        ("Delete Competitor", tester.test_delete_competitor),
    ]
    
    for test_name, test_func in tests:
        print()
        try:
            test_func()
        except Exception as e:
            tester.log(f"❌ {test_name} crashed: {str(e)}")
        print("-" * 40)
    
    # Final results
    print()
    print("=" * 60)
    print(f"📊 FINAL RESULTS")
    print(f"Tests run: {tester.tests_run}")
    print(f"Tests passed: {tester.tests_passed}")
    print(f"Tests failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%")
    print("=" * 60)
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())