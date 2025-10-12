#!/usr/bin/env python3
"""
Test script for the updated Panel API endpoints
Run this after starting the Flask application to test the new functionality
"""

import requests
import json
import time

# Configuration - update these values for your setup
BASE_URL = "http://localhost:5000"
# You'll need to get a valid session cookie or auth token for testing
# This is just a demo of the API structure

def test_panel_api():
    """Test the panel API endpoints"""
    
    print("🧪 Testing Panel API Endpoints\n")
    
    # Test data
    test_panel = {
        "name": "Test Cancer Panel",
        "description": "A test panel for cancer genes",
        "tags": "cancer,hereditary,test",
        "visibility": "PRIVATE",
        "status": "ACTIVE",
        "source_type": "manual",
        "genes": [
            {
                "symbol": "BRCA1",
                "ensembl_id": "ENSG00000012048",
                "name": "BRCA1 DNA repair associated",
                "confidence": "High",
                "mode_of_inheritance": "Autosomal dominant",
                "phenotypes": "Breast cancer, Ovarian cancer"
            },
            {
                "symbol": "BRCA2",
                "ensembl_id": "ENSG00000139618",
                "name": "BRCA2 DNA repair associated",
                "confidence": "High"
            },
            {
                "symbol": "TP53",
                "name": "tumor protein p53"
            }
        ]
    }
    
    # Headers for JSON requests
    headers = {
        'Content-Type': 'application/json'
    }
    
    print("1. 📋 Testing GET /api/user/panels (list panels)")
    try:
        response = requests.get(f"{BASE_URL}/api/user/panels")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Found {len(data.get('panels', []))} panels")
            print(f"   Pagination: {data.get('pagination', {})}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    print("\n2. ➕ Testing POST /api/user/panels (create panel)")
    try:
        response = requests.post(
            f"{BASE_URL}/api/user/panels",
            headers=headers,
            data=json.dumps(test_panel)
        )
        print(f"   Status: {response.status_code}")
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"   Created panel: {data.get('panel', {}).get('name')}")
            print(f"   Panel ID: {data.get('panel', {}).get('id')}")
            print(f"   Gene count: {data.get('panel', {}).get('gene_count')}")
            panel_id = data.get('panel', {}).get('id')
        else:
            print(f"   Error: {response.text}")
            panel_id = None
    except Exception as e:
        print(f"   Exception: {e}")
        panel_id = None
    
    if panel_id:
        print(f"\n3. 🔍 Testing GET /api/user/panels/{panel_id} (get panel details)")
        try:
            response = requests.get(f"{BASE_URL}/api/user/panels/{panel_id}")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                panel = data.get('panel', {})
                print(f"   Panel: {panel.get('name')}")
                print(f"   Genes: {len(panel.get('genes', []))}")
                print(f"   Last accessed: {panel.get('last_accessed_at')}")
            else:
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"   Exception: {e}")
        
        print(f"\n4. ✏️  Testing PUT /api/user/panels/{panel_id} (update panel)")
        update_data = {
            "name": "Updated Test Cancer Panel",
            "description": "Updated description with more details",
            "status": "ACTIVE",
            "genes": ["BRCA1", "BRCA2", "TP53", "ATM", "CHEK2"]  # Add more genes
        }
        try:
            response = requests.put(
                f"{BASE_URL}/api/user/panels/{panel_id}",
                headers=headers,
                data=json.dumps(update_data)
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Updated panel: {data.get('panel', {}).get('name')}")
                print(f"   New gene count: {data.get('panel', {}).get('gene_count')}")
            else:
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"   Exception: {e}")
        
        print(f"\n5. 🗑️  Testing DELETE /api/user/panels/{panel_id} (delete panel)")
        try:
            response = requests.delete(f"{BASE_URL}/api/user/panels/{panel_id}")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Message: {data.get('message')}")
            else:
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"   Exception: {e}")
    
    print("\n6. 🔍 Testing API with search and filters")
    try:
        # Test with search
        response = requests.get(f"{BASE_URL}/api/user/panels?search=cancer&sort_by=name&sort_order=asc")
        print(f"   Search 'cancer' - Status: {response.status_code}")
        
        # Test with status filter
        response = requests.get(f"{BASE_URL}/api/user/panels?status=ACTIVE&per_page=5")
        print(f"   Filter ACTIVE panels - Status: {response.status_code}")
        
        # Test with visibility filter
        response = requests.get(f"{BASE_URL}/api/user/panels?visibility=PRIVATE")
        print(f"   Filter PRIVATE panels - Status: {response.status_code}")
        
    except Exception as e:
        print(f"   Exception: {e}")
    
    print("\n✅ Panel API testing completed!")
    print("\nNote: If you see 401/403 errors, make sure you're logged in")
    print("You may need to run this script with proper authentication cookies/headers")

if __name__ == "__main__":
    test_panel_api()
