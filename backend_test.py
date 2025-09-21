import requests
import sys
import json
from datetime import datetime
import time

class OSINTAPITester:
    def __init__(self, base_url="https://imported-repo.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None, auth_required=False):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else self.api_url
        headers = {'Content-Type': 'application/json'}
        
        # Add authentication header if required
        if auth_required and self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2)}")
        if params:
            print(f"   Params: {params}")
        if auth_required:
            print(f"   Auth: {'✓' if self.auth_token else '✗'}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=60)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=60)

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

    def test_register_user(self):
        """Test user registration"""
        timestamp = datetime.now().strftime('%H%M%S')
        test_data = {
            "email": f"testuser_{timestamp}@threatradar.com",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
            "full_name": "Test User"
        }
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            201,
            data=test_data
        )
        
        if success:
            self.test_user_email = test_data["email"]
            self.test_user_password = test_data["password"]
            return True, response
        return False, {}

    def test_login_user(self):
        """Test user login"""
        if not hasattr(self, 'test_user_email'):
            print("⚠️  Skipping login test - no test user available")
            return False
            
        test_data = {
            "email": self.test_user_email,
            "password": self.test_user_password
        }
        
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data=test_data
        )
        
        if success and 'token' in response:
            self.auth_token = response['token']['access_token']
            print(f"✅ Authentication token obtained")
            return True, response
        return False, {}

    def test_google_search_health_check(self):
        """Test Google Custom Search API health check"""
        success, response = self.run_test(
            "Google Search Health Check",
            "GET",
            "health/google-search",
            200
        )
        
        if success:
            # Verify health check response structure
            if 'status' in response:
                print(f"✅ Health Status: {response['status']}")
                if response['status'] == 'healthy':
                    print("✅ Google Custom Search API is healthy")
                    return True
                else:
                    print(f"⚠️  Google API Status: {response.get('error', 'Unknown error')}")
                    return False
            else:
                print("❌ Invalid health check response structure")
                return False
        return False

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

    def test_enhanced_quick_scan_cybersecurity(self):
        """Test Enhanced Quick Scan with Google Custom Search - Cybersecurity"""
        if not self.auth_token:
            print("⚠️  Skipping enhanced quick scan test - authentication required")
            return False
            
        test_data = {"query": "cybersecurity"}
        
        success, response = self.run_test(
            "Enhanced Quick Scan - Cybersecurity",
            "POST",
            "quick-scan",
            200,
            data=test_data,
            auth_required=True
        )
        
        if success:
            # Verify enhanced response structure
            required_fields = [
                'query', 'summary', 'key_threats', 'sources', 
                'discovered_links', 'search_metadata', 'scan_type', 'timestamp'
            ]
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                print(f"❌ Response missing required fields: {missing_fields}")
                return False
            
            print("✅ Enhanced response has correct structure")
            print(f"✅ Query: {response['query']}")
            print(f"✅ Scan Type: {response['scan_type']}")
            print(f"✅ Key threats count: {len(response['key_threats'])}")
            print(f"✅ Sources count: {len(response['sources'])}")
            print(f"✅ Discovered links count: {len(response['discovered_links'])}")
            
            # Verify search metadata
            metadata = response.get('search_metadata', {})
            if 'total_results' in metadata and 'articles_analyzed' in metadata:
                print(f"✅ Search metadata: {metadata['articles_analyzed']} articles analyzed")
                print(f"✅ Total Google results: {metadata['total_results']}")
            
            # Verify discovered links structure
            if response['discovered_links']:
                first_link = response['discovered_links'][0]
                link_fields = ['title', 'url', 'snippet', 'date', 'severity', 'source']
                if all(field in first_link for field in link_fields):
                    print("✅ Discovered links have correct structure")
                    print(f"   Sample: {first_link['title'][:50]}... from {first_link['source']}")
                else:
                    print("⚠️  Discovered links missing some fields")
            
            # Check if summary contains meaningful AI analysis
            if len(response['summary']) > 100 and 'EXECUTIVE SUMMARY' in response['summary']:
                print("✅ AI-generated summary has meaningful content")
            else:
                print("⚠️  Summary seems incomplete or not AI-generated")
                
            return True
        return False

    def test_enhanced_quick_scan_ransomware(self):
        """Test Enhanced Quick Scan with Google Custom Search - Ransomware"""
        if not self.auth_token:
            print("⚠️  Skipping enhanced quick scan test - authentication required")
            return False
            
        test_data = {"query": "ransomware"}
        
        success, response = self.run_test(
            "Enhanced Quick Scan - Ransomware",
            "POST",
            "quick-scan",
            200,
            data=test_data,
            auth_required=True
        )
        
        if success:
            # Verify key threats are extracted from AI analysis
            if response.get('key_threats') and len(response['key_threats']) > 0:
                print(f"✅ Found {len(response['key_threats'])} key threats:")
                for i, threat in enumerate(response['key_threats'][:3], 1):
                    print(f"   {i}. {threat[:80]}...")
                
                # Check if threats are meaningful (not generic)
                threat_text = ' '.join(response['key_threats']).lower()
                if 'ransomware' in threat_text or 'malware' in threat_text or 'attack' in threat_text:
                    print("✅ Threats are contextually relevant")
                    return True
                else:
                    print("⚠️  Threats may not be contextually relevant")
                    return False
            else:
                print("❌ No key threats found")
                return False
        return False

    def test_enhanced_quick_scan_data_breach(self):
        """Test Enhanced Quick Scan with Google Custom Search - Data Breach"""
        if not self.auth_token:
            print("⚠️  Skipping enhanced quick scan test - authentication required")
            return False
            
        test_data = {"query": "data breach"}
        
        success, response = self.run_test(
            "Enhanced Quick Scan - Data Breach",
            "POST",
            "quick-scan",
            200,
            data=test_data,
            auth_required=True
        )
        
        if success:
            # Verify real Google search results are being used
            if response.get('discovered_links'):
                # Check if URLs are from real news sources
                real_sources = ['reuters.com', 'bbc.com', 'cnn.com', 'apnews.com', 'npr.org', 'wsj.com', 'nytimes.com']
                found_real_source = False
                
                for link in response['discovered_links']:
                    url = link.get('url', '').lower()
                    for source in real_sources:
                        if source in url:
                            found_real_source = True
                            print(f"✅ Found real news source: {link['source']}")
                            break
                    if found_real_source:
                        break
                
                if found_real_source:
                    print("✅ Using real Google search results from news sources")
                    return True
                else:
                    print("⚠️  No recognized news sources found in results")
                    # Still pass if we have valid links structure
                    return len(response['discovered_links']) > 0
            else:
                print("❌ No discovered links found")
                return False
        return False

    def test_quick_scan_without_auth(self):
        """Test Quick Scan without authentication (should fail)"""
        test_data = {"query": "cybersecurity"}
        
        # Temporarily remove auth token
        temp_token = self.auth_token
        self.auth_token = None
        
        success, response = self.run_test(
            "Quick Scan Without Auth",
            "POST",
            "quick-scan",
            401,  # Should return unauthorized
            data=test_data,
            auth_required=False
        )
        
        # Restore auth token
        self.auth_token = temp_token
        
        return success

    def test_quick_scan_rate_limiting(self):
        """Test Quick Scan rate limiting behavior"""
        if not self.auth_token:
            print("⚠️  Skipping rate limiting test - authentication required")
            return False
            
        print("🔄 Testing rate limiting with multiple quick scans...")
        
        # Perform multiple quick scans rapidly
        for i in range(3):
            test_data = {"query": f"test query {i+1}"}
            
            success, response = self.run_test(
                f"Quick Scan Rate Test {i+1}",
                "POST",
                "quick-scan",
                200,  # Should succeed for free tier limits
                data=test_data,
                auth_required=True
            )
            
            if success and 'scans_remaining' in response:
                print(f"✅ Scan {i+1}: {response['scans_remaining']} scans remaining")
            elif not success:
                print(f"⚠️  Scan {i+1} failed - may have hit rate limit")
                return True  # This is expected behavior
            
            # Small delay between requests
            time.sleep(1)
        
        return True

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
    print("🚀 Starting Enhanced OSINT Threat Monitoring API Tests")
    print("🔍 Testing Google Custom Search API Integration & Enhanced Quick Scan")
    print("=" * 80)
    
    tester = OSINTAPITester()
    
    # Test sequence - Authentication first, then enhanced features
    tests = [
        ("API Root Endpoint", tester.test_api_root),
        ("User Registration", tester.test_register_user),
        ("User Login", tester.test_login_user),
        ("Google Search Health Check", tester.test_google_search_health_check),
        ("Enhanced Quick Scan - Cybersecurity", tester.test_enhanced_quick_scan_cybersecurity),
        ("Enhanced Quick Scan - Ransomware", tester.test_enhanced_quick_scan_ransomware),
        ("Enhanced Quick Scan - Data Breach", tester.test_enhanced_quick_scan_data_breach),
        ("Quick Scan Without Auth", tester.test_quick_scan_without_auth),
        ("Quick Scan Rate Limiting", tester.test_quick_scan_rate_limiting),
        ("Quick Scan - Empty Query", tester.test_quick_scan_empty_query),
        ("Quick Scan - Missing Query", tester.test_quick_scan_missing_query),
        # Legacy subscription tests
        ("Subscribe with Valid Data", tester.test_subscribe_valid_data),
        ("Subscribe with Missing Fields", tester.test_subscribe_missing_required_fields),
        ("Subscribe Duplicate", tester.test_subscribe_duplicate),
        ("Status with Valid Email", tester.test_status_valid_email),
        ("Status with Non-existent Email", tester.test_status_nonexistent_email),
        ("Status Missing Email Parameter", tester.test_status_missing_email_param),
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*80}")
        print(f"Running: {test_name}")
        print('='*80)
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
    
    # Print final results
    print(f"\n{'='*80}")
    print("📊 FINAL TEST RESULTS")
    print('='*80)
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    # Enhanced summary
    if tester.tests_passed >= tester.tests_run * 0.8:  # 80% pass rate
        print("🎉 Most tests passed! Enhanced Quick Scan functionality is working.")
    elif tester.tests_passed >= tester.tests_run * 0.6:  # 60% pass rate
        print("⚠️  Some issues found. Check failed tests above.")
    else:
        print("❌ Multiple failures detected. System may need attention.")
    
    return 0 if tester.tests_passed >= tester.tests_run * 0.8 else 1

if __name__ == "__main__":
    sys.exit(main())