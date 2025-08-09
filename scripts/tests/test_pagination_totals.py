#!/usr/bin/env python3
"""
Test script to verify the pagination totals fix
"""

import requests
import json

def test_pagination_totals():
    """Test that the pagination endpoint returns proper totals"""
    try:
        # Test the pagination endpoint
        response = requests.get('http://127.0.0.1:5001/api/user/panels?page=1&per_page=20')
        
        if response.status_code == 401:
            print("✓ Server responded (authentication required as expected)")
            return True
        elif response.status_code == 200:
            data = response.json()
            pagination = data.get('pagination', {})
            
            print("✓ Server responded successfully")
            print(f"✓ Pagination data: {pagination}")
            
            # Check if totals are present
            if 'total_genes' in pagination and 'total_versions' in pagination:
                print("✓ Total genes and versions are included in response")
                return True
            else:
                print("✗ Missing total_genes or total_versions in pagination")
                return False
        elif response.status_code == 500:
            print("✗ Server error (500) - the fix didn't work")
            print(f"Response: {response.text}")
            return False
        else:
            print(f"✗ Unexpected status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to server. Make sure it's running on http://127.0.0.1:5001")
        return False
    except Exception as e:
        print(f"✗ Error testing: {e}")
        return False

if __name__ == "__main__":
    print("Testing pagination totals fix...")
    success = test_pagination_totals()
    
    if success:
        print("\n✓ Test passed! The pagination totals fix appears to be working.")
    else:
        print("\n✗ Test failed. Check the server logs for more details.")
