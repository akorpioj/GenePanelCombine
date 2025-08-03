/**
 * PanelMerge - Dynamic Panel Management
 * Handles adding/removing panel configurations dynamically
 */

import { currentAPI, listTypeOptions, setMaxPanels } from './state.js';
import { populateAll, clearPanel } from './panelManager.js';

// Track current panel configuration
let currentPanelCount = 3; // Default: 3 panels
const minPanels = 1;
const maxPanels = 8; // Keep the existing maximum

/**
 * Initialize dynamic panel management
 */
export function initializeDynamicPanels() {
    const addBtn = document.getElementById('add-panel-btn');
    const removeBtn = document.getElementById('remove-panel-btn');
    
    if (addBtn) {
        addBtn.addEventListener('click', addPanel);
    }
    
    if (removeBtn) {
        removeBtn.addEventListener('click', removePanel);
    }
    
    // Create initial panels (default: 3)
    createInitialPanels();
    updatePanelControls();
    
    // Update the global state
    setMaxPanels(currentPanelCount);
}

/**
 * Create initial panel configurations
 */
function createInitialPanels() {
    const container = document.getElementById('panel-configurations-container');
    if (!container) return;
    
    // Clear existing panels
    container.innerHTML = '';
    
    // Create default panels
    for (let i = 1; i <= currentPanelCount; i++) {
        createPanelConfiguration(i);
    }
    
    updatePanelCount();
}

/**
 * Create a single panel configuration
 * @param {number} panelIndex - Panel number
 */
function createPanelConfiguration(panelIndex) {
    const container = document.getElementById('panel-configurations-container');
    if (!container) return;
    
    const panelDiv = document.createElement('div');
    panelDiv.className = 'p-5 border border-gray-200 rounded-lg shadow-sm bg-gray-50';
    panelDiv.id = `panel-config-${panelIndex}`;
    
    panelDiv.innerHTML = `
        <div class="flex justify-between items-center mb-4">
            <h2 class="text-xl font-semibold text-sky-600">Panel ${panelIndex} Configuration</h2>
            <button type="button" onclick="clearPanel(${panelIndex});" class="btn btn-clear">Clear Panel ${panelIndex}</button>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
                <label for="panel_id_${panelIndex}" class="block text-sm font-medium text-gray-700 mb-1">Select Panel ${panelIndex}:</label>
                <select name="panel_id_${panelIndex}" id="panel_id_${panelIndex}" 
                        class="form-select-arrow form-select-custom mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm sm:text-sm appearance-none">
                    <option value="Loading" disabled selected>Loading panels...</option>
                </select>
                <input type="hidden" name="api_source_${panelIndex}" id="api_source_${panelIndex}" value="${currentAPI}">
                <button type="button" id="preview-btn-${panelIndex}" class="preview-btn mt-2 px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500">
                    👁️ Preview
                </button>
            </div>
            <div>
                <label for="list_type_${panelIndex}" class="block text-sm font-medium text-gray-700 mb-1">Select List Type for Panel ${panelIndex}:</label>
                <select name="list_type_${panelIndex}" id="list_type_${panelIndex}" 
                    class="form-select-arrow form-select-custom mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm sm:text-sm appearance-none">
                    ${generateListTypeOptions()}
                </select>
            </div>
        </div>
    `;
    
    container.appendChild(panelDiv);
    
    // Add panel change listener for preview functionality
    const panelSelect = panelDiv.querySelector(`#panel_id_${panelIndex}`);
    const previewBtn = panelDiv.querySelector(`#preview-btn-${panelIndex}`);
    
    if (panelSelect) {
        panelSelect.addEventListener('change', function() {
            handlePanelSelection(panelIndex);
        });
    }
    
    // Add preview button click handler
    if (previewBtn) {
        previewBtn.addEventListener('click', function() {
            handlePreviewClick(panelIndex);
        });
    }
}

/**
 * Generate list type options HTML
 * @returns {string} HTML options string
 */
function generateListTypeOptions() {
    return listTypeOptions.map(opt => 
        `<option value="${opt}">${opt}</option>`
    ).join('');
}

/**
 * Handle panel selection change (for preview functionality)
 * @param {number} panelIndex - Panel index
 */
function handlePanelSelection(panelIndex) {
    // This function can be used for other panel selection logic if needed
    // Preview button is now always shown and handled separately
}

/**
 * Handle preview button click
 * @param {number} panelIndex - Panel index
 */
async function handlePreviewClick(panelIndex) {
    const select = document.getElementById(`panel_id_${panelIndex}`);
    const previewBtn = document.getElementById(`preview-btn-${panelIndex}`);
    
    if (!select || !previewBtn) return;
    
    // Import preview functions
    const { showPanelPreview, showPanelSelectionForPreview } = await import('./panelPreview.js');
    
    // Check if a panel is selected
    if (select.value && select.value !== "None" && select.value !== "Loading" && select.value !== "") {
        // Panel is selected - show direct preview
        await showPanelPreview(select.value, previewBtn, select);
    } else {
        // No panel selected - show panel selection modal
        showPanelSelectionForPreview(select, previewBtn);
    }
}

/**
 * Add a new panel configuration
 */
function addPanel() {
    if (currentPanelCount >= maxPanels) return;
    
    currentPanelCount++;
    createPanelConfiguration(currentPanelCount);
    updatePanelControls();
    updatePanelCount();
    
    // Update global state
    setMaxPanels(currentPanelCount);
    
    // Populate the new panel with current search results
    populateAll().catch(console.error);
    
    // Scroll to the new panel
    const newPanel = document.getElementById(`panel-config-${currentPanelCount}`);
    if (newPanel) {
        newPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

/**
 * Remove the last panel configuration
 */
function removePanel() {
    if (currentPanelCount <= minPanels) return;
    
    // Clear the panel first to clean up any event listeners
    clearPanel(currentPanelCount);
    
    // Remove the panel DOM element
    const panelToRemove = document.getElementById(`panel-config-${currentPanelCount}`);
    if (panelToRemove) {
        panelToRemove.remove();
    }
    
    currentPanelCount--;
    updatePanelControls();
    updatePanelCount();
    
    // Update global state
    setMaxPanels(currentPanelCount);
}

/**
 * Update panel control buttons state
 */
function updatePanelControls() {
    const addBtn = document.getElementById('add-panel-btn');
    const removeBtn = document.getElementById('remove-panel-btn');
    
    if (addBtn) {
        addBtn.disabled = currentPanelCount >= maxPanels;
    }
    
    if (removeBtn) {
        removeBtn.disabled = currentPanelCount <= minPanels;
    }
}

/**
 * Update panel count display
 */
function updatePanelCount() {
    const countDisplay = document.getElementById('current-panel-count');
    if (countDisplay) {
        countDisplay.textContent = currentPanelCount;
    }
}

/**
 * Get current panel count
 * @returns {number} Current number of panels
 */
export function getCurrentPanelCount() {
    return currentPanelCount;
}

/**
 * Update max panels reference for other modules
 * @returns {number} Current panel count (for compatibility)
 */
export function getMaxPanels() {
    return currentPanelCount;
}

// Make functions available globally for onclick handlers
window.clearPanel = clearPanel;
