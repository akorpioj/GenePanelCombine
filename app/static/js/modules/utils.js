/**
 * PanelMerge - Utility Functions
 * Common utility functions used across the application
 */

import { fieldsToSearch } from './state.js';

/**
 * Debounce function to limit API calls
 * @param {Function} fn - Function to debounce
 * @param {number} delay - Delay in milliseconds
 * @returns {Function} Debounced function
 */
export function debounce(fn, delay) {
    let t;
    return (...args) => {
        clearTimeout(t);
        t = setTimeout(() => fn(...args), delay);
    };
}

/**
 * Check if a panel matches the search term
 * @param {Object} panel - Panel object to search
 * @param {string} term - Search term
 * @returns {boolean} True if panel matches the search term
 */
export function matches(panel, term) {
    const txt = term.toLowerCase();
    return fieldsToSearch.some(key => {
        const val = panel[key];
        if (!val) return false;
        // if it's an array, check each element:
        if (Array.isArray(val)) {
            return val.some(item => item.toLowerCase().includes(txt));
        }
        // otherwise treat it as a string
        return String(val).toLowerCase().includes(txt);
    });
}
