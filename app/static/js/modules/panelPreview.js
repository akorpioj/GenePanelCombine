/**
 * PanelMerge - Panel Preview Functionality
 * Provides quick panel summaries and gene counts on hover/click
 */

/**
 * Initialize panel preview functionality
 */
export function initializePanelPreview() {
    console.log('Initializing panel preview functionality');
    
    // Add event listeners for panel preview triggers immediately
    attachPanelPreviewListeners();
    
    // Also set up observer for dynamic content
    setupPanelObserver();
}

/**
 * Attach preview listeners to panel elements
 */
function attachPanelPreviewListeners() {
    // Listen for panel option hover events
    const panelSelects = document.querySelectorAll('select[id^="panel_id_"]');
    
    panelSelects.forEach(select => {
        // Skip if preview button already exists
        if (select.nextElementSibling && select.nextElementSibling.innerHTML && select.nextElementSibling.innerHTML.includes('Preview')) {
            return;
        }
        
        select.addEventListener('change', handlePanelSelection);
        
        // Add preview button next to each select
        addPreviewButton(select);
    });
}

/**
 * Setup observer to detect when panels are dynamically loaded
 */
function setupPanelObserver() {
    // Listen for custom panelsUpdated events
    document.addEventListener('panelsUpdated', (event) => {
        const select = event.target;
        if (select && select.id && select.id.startsWith('panel_id_')) {
            // Check if preview button already exists
            if (!select.nextElementSibling || !select.nextElementSibling.innerHTML.includes('Preview')) {
                addPreviewButton(select);
            }
        }
    });
}

/**
 * Add preview button next to panel select
 */
function addPreviewButton(selectElement) {
    // Only add button if select has actual panel options (more than just "None")
    const hasRealPanels = Array.from(selectElement.options).some(opt => 
        opt.value !== "None" && opt.value !== "Loading" && opt.value !== ""
    );
    
    if (!hasRealPanels) {
        return;
    }
    
    const previewBtn = document.createElement('button');
    previewBtn.type = 'button';
    previewBtn.className = 'ml-2 px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded hover:bg-blue-200 transition-colors';
    previewBtn.innerHTML = '👁️ Preview';
    previewBtn.title = 'Quick panel preview';
    previewBtn.style.display = 'inline-block'; // Always visible when panels are available
    
    previewBtn.addEventListener('click', (e) => {
        e.preventDefault();
        const selectedValue = selectElement.value;
        if (selectedValue && selectedValue !== 'None') {
            showPanelPreview(selectedValue, previewBtn, selectElement);
        } else {
            // If no panel selected, show dropdown to choose which panel to preview
            showPanelSelectionForPreview(selectElement, previewBtn);
        }
    });
    
    // Insert after the select element
    selectElement.parentNode.insertBefore(previewBtn, selectElement.nextSibling);
}

/**
 * Handle panel selection change - no longer needed to hide/show preview button
 */
function handlePanelSelection(event) {
    // Preview button is always visible when panels are available
    // No need to hide/show based on selection
}

/**
 * Show panel selection dropdown for preview when no panel is currently selected
 */
