/**
 * PanelMerge - Panel Management
 * Handles panel selection, filtering, and UI updates
 */

import { allPanels, currentAPI, maxPanels, listTypeOptions, getAllPanels } from './state.js';
import { matches } from './utils.js';
import { fetchPanelsByGene } from './api.js';

/**
 * Set loading state for all panel selects
 */
export function setLoadingState() {
    for (let i = 1; i <= maxPanels; i++) {
        const select = document.getElementById(`panel_id_${i}`);
        if (select) {
            // Only set loading if the select is currently empty or has no real options
            const hasRealOptions = Array.from(select.options).some(opt => 
                opt.value !== "Loading" && opt.value !== "None" && opt.value !== ""
            );
            
            if (!hasRealOptions) {
                select.innerHTML = '<option value="Loading" disabled selected>Loading panels...</option>';
                select.classList.remove('panel-source-uk', 'panel-source-aus');
            }
        }
    }
}

/**
 * Populate all panel select dropdowns with filtered results
 */
export async function populateAll() {
    // Check if we have data for the current API
    if (!allPanels[currentAPI] || allPanels[currentAPI].length === 0) {
        console.log(`No data available for ${currentAPI} source, keeping loading state`);
        return;
    }

    const term = document.getElementById("search_term_input")
        .value.trim().toLowerCase();

    // Start with text-based filtering
    let filtered = allPanels[currentAPI].filter(p => matches(p, term));

    // If the search term is a single word, also try fetching panels by gene name
    if (term && !term.includes(' ') && term.length > 1) {
        try {
            const genePanels = await fetchPanelsByGene(term, currentAPI);
            if (genePanels && Array.isArray(genePanels)) {
                // Merge gene panels with text-filtered results, removing duplicates
                const existingIds = new Set(filtered.map(p => `${p.id}-${p.api_source}`));
                genePanels.forEach(genePanel => {
                    const panelKey = `${genePanel.id}-${genePanel.api_source}`;
                    if (!existingIds.has(panelKey)) {
                        filtered.push(genePanel);
                        existingIds.add(panelKey);
                    }
                });
            }
        } catch (error) {
            console.log('Gene search failed, continuing with text search only:', error);
        }
    }

    for (let i = 1; i <= maxPanels; i++) {
        const select = document.getElementById(`panel_id_${i}`);
        const current = select.value || "None";
        
        // Keep current selection if it's from any source
        const currentPanel = ((current !== "None") &&
            getAllPanels().find(p => (String(p.id) + '-' + p.api_source) === current));
        
        updateSelectOptions(select, filtered, current, currentPanel);
    }
}

/**
 * Update select element options with filtered panel list
 * @param {HTMLSelectElement} select - Select element to update
 * @param {Array} list - Filtered panel list
 * @param {string} current - Currently selected value
 * @param {Object} currentPanel - Currently selected panel object
 */
export function updateSelectOptions(select, list, current, currentPanel) {
    // start with a "None" option
    const options = [{ id: "None", display_name: "None" }];
    const seen = new Set(["None"]);

    // add all filtered
    list.forEach(p => {
        options.push(p);
        seen.add(String(p.id) + '-' + p.api_source); // Combine ID + source
    });

    // if current selection was cleared but isn't in filtered, re-include it
    if (currentPanel && !seen.has(current)) {
        options.push(currentPanel);
        seen.add(current);
    }

    // sort ("None" stays first)
    options.sort((a, b) => {
        if (a.id === "None") return -1;
        if (b.id === "None") return 1;
        return a.display_name.localeCompare(b.display_name);
    });

    // rebuild DOM
    select.innerHTML = "";
    options.forEach(opt => {
        const o = document.createElement("option");
        if (opt.id === "None") {
            o.value = "None";
            o.textContent = "None";
        } else {
            o.value = `${opt.id}-${opt.api_source}`; // Combine ID + source
            o.textContent = opt.display_name;
        }
        o.dataset.source = opt.api_source;            
        if (String(o.value) === String(current)) {
            o.selected = true;
            // Add a visual indicator of the source and update the hidden source input
            select.classList.remove('panel-source-uk', 'panel-source-aus');
            if (opt.api_source) {
                select.classList.add(`panel-source-${opt.api_source}`);
                // Update the hidden source input
                const panelNumber = select.id.replace('panel_id_', '');
                document.getElementById(`api_source_${panelNumber}`).value = opt.api_source;
            }
        }
        select.append(o);
    });
}

/**
 * Clear a specific panel selection
 * @param {number} i - Panel index to clear
 */
export function clearPanel(i) {
    const sel = document.getElementById(`panel_id_${i}`);
    const sel2 = document.getElementById(`list_type_${i}`);
    sel.value = "None";
    sel2.value = listTypeOptions[0];
    sel.classList.remove('panel-source-uk', 'panel-source-aus');
}

/**
 * Clear all panel selections and search term
 */
export function clearAll() {
    // Clear search input
    document.getElementById('search_term_input').value = '';
    
    // Clear all panel selections
    for (let i = 1; i <= maxPanels; i++) {
        clearPanel(i);
    }
    
    // Refresh the panel list without any filters
    populateAll().catch(console.error);
}

/**
 * Get currently selected panels for comparison
 * @returns {Array} Array of selected panel objects
 */
export function getSelectedPanels() {
    const selectedPanels = [];
    for (let i = 1; i <= maxPanels; i++) {
        const select = document.getElementById(`panel_id_${i}`);
        if (select && select.value !== "None") {
            selectedPanels.push({
                id: select.value,
                name: select.options[select.selectedIndex].textContent,
                index: i
            });
        }
    }
    return selectedPanels;
}
