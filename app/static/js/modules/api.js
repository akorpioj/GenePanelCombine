/**
 * PanelMerge - API Management
 * Handles all API communications and data fetching
 */

import { allPanels, currentAPI, setCurrentAPI, updatePanels } from './state.js';

/**
 * Fetch panels from the specified API source
 * @param {string} apiSource - API source ('uk' or 'aus')
 */
export function fetchPanels(apiSource) {
    const url = `/api/panels?source=${apiSource}`;
    console.log(`Fetching panels from: ${url}`);
    
    fetch(url)
        .then(r => {
            if (!r.ok) {
                throw new Error(`HTTP ${r.status}: ${r.statusText}`);
            }
            return r.json();
        })
        .then(data => {
            console.log(`Received ${data.length} panels for ${apiSource} source`);
            updatePanels(apiSource, data);
            if (apiSource === currentAPI) {
                // Use dynamic import to avoid circular dependency
                import('./panelManager.js').then(module => {
                    module.populateAll().catch(console.error);
                });
            }
        })
        .catch(error => {
            console.error(`Failed to fetch panels for ${apiSource}:`, error);
            // Set empty array so we don't keep trying
            updatePanels(apiSource, []);
        });
}

/**
 * Switch between different API sources
 * @param {string} apiSource - API source to switch to
 */
export function switchAPI(apiSource) {
    setCurrentAPI(apiSource);
    
    // Update tab styling
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById(`${apiSource}-tab`).classList.add('active');
    
    // Show/hide upload form
    document.getElementById('upload-panel-form').style.display = (apiSource === 'upload') ? '' : 'none';
    
    // Show/hide panelapp-section
    var panelAppSection = document.getElementById('panelapp-section');
    if (panelAppSection) {
        panelAppSection.style.display = (apiSource === 'upload') ? 'none' : '';
    }
    
    // Update panel lists
    if (apiSource !== 'upload') {
        // Set loading state first, then populate
        import('./panelManager.js').then(module => {
            module.setLoadingState();
            module.populateAll().catch(console.error);
        });
    }
}

/**
 * Fetch gene suggestions for autocomplete
 * @param {string} query - Search query
 * @param {string} source - API source
 * @param {number} limit - Maximum number of suggestions
 * @returns {Promise<Array>} Promise resolving to suggestions array
 */
export async function fetchGeneSuggestions(query, source, limit = 8) {
    const response = await fetch(`/api/gene-suggestions?q=${encodeURIComponent(query)}&source=${source}&limit=${limit}`);
    if (response.ok) {
        return await response.json();
    }
    throw new Error(`Failed to fetch gene suggestions: ${response.status}`);
}

/**
 * Fetch panels containing a specific gene
 * @param {string} gene - Gene name
 * @param {string} source - API source
 * @returns {Promise<Array>} Promise resolving to panels array
 */
export async function fetchPanelsByGene(gene, source) {
    const geneUrl = `/api/genes/${encodeURIComponent(gene)}?source=${source}`;
    const response = await fetch(geneUrl);
    if (response.ok) {
        return await response.json();
    }
    throw new Error(`Failed to fetch panels by gene: ${response.status}`);
}

/**
 * Fetch detailed panel information for comparison
 * @param {string} panelIds - Comma-separated panel IDs
 * @returns {Promise<Array>} Promise resolving to panel details array
 */
export async function fetchPanelDetails(panelIds) {
    const response = await fetch(`/api/panel-details?panel_ids=${encodeURIComponent(panelIds)}`);
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.json();
}

/**
 * Fetch uploaded user panel files from backend
 * @returns {Promise<Array>} Promise resolving to uploaded files array
 */
export async function fetchUploadedFiles() {
    try {
        const resp = await fetch('/uploaded_user_panels');
        if (!resp.ok) return [];
        const data = await resp.json();
        return data.files || [];
    } catch (e) {
        return [];
    }
}

/**
 * Upload user panel files to server
 * @param {FormData} formData - Form data containing files
 * @returns {Promise<Response>} Promise resolving to fetch response
 */
export function uploadPanelFiles(formData) {
    return fetch('/upload_user_panel', {
        method: 'POST',
        body: formData
    });
}

/**
 * Remove a user panel file from server
 * @param {string} sheetName - Name of the sheet to remove
 * @returns {Promise<Response>} Promise resolving to fetch response
 */
export function removeUserPanel(sheetName) {
    return fetch('/remove_user_panel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sheet_name: sheetName })
    });
}
