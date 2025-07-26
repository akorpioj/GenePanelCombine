/**
 * PanelMerge - Main Application Entry Point
 * Imports and initializes all application modules
 */

// Import modules
import { fetchPanels, switchAPI } from './modules/api.js';
import { clearAll } from './modules/panelManager.js';
import { initializeAutocomplete } from './modules/autocomplete.js';
import { initializeDragAndDrop, initializeFileUpload } from './modules/fileUpload.js';
import { openPanelComparison } from './modules/panelComparison.js';

/**
 * Initialize all functionality when DOM is loaded
 */
function initializeApp() {
    console.log("PanelMerge: Initializing application");
    
    // Initialize all components
    initializeAutocomplete();
    initializeDragAndDrop();
    initializeFileUpload();
    
    console.log("PanelMerge: Application initialized successfully");
}

// Make functions globally available for HTML onclick handlers
window.switchAPI = switchAPI;
window.clearAll = clearAll;
window.openPanelComparison = openPanelComparison;

// Initialize panels data immediately
fetchPanels('uk');
fetchPanels('aus');

// Initialize app when DOM is ready
document.addEventListener("DOMContentLoaded", initializeApp);