function showPanelSelectionForPreview(selectElement, triggerElement) {
    // Get all available panel options from the select element
    const options = Array.from(selectElement.options).filter(opt => 
        opt.value !== "None" && opt.value !== "Loading" && opt.value !== ""
    );
    
    if (options.length === 0) {
        showNotification('No panels available for preview', 'error');
        return;
    }
    
    // Create a simple dropdown modal to select which panel to preview
    const modalBackdrop = document.createElement('div');
    modalBackdrop.id = 'panel-selection-modal';
    modalBackdrop.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    
    const modalContent = document.createElement('div');
    modalContent.className = 'bg-white rounded-lg max-w-md w-full mx-4 p-6 max-h-[80vh] flex flex-col';
    
    modalContent.innerHTML = `
        <div class="mb-4 flex-shrink-0">
            <h3 class="text-lg font-semibold text-gray-900">Select Panel to Preview</h3>
            <p class="text-sm text-gray-600 mt-1">Choose which panel you'd like to preview:</p>
        </div>
        
        <div class="flex-1 overflow-y-auto min-h-0 mb-4" style="max-height: 300px;">
            <div class="space-y-2">
                ${options.map(option => `
                    <button 
                        class="w-full text-left p-3 rounded border hover:bg-blue-50 hover:border-blue-300 transition-colors block"
                        data-panel-value="${option.value}"
                    >
                        <div class="font-medium text-gray-900">${option.textContent}</div>
                        <div class="text-xs text-gray-500">${option.value}</div>
                    </button>
                `).join('')}
            </div>
        </div>
        
        <div class="flex justify-end flex-shrink-0">
            <button id="cancel-selection" class="px-4 py-2 text-gray-600 border border-gray-300 rounded hover:bg-gray-50">
                Cancel
            </button>
        </div>
    `;
    
    modalBackdrop.appendChild(modalContent);
    document.body.appendChild(modalBackdrop);
    
    // Add event listeners
    const panelButtons = modalContent.querySelectorAll('[data-panel-value]');
    panelButtons.forEach(button => {
        button.addEventListener('click', async () => {
            const panelValue = button.dataset.panelValue;
            modalBackdrop.remove();
            
            // Show preview for selected panel
            await showPanelPreview(panelValue, triggerElement, selectElement);
        });
    });
    
    // Close handlers
    const closeHandler = () => modalBackdrop.remove();
    modalContent.querySelector('#cancel-selection').addEventListener('click', closeHandler);
    
    modalBackdrop.addEventListener('click', (e) => {
        if (e.target === modalBackdrop) {
            closeHandler();
        }
    });
    
    // Escape key to close
    const escapeHandler = (e) => {
        if (e.key === 'Escape') {
            closeHandler();
            document.removeEventListener('keydown', escapeHandler);
        }
    };
    document.addEventListener('keydown', escapeHandler);
}

/**
 * Show panel preview modal or tooltip
 */
