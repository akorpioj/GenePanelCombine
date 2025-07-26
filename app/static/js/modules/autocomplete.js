/**
 * PanelMerge - Autocomplete Functionality
 * Handles gene search autocomplete and suggestions
 */

import { currentAPI } from './state.js';
import { debounce } from './utils.js';
import { fetchGeneSuggestions } from './api.js';
import { populateAll } from './panelManager.js';

/**
 * Initialize autocomplete functionality for gene search
 */
export function initializeAutocomplete() {
    const searchInput = document.getElementById("search_term_input");
    if (!searchInput) return;

    // Create autocomplete dropdown
    const autocompleteDiv = document.createElement('div');
    autocompleteDiv.id = 'autocomplete-suggestions';
    autocompleteDiv.className = 'absolute z-50 w-full bg-white border border-gray-300 rounded-md shadow-lg mt-1 max-h-48 overflow-y-auto hidden';
    searchInput.parentNode.style.position = 'relative';
    searchInput.parentNode.appendChild(autocompleteDiv);
    
    let suggestionTimeout;
    let currentSuggestions = [];
    let selectedIndex = -1;
    
    // Function to show gene suggestions
    async function showGeneSuggestions(query) {
        if (query.length < 2 || query.includes(' ')) {
            hideAutocomplete();
            return;
        }
        
        try {
            const suggestions = await fetchGeneSuggestions(query, currentAPI, 8);
            displaySuggestions(suggestions, query);
        } catch (error) {
            console.error('Error fetching gene suggestions:', error);
            hideAutocomplete();
        }
    }
    
    // Function to display suggestions
    function displaySuggestions(suggestions, query) {
        currentSuggestions = suggestions;
        selectedIndex = -1;
        
        if (suggestions.length === 0) {
            hideAutocomplete();
            return;
        }
        
        autocompleteDiv.innerHTML = '';
        suggestions.forEach((suggestion, index) => {
            const item = document.createElement('div');
            item.className = 'px-3 py-2 cursor-pointer hover:bg-sky-100 text-sm';
            
            // Highlight matching part
            const regex = new RegExp(`(${query})`, 'gi');
            const highlightedText = suggestion.replace(regex, '<strong>$1</strong>');
            item.innerHTML = `${highlightedText} <span class="text-xs text-gray-500">gene</span>`;
            
            item.addEventListener('click', () => {
                searchInput.value = suggestion;
                hideAutocomplete();
                populateAll().catch(console.error);
            });
            
            autocompleteDiv.appendChild(item);
        });
        
        autocompleteDiv.classList.remove('hidden');
    }
    
    // Function to hide autocomplete
    function hideAutocomplete() {
        autocompleteDiv.classList.add('hidden');
        currentSuggestions = [];
        selectedIndex = -1;
    }
    
    // Update visual selection
    function updateSelection() {
        const items = autocompleteDiv.querySelectorAll('div');
        items.forEach((item, index) => {
            if (index === selectedIndex) {
                item.classList.add('bg-sky-100');
            } else {
                item.classList.remove('bg-sky-100');
            }
        });
    }

    // Search input event handler
    searchInput.addEventListener("input", debounce(async (e) => {
        const query = e.target.value.trim();
        
        // Show gene suggestions if it looks like a gene name
        if (query.length >= 2 && !query.includes(' ')) {
            clearTimeout(suggestionTimeout);
            suggestionTimeout = setTimeout(() => {
                showGeneSuggestions(query);
            }, 150);
        } else {
            hideAutocomplete();
        }
        
        // Always perform the main search
        await populateAll();
    }, 300));
    
    // Keyboard navigation for autocomplete
    searchInput.addEventListener('keydown', (e) => {
        if (autocompleteDiv.classList.contains('hidden')) return;
        
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                selectedIndex = Math.min(selectedIndex + 1, currentSuggestions.length - 1);
                updateSelection();
                break;
            case 'ArrowUp':
                e.preventDefault();
                selectedIndex = Math.max(selectedIndex - 1, -1);
                updateSelection();
                break;
            case 'Enter':
                e.preventDefault();
                if (selectedIndex >= 0 && selectedIndex < currentSuggestions.length) {
                    searchInput.value = currentSuggestions[selectedIndex];
                    hideAutocomplete();
                    populateAll().catch(console.error);
                }
                break;
            case 'Escape':
                hideAutocomplete();
                break;
        }
    });
    
    // Hide autocomplete when clicking outside
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !autocompleteDiv.contains(e.target)) {
            hideAutocomplete();
        }
    });
}
