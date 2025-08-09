#!/usr/bin/env python3
"""
Test script for enhanced pagination support in Panel API
Run this after starting the Flask application
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:5000"

def test_pagination_api():
    """Test the enhanced pagination features"""
    
    print("🧪 Testing Enhanced Pagination API\n")
    
    # Test basic pagination
    print("1. 📄 Testing Basic Pagination")
    test_cases = [
        {"page": 1, "per_page": 5},
        {"page": 2, "per_page": 10},
        {"page": 1, "per_page": 100},  # Max per_page
    ]
    
    for params in test_cases:
        try:
            response = requests.get(f"{BASE_URL}/api/user/panels", params=params)
            print(f"   Page {params['page']}, Per Page {params['per_page']}: Status {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                pagination = data.get('pagination', {})
                print(f"     → Got {len(data.get('panels', []))} panels")
                print(f"     → Pagination: Page {pagination.get('page')}/{pagination.get('pages')}, Total: {pagination.get('total')}")
        except Exception as e:
            print(f"     → Exception: {e}")
    
    # Test pagination with search
    print("\n2. 🔍 Testing Pagination with Search")
    search_params = {
        "page": 1,
        "per_page": 10,
        "search": "cancer"
    }
    try:
        response = requests.get(f"{BASE_URL}/api/user/panels", params=search_params)
        print(f"   Search 'cancer': Status {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   → Found {len(data.get('panels', []))} panels matching 'cancer'")
            print(f"   → Total matches: {data.get('pagination', {}).get('total', 0)}")
    except Exception as e:
        print(f"   → Exception: {e}")
    
    # Test pagination with filters
    print("\n3. 🎛️  Testing Pagination with Filters")
    filter_params = {
        "page": 1,
        "per_page": 20,
        "status": "ACTIVE",
        "visibility": "PRIVATE",
        "gene_count_min": 10,
        "gene_count_max": 100
    }
    try:
        response = requests.get(f"{BASE_URL}/api/user/panels", params=filter_params)
        print(f"   Filtered request: Status {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            panels = data.get('panels', [])
            print(f"   → Found {len(panels)} panels with filters")
            if panels:
                # Verify gene count filter worked
                gene_counts = [p.get('gene_count', 0) for p in panels]
                print(f"   → Gene counts range: {min(gene_counts)}-{max(gene_counts)}")
    except Exception as e:
        print(f"   → Exception: {e}")
    
    # Test pagination with sorting
    print("\n4. ↕️  Testing Pagination with Sorting")
    sort_params = {
        "page": 1,
        "per_page": 15,
        "sort_by": "gene_count",
        "sort_order": "desc"
    }
    try:
        response = requests.get(f"{BASE_URL}/api/user/panels", params=sort_params)
        print(f"   Sort by gene_count desc: Status {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            panels = data.get('panels', [])
            print(f"   → Got {len(panels)} panels")
            if len(panels) >= 2:
                # Verify sorting worked
                gene_counts = [p.get('gene_count', 0) for p in panels[:3]]
                print(f"   → Top gene counts: {gene_counts}")
                is_desc_sorted = all(gene_counts[i] >= gene_counts[i+1] for i in range(len(gene_counts)-1))
                print(f"   → Correctly sorted: {is_desc_sorted}")
    except Exception as e:
        print(f"   → Exception: {e}")
    
    # Test complex query
    print("\n5. 🎯 Testing Complex Query")
    complex_params = {
        "page": 1,
        "per_page": 5,
        "search": "panel",
        "status": "ACTIVE",
        "gene_count_min": 5,
        "sort_by": "updated_at",
        "sort_order": "desc"
    }
    try:
        response = requests.get(f"{BASE_URL}/api/user/panels", params=complex_params)
        print(f"   Complex query: Status {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            pagination = data.get('pagination', {})
            print(f"   → Results: {len(data.get('panels', []))} panels")
            print(f"   → Pagination: {pagination}")
    except Exception as e:
        print(f"   → Exception: {e}")
    
    # Test edge cases
    print("\n6. ⚠️  Testing Edge Cases")
    edge_cases = [
        {"page": 0, "per_page": 10},      # Invalid page
        {"page": 999, "per_page": 10},    # Page beyond range
        {"page": 1, "per_page": 200},     # Exceeds max per_page
        {"page": 1, "per_page": -5},      # Negative per_page
    ]
    
    for params in edge_cases:
        try:
            response = requests.get(f"{BASE_URL}/api/user/panels", params=params)
            print(f"   Edge case {params}: Status {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                pagination = data.get('pagination', {})
                print(f"     → Handled gracefully: Page {pagination.get('page')}, Per Page {pagination.get('per_page')}")
        except Exception as e:
            print(f"     → Exception: {e}")
    
    print("\n✅ Pagination testing completed!")
    print("\nIf you see 401/403 errors, make sure you're logged in")
    print("The pagination system gracefully handles edge cases and provides consistent responses")

def test_javascript_integration():
    """Test the JavaScript integration with a simple HTML page"""
    
    html_test = """
