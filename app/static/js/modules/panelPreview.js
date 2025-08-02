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
    modalBackdrop.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
    
    const modalContent = document.createElement('div');
    modalContent.className = 'bg-white rounded-lg w-full max-w-2xl h-full max-h-[85vh] overflow-hidden flex flex-col shadow-xl';
    
    modalContent.innerHTML = `
        <div class="flex-shrink-0 p-4 border-b bg-white">
            <div class="flex justify-between items-start">
                <div>
                    <h3 class="text-lg font-semibold text-gray-900">Select Panel to Preview</h3>
                    <p class="text-sm text-gray-600 mt-1">Choose from ${options.length} available panels:</p>
                </div>
                <button id="cancel-selection-x" class="text-gray-400 hover:text-gray-600 text-xl ml-4">&times;</button>
            </div>
        </div>
        
        <div class="flex-1 overflow-y-auto min-h-0 p-4">
            <div class="grid gap-2 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
                ${options.map(option => {
                    // Extract panel info from the option text and value
                    const panelText = option.textContent.trim();
                    const panelValue = option.value;
                    const [panelId, apiSource] = panelValue.split('-');
                    
                    // Try to extract version and source info if available in the text
                    const versionMatch = panelText.match(/v([\d.]+)/);
                    const version = versionMatch ? versionMatch[1] : '';
                    
                    return `
                        <button 
                            class="text-left p-3 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-all duration-200 transform hover:scale-[1.02] focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 group"
                            data-panel-value="${option.value}"
                        >
                            <div class="space-y-1">
                                <div class="font-medium text-gray-900 text-sm leading-tight group-hover:text-blue-700 transition-colors">
                                    ${panelText}
                                </div>
                                <div class="text-xs text-gray-500 font-mono bg-gray-50 px-2 py-1 rounded">
                                    ${panelValue}
                                </div>
                                ${version ? `
                                <div class="text-xs text-blue-600 font-medium">
                                    v${version}
                                </div>
                                ` : ''}
                                <div class="text-xs text-gray-400 uppercase tracking-wide">
                                    ${apiSource === 'panelapp' ? 'PanelApp' : apiSource === 'genomics_england' ? 'Genomics England' : apiSource}
                                </div>
                            </div>
                        </button>
                    `;
                }).join('')}
            </div>
        </div>
        
        <div class="flex justify-between items-center p-4 border-t bg-gray-50 flex-shrink-0">
            <div class="text-sm text-gray-600">
                Click any panel to view its details
            </div>
            <button id="cancel-selection" class="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-white transition-colors">
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
    const closeXButton = modalContent.querySelector('#cancel-selection-x');
    if (closeXButton) {
        closeXButton.addEventListener('click', closeHandler);
    }
    
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
    modalBackdrop.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
    
    // Create modal content
    const modalContent = document.createElement('div');
    modalContent.className = 'bg-white rounded-lg w-full max-w-4xl h-full max-h-[90vh] overflow-hidden flex flex-col shadow-xl';
    
    // Modal HTML content - restructured for better space usage
    modalContent.innerHTML = `
        <div class="flex flex-col h-full">
            <!-- Header - compact and fixed -->
            <div class="flex justify-between items-start p-3 border-b flex-shrink-0 bg-white">
                <div class="flex-1 min-w-0">
                    <h2 class="text-base font-bold text-gray-900 truncate">${previewData.display_name}</h2>
                    <div class="flex items-center gap-3 text-xs text-gray-600 mt-1 flex-wrap">
                        <span>v${previewData.version}</span>
                        <span>•</span>
                        <span>${previewData.source_name}</span>
                        <span>•</span>
                        <span class="font-medium text-blue-600">${previewData.gene_count} genes</span>
                        ${isCurrentlySelected ? '<span class="text-green-600 font-medium">✓ Selected</span>' : ''}
                    </div>
                </div>
                <button id="close-preview" class="text-gray-400 hover:text-gray-600 text-xl ml-2 flex-shrink-0">&times;</button>
            </div>
            
            <!-- Compact Stats Bar - fixed -->
            <div class="px-3 py-2 bg-gray-50 border-b flex-shrink-0">
                <div class="flex items-center justify-center gap-4 text-xs flex-wrap">
                    ${previewData.confidence_stats.green ? `
                    <div class="flex items-center gap-1 bg-green-100 px-2 py-1 rounded">
                        <div class="w-2 h-2 bg-green-500 rounded-full"></div>
                        <span class="font-medium text-green-800">${previewData.confidence_stats.green}</span>
                        <span class="text-green-700">High</span>
                    </div>
                    ` : ''}
                    ${previewData.confidence_stats.amber ? `
                    <div class="flex items-center gap-1 bg-yellow-100 px-2 py-1 rounded">
                        <div class="w-2 h-2 bg-yellow-500 rounded-full"></div>
                        <span class="font-medium text-yellow-800">${previewData.confidence_stats.amber}</span>
                        <span class="text-yellow-700">Med</span>
                    </div>
                    ` : ''}
                    ${previewData.confidence_stats.red ? `
                    <div class="flex items-center gap-1 bg-red-100 px-2 py-1 rounded">
                        <div class="w-2 h-2 bg-red-500 rounded-full"></div>
                        <span class="font-medium text-red-800">${previewData.confidence_stats.red}</span>
                        <span class="text-red-700">Low</span>
                    </div>
                    ` : ''}
                    ${previewData.disease_group && previewData.disease_group !== 'N/A' ? `
                    <div class="text-gray-600 bg-gray-100 px-2 py-1 rounded">
                        <span>Disease: </span><span class="font-medium">${previewData.disease_group}</span>
                    </div>
                    ` : ''}
                </div>
            </div>
            
            <!-- Scrollable Content Area -->
            <div class="flex-1 overflow-y-auto min-h-0">
                <!-- Description - collapsible if available -->
                ${previewData.description && previewData.description !== 'No description available' ? `
                <div class="px-3 py-2 border-b">
                    <details class="text-xs">
                        <summary class="cursor-pointer font-medium text-gray-700 hover:text-gray-900 py-1">
                            Description
                        </summary>
                        <p class="mt-1 text-gray-600 text-xs leading-relaxed pl-2">${previewData.description}</p>
                    </details>
                </div>
                ` : ''}
                
                <!-- Gene List -->
                ${previewData.all_genes && previewData.all_genes.length > 0 ? `
                <div class="p-3">
                    <h3 class="font-semibold text-gray-900 text-sm mb-2 sticky top-0 bg-white">All Genes (${previewData.all_genes.length})</h3>
                    <div class="space-y-1">
                        ${previewData.all_genes.map(gene => {
                            const confidenceClass = 
                                gene.confidence === '3' ? 'bg-green-50 text-green-800 border-green-200' :
                                gene.confidence === '2' ? 'bg-yellow-50 text-yellow-800 border-yellow-200' :
                                gene.confidence === '1' ? 'bg-red-50 text-red-800 border-red-200' :
                                'bg-gray-50 text-gray-800 border-gray-200';
                            
                            const confidenceLabel = 
                                gene.confidence === '3' ? 'H' :
                                gene.confidence === '2' ? 'M' :
                                gene.confidence === '1' ? 'L' :
                                '?';
                                
                            return `
                                <div class="flex items-center justify-between p-2 border rounded ${confidenceClass} hover:shadow-sm transition-shadow">
                                    <div class="flex items-center gap-2 flex-1 min-w-0">
                                        <span class="font-mono font-bold text-sm">${gene.symbol}</span>
                                        <span class="text-xs px-1 py-0.5 rounded bg-white bg-opacity-70 font-medium" title="${gene.confidence === '3' ? 'High Confidence' : gene.confidence === '2' ? 'Medium Confidence' : gene.confidence === '1' ? 'Low Confidence' : 'Unknown Confidence'}">${confidenceLabel}</span>
                                        ${gene.moi !== 'N/A' && gene.moi ? `<span class="text-xs text-gray-600 bg-white bg-opacity-50 px-1 py-0.5 rounded">${gene.moi}</span>` : ''}
                                    </div>
                                    <!-- gene.phenotype can be a string or a list of strings -->
                                    <div class="flex items-center gap-2 flex-1 min-w-0">
                                        ${gene.phenotype !== 'N/A' && gene.phenotype && gene.phenotype.length > 3 ? `
                                        <div class="text-xs text-gray-600 ml-2" title="${gene.phenotype}">
                                        ${gene.phenotype}
                                        </div>
                                        ` : ''}
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
                ` : `
                <div class="flex-1 flex items-center justify-center text-gray-500 p-8">
                    <div class="text-center">
                        <div class="text-2xl mb-2">📋</div>
                        <div>No gene information available</div>
                    </div>
                </div>
                `}
            </div>
            
            <!-- Footer Actions - fixed at bottom -->
            <div class="flex justify-end space-x-2 p-3 border-t flex-shrink-0 bg-white">
                <button id="close-preview-btn" class="px-3 py-1.5 text-xs text-gray-600 border border-gray-300 rounded hover:bg-gray-50">
                    Close
                </button>
                ${selectElement && !isCurrentlySelected ? `
                <button id="replace-panel-btn" class="px-3 py-1.5 text-xs bg-orange-600 text-white rounded hover:bg-orange-700" data-panel-id="${previewData.id}" data-api-source="${previewData.api_source}">
                    Select Panel
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
