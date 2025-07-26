/**
 * PanelMerge - Main Application Entry Point
 * Imports and initializes all application modules
 */

// Import modules
import { fetchPanels, switchAPI } from './modules/api.js';
import { clearAll, clearPanel, setLoadingState } from './modules/panelManager.js';
import { initializeAutocomplete } from './modules/autocomplete.js';
import { initializeDragAndDrop, initializeFileUpload } from './modules/fileUpload.js';
import { openPanelComparison } from './modules/panelComparison.js';
import { initializePanelPreview } from './modules/panelPreview.js';
import { initializeEnhancedDownload } from './modules/downloadManager.js';

/**
 * Initialize all functionality when DOM is loaded
 */
function initializeApp() {
    console.log("PanelMerge: Initializing application");
    
    // Set initial loading state for panel selects
    setLoadingState();
    
    // Initialize all components
    initializeAutocomplete();
    initializeDragAndDrop();
    initializeFileUpload();
    initializePanelPreview();
    initializeEnhancedDownload();
    
    console.log("PanelMerge: Application initialized successfully");
}

// Make functions globally available for HTML onclick handlers
window.switchAPI = switchAPI;
window.clearAll = clearAll;
window.clearPanel = clearPanel;
window.openPanelComparison = openPanelComparison;

// Initialize panels data immediately
fetchPanels('uk');
fetchPanels('aus');

// Initialize app when DOM is ready
document.addEventListener("DOMContentLoaded", initializeApp);