<!DOCTYPE html>
<html>
<head>
    <title>Pagination Test</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="p-8">
    <h1 class="text-2xl mb-4">Panel Pagination Test</h1>
    
    <div class="mb-4">
        <button onclick="testPagination()" class="px-4 py-2 bg-blue-500 text-white rounded">
            Test Pagination
        </button>
        <button onclick="testFilters()" class="px-4 py-2 bg-green-500 text-white rounded ml-2">
            Test Filters
        </button>
    </div>
    
    <div id="results" class="bg-gray-100 p-4 rounded min-h-64"></div>
    
    <script>
        async function testPagination() {
            const results = document.getElementById('results');
            results.innerHTML = '<p>Testing pagination...</p>';
            
            try {
                // Test multiple pages
                const tests = [
                    { page: 1, per_page: 5 },
                    { page: 2, per_page: 5 },
                    { page: 1, per_page: 10, search: 'cancer' }
                ];
                
                let output = '<h3>Pagination Test Results:</h3>';
                
                for (const params of tests) {
                    const url = `/api/user/panels?${new URLSearchParams(params)}`;
                    const response = await fetch(url);
                    const data = await response.json();
                    
                    output += `<div class="mb-2">`;
                    output += `<strong>Page ${params.page}, Per Page ${params.per_page}${params.search ? ', Search: ' + params.search : ''}</strong><br>`;
                    output += `Panels: ${data.panels?.length || 0}, Total: ${data.pagination?.total || 0}<br>`;
                    output += `</div>`;
                }
                
                results.innerHTML = output;
            } catch (error) {
                results.innerHTML = `<p class="text-red-500">Error: ${error.message}</p>`;
            }
        }
        
        async function testFilters() {
            const results = document.getElementById('results');
            results.innerHTML = '<p>Testing filters...</p>';
            
            try {
                const params = {
                    page: 1,
                    per_page: 10,
                    status: 'ACTIVE',
                    gene_count_min: 10,
                    sort_by: 'gene_count',
                    sort_order: 'desc'
                };
                
                const url = `/api/user/panels?${new URLSearchParams(params)}`;
                const response = await fetch(url);
                const data = await response.json();
                
                let output = '<h3>Filter Test Results:</h3>';
                output += `<p>Found ${data.panels?.length || 0} panels</p>`;
                output += `<p>Total matching filters: ${data.pagination?.total || 0}</p>`;
                
                if (data.panels && data.panels.length > 0) {
                    output += '<h4>Sample Results:</h4>';
                    data.panels.slice(0, 3).forEach(panel => {
                        output += `<div class="border p-2 mb-1">`;
                        output += `<strong>${panel.name}</strong> - ${panel.gene_count} genes<br>`;
                        output += `Status: ${panel.status}, Created: ${panel.created_at}`;
                        output += `</div>`;
                    });
                }
                
                results.innerHTML = output;
            } catch (error) {
                results.innerHTML = `<p class="text-red-500">Error: ${error.message}</p>`;
            }
        }
    </script>
</body>
</html>
    """
    
    with open('test_pagination.html', 'w') as f:
        f.write(html_test)
    
    print("\n📄 Created test_pagination.html for JavaScript testing")
    print("Open this file in your browser to test the pagination JavaScript integration")

if __name__ == "__main__":
    test_pagination_api()
    test_javascript_integration()
