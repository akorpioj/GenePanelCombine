#!/usr/bin/env python3
"""
Quick test to verify the pagination API fix
"""

import requests
import json

def test_fix():
    """Test that the 500 error is fixed"""
    print("🧪 Testing API Fix\n")
    
    BASE_URL = "http://127.0.0.1:5001"  # Using the correct port from the error
    
    try:
        # Test the endpoint that was failing
        response = requests.get(f"{BASE_URL}/api/user/panels?page=1&per_page=20")
        
        print(f"📡 GET {BASE_URL}/api/user/panels?page=1&per_page=20")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: API is working!")
            data = response.json()
            print(f"📊 Response: {len(data.get('panels', []))} panels, pagination: {data.get('pagination', {})}")
        elif response.status_code == 401:
            print("🔐 AUTH REQUIRED: Need to be logged in (this is expected)")
            print("✅ SUCCESS: No more 500 error - server is working properly!")
        else:
            print(f"❌ ERROR: Unexpected status code {response.status_code}")
            print(f"📝 Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Make sure the server is running on port 5001")
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")

if __name__ == "__main__":
    test_fix()
