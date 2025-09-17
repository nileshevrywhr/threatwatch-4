import requests
import sys
import json
from datetime import datetime

class OSINTAPITester:
    def __init__(self, base_url="https://threatwatch-4.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else self.api_url
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2)}")
        if params:
            print(f"   Params: {params}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)

            print(f"   Response Status: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2, default=str)}")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error Response: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"   Raw Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_api_root(self):
        """Test API root endpoint"""
        return self.run_test(
            "API Root",
            "GET",
            "",
            200
        )

    def test_subscribe_valid_data(self):
        """Test subscription with valid data"""
        test_data = {
            "term": "ATM fraud",
            "email": f"test_{datetime.now().strftime('%H%M%S')}@example.com",
            "phone": "+1234567890"
        }
        
        success, response = self.run_test(
            "Subscribe with Valid Data",
            "POST",
            "subscribe",
            200,
            data=test_data
        )
        
        if success:
            # Store email for later tests
            self.test_email = test_data["email"]
            return True, response
        return False, {}

    def test_subscribe_missing_required_fields(self):
        """Test subscription with missing required fields"""
        # Test missing term
        success1, _ = self.run_test(
            "Subscribe Missing Term",
            "POST",
            "subscribe",
            422,  # Validation error
            data={"email": "test@example.com"}
        )
        
        # Test missing email
        success2, _ = self.run_test(
            "Subscribe Missing Email",
            "POST",
            "subscribe",
            422,  # Validation error
            data={"term": "test term"}
        )
        
        return success1 and success2

    def test_subscribe_duplicate(self):
        """Test duplicate subscription"""
        if not hasattr(self, 'test_email'):
            print("⚠️  Skipping duplicate test - no test email available")
            return False
            
        # Try to subscribe with same term and email again
        duplicate_data = {
            "term": "ATM fraud",
            "email": self.test_email,
            "phone": "+1234567890"
        }
        
        return self.run_test(
            "Subscribe Duplicate",
            "POST",
            "subscribe",
            400,  # Should return error for duplicate
            data=duplicate_data
        )[0]

    def test_status_valid_email(self):
        """Test status endpoint with valid email"""
        if not hasattr(self, 'test_email'):
            print("⚠️  Skipping status test - no test email available")
            return False
            
        success, response = self.run_test(
            "Get Status with Valid Email",
            "GET",
            "status",
            200,
            params={"email": self.test_email}
        )
        
        if success:
            # Verify response structure
            if 'subscriptions' in response and 'intelligence_matches' in response:
                print("✅ Response has correct structure")
                
                # Check if we have subscriptions
                if len(response['subscriptions']) > 0:
                    print(f"✅ Found {len(response['subscriptions'])} subscription(s)")
                    
                # Check if we have intelligence matches for ATM fraud
                if len(response['intelligence_matches']) > 0:
                    print(f"✅ Found {len(response['intelligence_matches'])} intelligence match(es)")
                    for match in response['intelligence_matches']:
                        print(f"   - {match['incident_title']} (Severity: {match['severity']})")
                else:
                    print("⚠️  No intelligence matches found")
                    
                return True
            else:
                print("❌ Response missing required fields")
                return False
        return False

    def test_status_nonexistent_email(self):
        """Test status endpoint with non-existent email"""
        return self.run_test(
            "Get Status with Non-existent Email",
            "GET",
            "status",
            200,  # Should still return 200 but with empty data
            params={"email": "nonexistent@example.com"}
        )[0]

    def test_status_missing_email_param(self):
        """Test status endpoint without email parameter"""
        return self.run_test(
            "Get Status Missing Email Parameter",
            "GET",
            "status",
            422,  # Validation error
            params={}
        )[0]

    def test_quick_scan_ransomware(self):
        """Test Quick Scan with ransomware query"""
        test_data = {"query": "ransomware"}
        
        success, response = self.run_test(
            "Quick Scan - Ransomware",
            "POST",
            "quick-scan",
            200,
            data=test_data
        )
        
        if success:
            # Verify response structure
            required_fields = ['query', 'summary', 'key_threats', 'sources', 'timestamp']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                print(f"❌ Response missing required fields: {missing_fields}")
                return False
            
            print("✅ Response has correct structure")
            print(f"✅ Query: {response['query']}")
            print(f"✅ Key threats count: {len(response['key_threats'])}")
            print(f"✅ Sources count: {len(response['sources'])}")
            
            # Check if summary contains meaningful content
            if len(response['summary']) > 50:
                print("✅ Summary has meaningful content")
            else:
                print("⚠️  Summary seems too short")
                
            return True
        return False

    def test_quick_scan_malware(self):
        """Test Quick Scan with malware query"""
        test_data = {"query": "malware"}
        
        success, response = self.run_test(
            "Quick Scan - Malware",
            "POST",
            "quick-scan",
            200,
            data=test_data
        )
        
        if success:
            # Verify key threats are extracted
            if response.get('key_threats') and len(response['key_threats']) > 0:
                print(f"✅ Found {len(response['key_threats'])} key threats:")
                for i, threat in enumerate(response['key_threats'][:3], 1):
                    print(f"   {i}. {threat}")
                return True
            else:
                print("⚠️  No key threats found")
                return False
        return False

    def test_quick_scan_phishing(self):
        """Test Quick Scan with phishing query"""
        test_data = {"query": "phishing"}
        
        return self.run_test(
            "Quick Scan - Phishing",
            "POST",
            "quick-scan",
            200,
            data=test_data
        )[0]

    def test_quick_scan_zero_day(self):
        """Test Quick Scan with zero-day query"""
        test_data = {"query": "zero-day"}
        
        return self.run_test(
            "Quick Scan - Zero-day",
            "POST",
            "quick-scan",
            200,
            data=test_data
        )[0]

    def test_quick_scan_empty_query(self):
        """Test Quick Scan with empty query"""
        test_data = {"query": ""}
        
        # This should either return 422 for validation error or 200 with empty results
        success, response = self.run_test(
            "Quick Scan - Empty Query",
            "POST",
            "quick-scan",
            200,  # Assuming it handles empty queries gracefully
            data=test_data
        )
        
        return success

    def test_quick_scan_missing_query(self):
        """Test Quick Scan with missing query field"""
        test_data = {}
        
        return self.run_test(
            "Quick Scan - Missing Query Field",
            "POST",
            "quick-scan",
            422,  # Validation error
            data=test_data
        )[0]

def main():
    print("🚀 Starting OSINT Threat Monitoring API Tests")
    print("=" * 60)
    
    tester = OSINTAPITester()
    
    # Test sequence
    tests = [
        ("API Root Endpoint", tester.test_api_root),
        ("Subscribe with Valid Data", tester.test_subscribe_valid_data),
        ("Subscribe with Missing Fields", tester.test_subscribe_missing_required_fields),
        ("Subscribe Duplicate", tester.test_subscribe_duplicate),
        ("Status with Valid Email", tester.test_status_valid_email),
        ("Status with Non-existent Email", tester.test_status_nonexistent_email),
        ("Status Missing Email Parameter", tester.test_status_missing_email_param),
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print('='*60)
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
    
    # Print final results
    print(f"\n{'='*60}")
    print("📊 FINAL TEST RESULTS")
    print('='*60)
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())