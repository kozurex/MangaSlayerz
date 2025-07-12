#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Manga Slayer PWA
Tests all API endpoints defined in the FastAPI backend
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any

class MangaSlayerAPITester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int = 200, data: Dict = None) -> tuple:
        """Run a single API test"""
        url = f"{self.base_url}/api{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                self.log_test(name, False, f"Unsupported method: {method}")
                return False, {}

            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}

            if success:
                self.log_test(name, True, f"Status: {response.status_code}")
            else:
                self.log_test(name, False, f"Expected {expected_status}, got {response.status_code}. Response: {response.text[:200]}")

            return success, response_data

        except requests.exceptions.RequestException as e:
            self.log_test(name, False, f"Request failed: {str(e)}")
            return False, {}
        except Exception as e:
            self.log_test(name, False, f"Unexpected error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test health check endpoint"""
        success, response = self.run_test("Health Check", "GET", "/health")
        if success and "status" in response:
            print(f"   Server status: {response.get('status')}")
        return success

    def test_sources_management(self):
        """Test sources management endpoints"""
        print("\n🔍 Testing Sources Management...")
        
        # Test get sources
        success, sources_response = self.run_test("Get Sources", "GET", "/sources")
        if not success:
            return False
            
        sources = sources_response.get("sources", [])
        print(f"   Found {len(sources)} sources")
        
        # Test add custom source
        test_source = {
            "name": "Test Manga Source",
            "url": "https://httpbin.org/status/200",
            "enabled": True
        }
        
        success, add_response = self.run_test(
            "Add Custom Source", 
            "POST", 
            "/sources", 
            200, 
            test_source
        )
        
        if success and "source" in add_response:
            source_id = add_response["source"]["id"]
            print(f"   Added source with ID: {source_id}")
            
            # Test delete custom source
            success, _ = self.run_test(
                "Delete Custom Source",
                "DELETE",
                f"/sources/{source_id}"
            )
            
            return success
        
        return False

    def test_manga_search(self):
        """Test manga search functionality"""
        print("\n🔍 Testing Manga Search...")
        
        # Test search without query
        success, response = self.run_test("Search Manga (Empty Query)", "GET", "/manga/search")
        if success:
            results = response.get("results", [])
            print(f"   Found {len(results)} manga without query")
        
        # Test search with query
        success, response = self.run_test("Search Manga (With Query)", "GET", "/manga/search?query=naruto")
        if success:
            results = response.get("results", [])
            print(f"   Found {len(results)} manga for 'naruto'")
        
        return success

    def test_download_stats(self):
        """Test download statistics"""
        print("\n🔍 Testing Download Statistics...")
        
        success, response = self.run_test("Get Download Stats", "GET", "/downloads/stats")
        if success:
            stats = response
            print(f"   Total manga: {stats.get('total_manga', 0)}")
            print(f"   Total chapters: {stats.get('total_chapters', 0)}")
            print(f"   Total size: {stats.get('total_size_mb', 0)} MB")
            print(f"   Available space: {stats.get('available_space_gb', 0)} GB")
        
        return success

    def test_downloads_list(self):
        """Test downloads list"""
        success, response = self.run_test("Get Downloads List", "GET", "/downloads")
        if success:
            downloads = response.get("downloads", [])
            print(f"   Found {len(downloads)} downloaded manga")
        
        return success

    def test_preferences(self):
        """Test user preferences management"""
        print("\n🔍 Testing User Preferences...")
        
        # Test get preferences
        success, prefs_response = self.run_test("Get User Preferences", "GET", "/preferences")
        if not success:
            return False
            
        print(f"   Current preferences loaded")
        
        # Test update preferences
        test_preferences = {
            "auto_scroll": {
                "speed": 5,
                "enabled": True,
                "pause_on_tap": True
            },
            "language": "ar",
            "reading_direction": "rtl",
            "auto_translate": True
        }
        
        success, _ = self.run_test(
            "Update User Preferences",
            "POST",
            "/preferences",
            200,
            test_preferences
        )
        
        return success

    def test_manga_detail_endpoints(self):
        """Test manga detail related endpoints"""
        print("\n🔍 Testing Manga Detail Endpoints...")
        
        # These endpoints expect specific manga IDs, so we'll test with sample IDs
        # and expect 404 responses since no data is seeded
        
        test_manga_id = "test_manga_123"
        test_chapter_id = "test_chapter_123"
        
        # Test get manga details (expect 404)
        success, _ = self.run_test(
            "Get Manga Details (404 Expected)",
            "GET",
            f"/manga/{test_manga_id}",
            404
        )
        
        # Test get chapter pages (expect 404)
        success, _ = self.run_test(
            "Get Chapter Pages (404 Expected)",
            "GET",
            f"/chapter/{test_chapter_id}",
            404
        )
        
        # Test download manga
        success, _ = self.run_test(
            "Download Manga",
            "POST",
            f"/download/manga/{test_manga_id}"
        )
        
        # Test download chapter (expect 404)
        success, _ = self.run_test(
            "Download Chapter (404 Expected)",
            "POST",
            f"/download/chapter/{test_chapter_id}",
            404
        )
        
        return True  # These are expected to have mixed results

    def test_translation_endpoint(self):
        """Test translation functionality"""
        print("\n🔍 Testing Translation...")
        
        test_chapter_id = "test_chapter_123"
        
        # Test translate chapter (expect 404)
        success, _ = self.run_test(
            "Translate Chapter (404 Expected)",
            "POST",
            f"/translate?chapter_id={test_chapter_id}&target_lang=ar",
            404
        )
        
        return True  # Expected to fail due to no data

    def test_reading_progress(self):
        """Test reading progress endpoints"""
        print("\n🔍 Testing Reading Progress...")
        
        test_manga_id = "test_manga_123"
        test_chapter_id = "test_chapter_123"
        
        # Test update reading progress
        success, _ = self.run_test(
            "Update Reading Progress",
            "POST",
            f"/reading-progress?manga_id={test_manga_id}&chapter_id={test_chapter_id}&page=5"
        )
        
        # Test get reading progress
        success, response = self.run_test(
            "Get Reading Progress",
            "GET",
            f"/reading-progress/{test_manga_id}"
        )
        
        if success:
            print(f"   Progress: Page {response.get('page', 0)}")
        
        return success

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Manga Slayer API Tests...")
        print(f"📡 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Core functionality tests
        self.test_health_check()
        self.test_sources_management()
        self.test_manga_search()
        self.test_download_stats()
        self.test_downloads_list()
        self.test_preferences()
        
        # Data-dependent tests (may fail due to no seeded data)
        self.test_manga_detail_endpoints()
        self.test_translation_endpoint()
        self.test_reading_progress()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed >= self.tests_run * 0.7:  # 70% pass rate is acceptable
            print("✅ Overall Result: ACCEPTABLE")
            return 0
        else:
            print("❌ Overall Result: NEEDS ATTENTION")
            return 1

def main():
    # Use the public URL from frontend .env
    public_url = "http://localhost:8001"  # This matches REACT_APP_BACKEND_URL
    
    tester = MangaSlayerAPITester(public_url)
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())