async function showPanelPreview(panelIdStr, triggerElement, selectElement = null) {
    if (!panelIdStr || panelIdStr === 'None') return;
    
    const [panelId, apiSource] = panelIdStr.split('-');
    
    // Store original text outside try block
    const originalText = triggerElement.innerHTML;
    
    try {
        // Show loading state
        triggerElement.innerHTML = '⏳ Loading...';
        triggerElement.disabled = true;
        
        // Fetch preview data
        const response = await fetch(`/api/panel-preview/${panelId}?source=${apiSource}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const previewData = await response.json();
        
        // Create and show preview modal with context about which select element it came from
        createPreviewModal(previewData, selectElement);
        
    } catch (error) {
        console.error('Error fetching panel preview:', error);
        showPreviewError('Failed to load panel preview. Please try again.');
    } finally {
        // Restore button state
        triggerElement.innerHTML = originalText;
        triggerElement.disabled = false;
    }
}

/**
 * Create and display preview modal
 */
function createPreviewModal(previewData, selectElement = null) {
    // Remove any existing preview modal
    const existingModal = document.getElementById('panel-preview-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Determine if this panel is currently selected in the given select element
    const currentValue = selectElement ? selectElement.value : null;
    const isCurrentlySelected = currentValue === `${previewData.id}-${previewData.api_source}`;
    
    // Create modal backdrop
    const modalBackdrop = document.createElement('div');
    modalBackdrop.id = 'panel-preview-modal';
    modalBackdrop.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    
    // Create modal content
    const modalContent = document.createElement('div');
    modalContent.className = 'bg-white rounded-lg max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto';
    
    // Modal HTML content
    modalContent.innerHTML = `
        <div class="p-6">
            <!-- Header -->
            <div class="flex justify-between items-start mb-4">
                <div>
                    <h2 class="text-xl font-bold text-gray-900">${previewData.display_name}</h2>
                    <p class="text-sm text-gray-600">Version ${previewData.version} • ${previewData.source_name}</p>
                    ${isCurrentlySelected ? '<p class="text-sm text-green-600 font-medium">✓ Currently selected</p>' : ''}
                </div>
                <button id="close-preview" class="text-gray-400 hover:text-gray-600 text-2xl">&times;</button>
            </div>
            
            <!-- Quick Stats -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div class="text-center p-3 bg-blue-50 rounded">
                    <div class="text-2xl font-bold text-blue-600">${previewData.gene_count}</div>
                    <div class="text-sm text-gray-600">Total Genes</div>
                </div>
                ${previewData.confidence_stats.green ? `
                <div class="text-center p-3 bg-green-50 rounded">
                    <div class="text-2xl font-bold text-green-600">${previewData.confidence_stats.green}</div>
                    <div class="text-sm text-gray-600">High Confidence</div>
                </div>
                ` : ''}
                ${previewData.confidence_stats.amber ? `
                <div class="text-center p-3 bg-yellow-50 rounded">
                    <div class="text-2xl font-bold text-yellow-600">${previewData.confidence_stats.amber}</div>
                    <div class="text-sm text-gray-600">Medium Confidence</div>
                </div>
                ` : ''}
                ${previewData.confidence_stats.red ? `
                <div class="text-center p-3 bg-red-50 rounded">
                    <div class="text-2xl font-bold text-red-600">${previewData.confidence_stats.red}</div>
                    <div class="text-sm text-gray-600">Low Confidence</div>
                </div>
                ` : ''}
            </div>
            
            <!-- Panel Information -->
            <div class="space-y-4 mb-6">
                <div>
                    <h3 class="font-semibold text-gray-900 mb-2">Description</h3>
                    <p class="text-gray-700 text-sm">${previewData.description || 'No description available'}</p>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <h4 class="font-medium text-gray-900 mb-1">Disease Group</h4>
                        <p class="text-gray-600 text-sm">${previewData.disease_group || 'N/A'}</p>
                    </div>
                    <div>
                        <h4 class="font-medium text-gray-900 mb-1">Disease Sub-group</h4>
                        <p class="text-gray-600 text-sm">${previewData.disease_sub_group || 'N/A'}</p>
                    </div>
                </div>
            </div>
            
            <!-- Sample Genes -->
            ${previewData.all_genes && previewData.all_genes.length > 0 ? `
            <div class="mb-6">
                <h3 class="font-semibold text-gray-900 mb-3">All Genes (${previewData.all_genes.length})</h3>
                <div class="max-h-60 overflow-y-auto border rounded p-3">
                    <div class="grid gap-2">
                        ${previewData.all_genes.map(gene => {
                            const confidenceClass = 
                                gene.confidence === '3' ? 'bg-green-100 text-green-800 border-green-200' :
                                gene.confidence === '2' ? 'bg-yellow-100 text-yellow-800 border-yellow-200' :
                                gene.confidence === '1' ? 'bg-red-100 text-red-800 border-red-200' :
                                'bg-gray-100 text-gray-800 border-gray-200';
                            
                            const confidenceLabel = 
                                gene.confidence === '3' ? 'High' :
                                gene.confidence === '2' ? 'Medium' :
                                gene.confidence === '1' ? 'Low' :
                                'Unknown';
                                
                            return `
                                <div class="flex items-center justify-between p-2 border rounded ${confidenceClass}">
                                    <div class="flex-1">
                                        <span class="font-medium">${gene.symbol}</span>
                                        <span class="ml-2 text-xs px-2 py-1 rounded bg-white bg-opacity-50">${confidenceLabel}</span>
                                    </div>
                                    <div class="text-xs text-right max-w-xs">
                                        ${gene.moi !== 'N/A' ? `<div>MOI: ${gene.moi}</div>` : ''}
                                        ${gene.phenotype !== 'N/A' && gene.phenotype.length > 3 ? `<div class="truncate" title="${gene.phenotype}">Phenotype: ${gene.phenotype}</div>` : ''}
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            </div>
            ` : ''}
            
            <!-- Actions -->
            <div class="flex justify-end space-x-3">
                <button id="close-preview-btn" class="px-4 py-2 text-gray-600 border border-gray-300 rounded hover:bg-gray-50">
                    Close
                </button>
                ${selectElement && !isCurrentlySelected ? `
                <button id="replace-panel-btn" class="px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700" data-panel-id="${previewData.id}" data-api-source="${previewData.api_source}">
                    Select as Current Panel
                </button>
                ` : ''}
            </div>
        </div>
    `;
    
    modalBackdrop.appendChild(modalContent);
    document.body.appendChild(modalBackdrop);
    
    // Add event listeners
    setupModalEventListeners(modalBackdrop, previewData, selectElement);
}

/**
 * Setup event listeners for preview modal
 */
function setupModalEventListeners(modal, previewData, selectElement = null) {
    const closeButtons = modal.querySelectorAll('#close-preview, #close-preview-btn');
    const replaceButton = modal.querySelector('#replace-panel-btn');
    
    // Close modal handlers
    closeButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            modal.remove();
        });
    });
    
    // Close on backdrop click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
    
    // Close on Escape key
    const escapeHandler = (e) => {
        if (e.key === 'Escape') {
            modal.remove();
            document.removeEventListener('keydown', escapeHandler);
        }
    };
    document.addEventListener('keydown', escapeHandler);
    
    // Replace panel handler
    if (replaceButton && selectElement) {
        replaceButton.addEventListener('click', () => {
            replacePanelFromPreview(previewData, selectElement);
            modal.remove();
        });
    }
}

