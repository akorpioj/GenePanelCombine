#!/usr/bin/env python3

"""
Test script to verify the panel gene creation fix works correctly
"""

import requests
import json

def test_panel_creation_with_empty_genes():
    """Test creating a panel with various gene input scenarios"""
    
    base_url = "http://127.0.0.1:5001"
    
    # Test data with problematic gene inputs
    test_cases = [
        {
            "name": "Test Panel with Empty Genes",
            "description": "Testing empty gene handling",
            "genes": ["BRCA1", "", "BRCA2", "   ", "TP53"]  # Contains empty strings
        },
        {
            "name": "Test Panel with Duplicate Genes", 
            "description": "Testing duplicate gene handling",
            "genes": ["BRCA1", "BRCA2", "BRCA1", "TP53", "BRCA2"]  # Contains duplicates
        },
        {
            "name": "Test Panel with Mixed Input",
            "description": "Testing mixed input handling", 
            "genes": "BRCA1,,BRCA2,  ,TP53,BRCA1"  # String with empty values and duplicates
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: {test_case['name']} ---")
        
        try:
            response = requests.post(
                f"{base_url}/api/user/panels",
                json=test_case,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Panel created successfully!")
                print(f"   Panel ID: {data.get('id')}")
                print(f"   Gene Count: {data.get('gene_count')}")
                print(f"   Name: {data.get('name')}")
            else:
                print(f"❌ Failed to create panel")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('error', 'Unknown error')}")
                except:
                    print(f"   Error: {response.text}")
                    
        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to server at {base_url}")
            print("   Make sure the Flask server is running")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    print("🧪 Testing Panel Gene Creation Fix")
    print("=" * 50)
    test_panel_creation_with_empty_genes()
    print("\n" + "=" * 50)
    print("🏁 Test completed!")
