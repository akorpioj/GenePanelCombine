/**
 * PanelMerge - Panel Comparison Functionality
 * Handles side-by-side panel comparison and modal interface
 */

import { fetchPanelDetails } from './api.js';
import { getSelectedPanels } from './panelManager.js';

/**
 * Open panel comparison modal
 */
export function openPanelComparison() {
    const selectedPanels = getSelectedPanels();
    
    if (selectedPanels.length < 2) {
        alert('Please select at least 2 panels to compare.');
        return;
    }
    
    if (selectedPanels.length > 4) {
        alert('You can compare up to 4 panels at a time.');
        return;
    }
    
    createComparisonModal(selectedPanels);
}

/**
 * Create and display comparison modal
 * @param {Array} selectedPanels - Array of selected panels
 */
function createComparisonModal(selectedPanels) {
    // Remove existing modal if present
    const existingModal = document.getElementById('comparison-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Create modal overlay
    const modalOverlay = document.createElement('div');
    modalOverlay.id = 'comparison-modal';
    modalOverlay.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4';
    modalOverlay.onclick = (e) => {
        if (e.target === modalOverlay) closePanelComparison();
    };
    
    // Create modal content
    const modalContent = document.createElement('div');
    modalContent.className = 'bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col';
    
    // Modal header
    const modalHeader = document.createElement('div');
    modalHeader.className = 'flex justify-between items-center p-4 border-b border-gray-200 flex-shrink-0';
    modalHeader.innerHTML = `
        <h2 class="text-xl font-semibold text-gray-900">Panel Comparison</h2>
        <button onclick="closePanelComparison()" class="text-gray-400 hover:text-gray-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
        </button>
    `;
    
    // Modal body with loading state
    const modalBody = document.createElement('div');
    modalBody.className = 'flex-1 overflow-y-auto p-4';
    modalBody.innerHTML = `
        <div class="flex justify-center items-center h-32">
            <div class="text-center">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-600 mx-auto"></div>
                <span class="mt-2 text-gray-600 block">Loading panel details...</span>
            </div>
        </div>
    `;
    
    modalContent.appendChild(modalHeader);
    modalContent.appendChild(modalBody);
    modalOverlay.appendChild(modalContent);
    document.body.appendChild(modalOverlay);
    
    // Fetch and display panel details
    fetchPanelDetailsForComparison(selectedPanels, modalBody);
}

/**
 * Fetch detailed panel information for comparison
 * @param {Array} selectedPanels - Selected panels
 * @param {HTMLElement} modalBody - Modal body element to update
 */
async function fetchPanelDetailsForComparison(selectedPanels, modalBody) {
    try {
        const panelIds = selectedPanels.map(p => p.id).join(',');
        const panelDetails = await fetchPanelDetails(panelIds);
        displayPanelComparison(panelDetails, modalBody);
        
    } catch (error) {
        console.error('Error fetching panel details:', error);
        modalBody.innerHTML = `
            <div class="text-center text-red-600">
                <svg class="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <h3 class="text-lg font-semibold mb-2">Error Loading Panel Details</h3>
                <p class="text-gray-600">${error.message}</p>
                <button onclick="closePanelComparison()" class="mt-4 px-4 py-2 bg-sky-600 text-white rounded hover:bg-sky-700">
                    Close
                </button>
            </div>
        `;
    }
}

/**
 * Display panel comparison in modal
 * @param {Array} panelDetails - Panel details from API
 * @param {HTMLElement} modalBody - Modal body element
 */
function displayPanelComparison(panelDetails, modalBody) {
    if (!panelDetails || panelDetails.length === 0) {
        modalBody.innerHTML = `
            <div class="text-center text-gray-600">
                <p>No panel details found for comparison.</p>
                <button onclick="closePanelComparison()" class="mt-4 px-4 py-2 bg-sky-600 text-white rounded hover:bg-sky-700">
                    Close
                </button>
            </div>
        `;
        return;
    }
    
    // Create responsive comparison grid - side by side layout
    const gridCols = panelDetails.length === 2 ? 'grid-cols-2' : 
                     panelDetails.length === 3 ? 'grid-cols-3' : 'grid-cols-2';
    
    modalBody.innerHTML = `
        <div class="grid ${gridCols} gap-4 mb-4">
            ${panelDetails.map(panel => createPanelCard(panel)).join('')}
        </div>
        
        <div class="border-t border-gray-200 pt-3">
            <h3 class="text-base font-semibold text-gray-900 mb-2">Comparison Summary</h3>
            ${createComparisonSummary(panelDetails)}
        </div>
        
        <div class="flex justify-end gap-3 mt-3">
            <button onclick="closePanelComparison()" class="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600">
                Close
            </button>
            <button onclick="proceedWithSelection()" class="px-4 py-2 bg-sky-600 text-white rounded hover:bg-sky-700">
                Proceed with Selection
            </button>
        </div>
    `;
}

/**
 * Create individual panel card for comparison
 * @param {Object} panel - Panel data object
 * @returns {string} HTML string for panel card
 */
function createPanelCard(panel) {
    const geneDisplay = panel.all_genes && panel.all_genes.length > 0 ? 
        createGeneDisplay(panel.all_genes) : 
        '<p class="text-gray-500 text-xs">No genes available</p>';
        
    return `
        <div class="border border-gray-200 rounded-lg p-4 bg-gray-50 min-h-[500px] max-h-[700px] overflow-hidden flex flex-col">
            <div class="mb-3 flex-shrink-0">
                <h4 class="font-semibold text-lg text-gray-900 mb-1">${panel.display_name}</h4>
                <p class="text-sm text-gray-500">Version ${panel.version} • ID: ${panel.id}</p>
            </div>
            
            <div class="space-y-3 text-sm flex-shrink-0">
                <div>
                    <span class="font-medium text-gray-700">Gene Count:</span>
                    <span class="ml-2 px-2 py-1 bg-sky-100 text-sky-800 rounded text-xs font-medium">
                        ${panel.gene_count}
                    </span>
                </div>
                
                <div>
                    <span class="font-medium text-gray-700">Disease Group:</span>
                    <p class="text-gray-600 mt-1 text-xs">${panel.disease_group}</p>
                </div>
                
                ${panel.disease_sub_group !== 'N/A' ? `
                <div>
                    <span class="font-medium text-gray-700">Sub-group:</span>
                    <p class="text-gray-600 mt-1 text-xs">${panel.disease_sub_group}</p>
                </div>
                ` : ''}
                
                <div>
                    <span class="font-medium text-gray-700">Status:</span>
                    <span class="ml-2 px-2 py-1 ${panel.status === 'public' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'} rounded text-xs">
                        ${panel.status}
                    </span>
                </div>
                
                ${panel.description && panel.description !== 'No description available' ? `
                <div>
                    <details class="text-xs">
                        <summary class="cursor-pointer font-medium text-gray-700 hover:text-gray-900 py-1">
                            Description
                        </summary>
                        <p class="mt-1 text-gray-600 text-xs leading-relaxed pl-2">${panel.description}</p>
                    </details>
                </div>
                ` : ''}
            </div>
            
            <div class="mt-3 flex-1 min-h-0">
                <span class="font-medium text-gray-700 text-sm">All Genes (${panel.gene_count}):</span>
                <div class="mt-2 h-full">
                    ${geneDisplay}
                </div>
            </div>
        </div>
    `;
}

/**
 * Create gene display with scrollable container
 * @param {Array} genes - Array of gene names
 * @returns {string} HTML string for gene display
 */
function createGeneDisplay(genes) {
    if (!genes || genes.length === 0) {
        return '<p class="text-gray-500 text-xs">No genes available</p>';
    }
    
    const geneChips = genes.map(gene => 
        `<span class="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded mr-1 mb-1">${gene}</span>`
    ).join('');
    
    return `
        <div class="gene-display-container border border-gray-200 rounded p-2 bg-white h-full overflow-y-auto">
            <div class="flex flex-wrap">
                ${geneChips}
            </div>
        </div>
    `;
}

/**
 * Create comparison summary with statistics
 * @param {Array} panelDetails - Array of panel detail objects
 * @returns {string} HTML string for comparison summary
 */
function createComparisonSummary(panelDetails) {
    // Calculate unique genes across all panels
    const allGenes = new Set();
    panelDetails.forEach(panel => {
        if (panel.all_genes && Array.isArray(panel.all_genes)) {
            panel.all_genes.forEach(gene => allGenes.add(gene));
        }
    });
    const uniqueGenes = allGenes.size;
    
    const totalGenes = panelDetails.reduce((sum, panel) => sum + panel.gene_count, 0);
    const avgGenes = Math.round(totalGenes / panelDetails.length);
    const sources = [...new Set(panelDetails.map(p => p.api_source))];
    const diseaseGroups = [...new Set(panelDetails.map(p => p.disease_group))];
    
    return `
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-center mb-3">
            <div class="bg-blue-50 p-2 rounded">
                <div class="text-lg font-bold text-blue-600">${panelDetails.length}</div>
                <div class="text-xs text-gray-600">Panels</div>
            </div>
            <div class="bg-green-50 p-2 rounded">
                <div class="text-lg font-bold text-green-600">${uniqueGenes}</div>
                <div class="text-xs text-gray-600">Unique Genes</div>
            </div>
            <div class="bg-purple-50 p-2 rounded">
                <div class="text-lg font-bold text-purple-600">${avgGenes}</div>
                <div class="text-xs text-gray-600">Avg per Panel</div>
            </div>
            <div class="bg-orange-50 p-2 rounded">
                <div class="text-lg font-bold text-orange-600">${sources.length}</div>
                <div class="text-xs text-gray-600">Source${sources.length > 1 ? 's' : ''}</div>
            </div>
        </div>
        
        <div class="text-xs text-gray-600 space-y-1">
            <strong>Overlap:</strong> ${totalGenes - uniqueGenes} duplicate${totalGenes - uniqueGenes !== 1 ? 's' : ''}</p>
        </div>
    `;
}

/**
 * Close panel comparison modal
 */
export function closePanelComparison() {
    const modal = document.getElementById('comparison-modal');
    if (modal) {
        modal.remove();
    }
}

/**
 * Proceed with current panel selection after comparison
 */
export function proceedWithSelection() {
    closePanelComparison();
    document.getElementById('generate-btn-container').scrollIntoView({ behavior: 'smooth' });
}

// Make functions globally available for onclick handlers
window.closePanelComparison = closePanelComparison;
window.proceedWithSelection = proceedWithSelection;
