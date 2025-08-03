/**
 * PanelMerge - Global State Management
 * Manages global application state and configuration
 */

// =============================================================================
// GLOBAL STATE AND CONFIGURATION
// =============================================================================

export let allPanels = { uk: [], aus: [] };
export let currentAPI = 'uk';
export const maxPanels = window.maxPanels || 10; // Keep for backward compatibility
export const listTypeOptions = window.listTypeOptions || ['Whole gene panel', 'High evidence (Green only)', 'High + Moderate evidence (Green + Amber)', 'All evidence levels (Green + Amber + Red)']; // Get from global or default

// Dynamic panel management
let dynamicMaxPanels = 3; // Default starting panels

/**
 * Get current maximum panels (dynamic)
 * @returns {number} Current max panels
 */
export function getMaxPanels() {
    return dynamicMaxPanels;
}

/**
 * Set current maximum panels (dynamic)
 * @param {number} count - New panel count
 */
export function setMaxPanels(count) {
    dynamicMaxPanels = count;
}

// Search configuration
export const fieldsToSearch = [
    'display_name',
    'description',
    'disease_group',
    'disease_sub_group',
];

/**
 * Update the current API source
 * @param {string} apiSource - New API source
 */
export function setCurrentAPI(apiSource) {
    currentAPI = apiSource;
}

/**
 * Update panels data for a specific source
 * @param {string} source - API source
 * @param {Array} panels - Panel data array
 */
export function updatePanels(source, panels) {
    allPanels[source] = panels;
}

/**
 * Get panels for current API source
 * @returns {Array} Current panels array
 */
export function getCurrentPanels() {
    return allPanels[currentAPI];
}

/**
 * Get all panels across all sources
 * @returns {Array} Combined panels array
 */
export function getAllPanels() {
    return allPanels.uk.concat(allPanels.aus);
}