/**
 * Replace current panel with the previewed panel
 */
function replacePanelFromPreview(previewData, selectElement) {
    const panelValue = `${previewData.id}-${previewData.api_source}`;
    
    // Check if this panel value exists in the select options
    const option = selectElement.querySelector(`option[value="${panelValue}"]`);
    if (option) {
        // Set the new value
        selectElement.value = panelValue;
        
        // Trigger change event to update UI
        selectElement.dispatchEvent(new Event('change', { bubbles: true }));
        
        // Show success message
        showNotification(`Panel replaced with ${previewData.display_name}`, 'success');
    } else {
        showNotification('Panel not available in current dropdown', 'error');
    }
}

/**
 * Select panel from preview modal (legacy function for backwards compatibility)
 */
function selectPanelFromPreview(previewData) {
    const panelValue = `${previewData.id}-${previewData.api_source}`;
    
    // Find the first available panel select dropdown
    const panelSelects = document.querySelectorAll('select[id^="panel_id_"]');
    
    for (const select of panelSelects) {
        if (select.value === 'None' || select.value === '') {
            select.value = panelValue;
            
            // Trigger change event to update UI
            select.dispatchEvent(new Event('change', { bubbles: true }));
            
            // Show success message
            showPreviewSuccess(`Panel "${previewData.name}" has been selected!`);
            return;
        }
    }
    
    // If no empty slots, show message
    showPreviewError('All panel slots are filled. Please remove a panel first.');
}

/**
 * Show preview error message
 */
function showPreviewError(message) {
    showPreviewMessage(message, 'error');
}

/**
 * Show preview success message
 */
function showPreviewSuccess(message) {
    showPreviewMessage(message, 'success');
}

/**
 * Show preview message (success or error)
 */
function showPreviewMessage(message, type) {
    // Remove any existing messages
    const existingMessage = document.getElementById('preview-message');
    if (existingMessage) {
        existingMessage.remove();
    }
    
    // Create message element
    const messageDiv = document.createElement('div');
    messageDiv.id = 'preview-message';
    messageDiv.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-sm ${
        type === 'success' ? 'bg-green-100 text-green-800 border border-green-200' : 
        'bg-red-100 text-red-800 border border-red-200'
    }`;
    
    messageDiv.innerHTML = `
        <div class="flex items-center justify-between">
            <span class="text-sm font-medium">${message}</span>
            <button class="ml-3 text-lg">&times;</button>
        </div>
    `;
    
    document.body.appendChild(messageDiv);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        if (messageDiv.parentNode) {
            messageDiv.remove();
        }
    }, 3000);
    
    // Click to close
    messageDiv.querySelector('button').addEventListener('click', () => {
        messageDiv.remove();
    });
}

/**
 * Show notification to user
 */
function showNotification(message, type = 'info') {
    // Remove any existing notifications
    const existingNotification = document.getElementById('panel-notification');
    if (existingNotification) {
        existingNotification.remove();
    }
    
    // Create notification
    const notification = document.createElement('div');
    notification.id = 'panel-notification';
    notification.className = `fixed top-4 right-4 z-50 px-4 py-2 rounded shadow-lg ${
        type === 'success' ? 'bg-green-600 text-white' :
        type === 'error' ? 'bg-red-600 text-white' :
        'bg-blue-600 text-white'
    }`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 3000);
}

/**
 * Add preview tooltips to panel options (alternative to modal)
 */
export function addPanelPreviewTooltips() {
    const panelSelects = document.querySelectorAll('select[id^="panel_id_"]');
    
    panelSelects.forEach(select => {
        select.addEventListener('mouseover', (e) => {
            if (e.target.tagName === 'OPTION' && e.target.value !== 'None') {
                // Could implement tooltip preview here for quick info
                console.log('Hovering over panel option:', e.target.value);
            }
        });
    });
}

export default {
    initializePanelPreview,
    addPanelPreviewTooltips
};
