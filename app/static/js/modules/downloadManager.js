/**
 * PanelMerge - Download Manager
 * Handles Excel file downloads with custom naming and folder selection
 */

/**
 * Check if File System Access API is supported
 * @returns {boolean} True if supported
 */
function isFileSystemAccessSupported() {
    return 'showSaveFilePicker' in window;
}

/**
 * Generate a default filename based on current selections
 * @returns {string} Default filename
 */
function generateDefaultFilename() {
    const searchTerm = document.getElementById('search_term_input')?.value?.trim();
    const selectedPanels = getSelectedPanelNames();
    
    let filename = 'filtered_gene_list';
    
    if (searchTerm) {
        // Clean search term for filename
        const cleanSearchTerm = searchTerm.replace(/[^a-zA-Z0-9]/g, '_');
        filename = `gene_list_${cleanSearchTerm}`;
    } else if (selectedPanels.length > 0) {
        // Use first panel name if no search term
        const cleanPanelName = selectedPanels[0].replace(/[^a-zA-Z0-9]/g, '_');
        filename = `gene_list_${cleanPanelName}`;
    }
    
    // Add timestamp for uniqueness
    const timestamp = new Date().toISOString().slice(0, 16).replace(/[:-]/g, '');
    filename += `_${timestamp}`;
    
    return `${filename}.xlsx`;
}

/**
 * Get selected panel names for filename generation
 * @returns {Array<string>} Array of panel names
 */
function getSelectedPanelNames() {
    const selectedPanels = [];
    // Import dynamically to avoid circular dependencies
    import('./state.js').then(({ getMaxPanels }) => {
        const maxPanels = getMaxPanels();
        for (let i = 1; i <= maxPanels; i++) {
            const select = document.getElementById(`panel_id_${i}`);
            if (select && select.value !== "None") {
                const panelName = select.options[select.selectedIndex].textContent;
                selectedPanels.push(panelName);
            }
        }
    });
    
    // Fallback: check up to 10 panels for immediate use
    for (let i = 1; i <= 10; i++) {
        const select = document.getElementById(`panel_id_${i}`);
        if (select && select.value !== "None") {
            const panelName = select.options[select.selectedIndex].textContent;
            selectedPanels.push(panelName);
        }
    }
    return selectedPanels;
}

/**
 * Show file naming modal
 * @param {string} defaultFilename Default filename
 * @returns {Promise<string|null>} Selected filename or null if cancelled
 */
function showFileNamingModal(defaultFilename) {
    return new Promise((resolve) => {
        // Create modal HTML
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                <h3 class="text-lg font-semibold text-gray-900 mb-4">Save Gene List</h3>
                <div class="mb-4">
                    <label for="filename-input" class="block text-sm font-medium text-gray-700 mb-2">
                        Filename:
                    </label>
                    <input 
                        type="text" 
                        id="filename-input" 
                        value="${defaultFilename.replace('.xlsx', '')}"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
                        placeholder="Enter filename"
                    />
                    <div class="mt-1 text-sm text-gray-500">.xlsx extension will be added automatically</div>
                </div>
                <div class="flex gap-3 justify-end">
                    <button 
                        type="button" 
                        id="cancel-download"
                        class="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-400"
                    >
                        Cancel
                    </button>
                    <button 
                        type="button" 
                        id="confirm-download"
                        class="px-4 py-2 bg-sky-600 text-white rounded-md hover:bg-sky-700 focus:outline-none focus:ring-2 focus:ring-sky-500"
                    >
                        Download
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        const filenameInput = modal.querySelector('#filename-input');
        const confirmBtn = modal.querySelector('#confirm-download');
        const cancelBtn = modal.querySelector('#cancel-download');
        
        // Focus and select the filename (without extension)
        filenameInput.focus();
        filenameInput.select();
        
        // Handle confirm
        const handleConfirm = () => {
            const filename = filenameInput.value.trim();
            if (filename) {
                document.body.removeChild(modal);
                resolve(filename.endsWith('.xlsx') ? filename : `${filename}.xlsx`);
            }
        };
        
        // Handle cancel
        const handleCancel = () => {
            document.body.removeChild(modal);
            resolve(null);
        };
        
        confirmBtn.addEventListener('click', handleConfirm);
        cancelBtn.addEventListener('click', handleCancel);
        
        // Handle enter key
        filenameInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                handleConfirm();
            } else if (e.key === 'Escape') {
                handleCancel();
            }
        });
        
        // Handle click outside modal
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                handleCancel();
            }
        });
    });
}

/**
 * Download file using traditional method (fallback)
 * @param {Blob} blob File blob
 * @param {string} filename Filename
 */
function downloadWithTraditionalMethod(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.style.display = 'none';
    
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    
    // Clean up the URL object
    setTimeout(() => URL.revokeObjectURL(url), 100);
}

/**
 * Submit form data and get Excel file blob
 * @param {FormData} formData Form data to submit
 * @returns {Promise<Blob>} Excel file blob
 */
async function submitFormAndGetBlob(formData) {
    const response = await fetch('/generate', {
        method: 'POST',
        body: formData
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('text/html')) {
        // If we get HTML back, it means there was an error and we got redirected
        throw new Error('Server returned an error. Please check your selections and try again.');
    }
    
    return await response.blob();
}

/**
 * Enhanced download function that handles custom naming and folder selection
 * @param {Event} event Form submit event
 */
export async function handleEnhancedDownload(event) {
    event.preventDefault();
    
    const form = event.target;
    const submitButton = form.querySelector('button[type="submit"]');
    const originalButtonText = submitButton.textContent;
    
    try {
        // Get default filename
        const defaultFilename = generateDefaultFilename();
        
        let fileHandle = null;
        let useFileSystemAPI = false;
        
        // Try to get file handle IMMEDIATELY while we have user gesture
        if (isFileSystemAccessSupported()) {
            console.log('File System Access API is supported, trying to get file handle');
            try {
                fileHandle = await window.showSaveFilePicker({
                    suggestedName: defaultFilename,
                    types: [{
                        description: 'Excel files',
                        accept: {
                            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx']
                        }
                    }]
                });
                useFileSystemAPI = true;
                console.log('File handle obtained successfully');
            } catch (error) {
                if (error.name === 'AbortError') {
                    console.log('User cancelled File System Access API save dialog');
                    // User cancelled, we'll exit
                    return;
                } else {
                    console.log('File System Access API failed:', error.message);
                    // API failed, we'll fall back to modal approach after generating the file
                }
            }
        }
        
        // Show loading state
        submitButton.disabled = true;
        submitButton.textContent = '⏳ Generating...';
        
        // Submit form and get blob
        const formData = new FormData(form);
        const blob = await submitFormAndGetBlob(formData);
        
        // Update button text
        submitButton.textContent = '⬇️ Downloading...';
        
        let selectedFilename = defaultFilename;
        let downloadSuccess = false;
        
        // If we have a file handle, use it
        if (useFileSystemAPI && fileHandle) {
            try {
                const writable = await fileHandle.createWritable();
                await writable.write(blob);
                await writable.close();
                
                selectedFilename = fileHandle.name || defaultFilename;
                downloadSuccess = true;
                console.log('File saved successfully with File System Access API');
            } catch (error) {
                console.log('Failed to write file with File System Access API:', error.message);
                // Fall back to modal approach
            }
        }
        
        // If File System Access API didn't work or isn't supported, use modal approach
        if (!downloadSuccess) {
            console.log('Falling back to modal filename selection');
            selectedFilename = await showFileNamingModal(defaultFilename);
            if (!selectedFilename) {
                // User cancelled the modal
                return;
            }
            
            // Use traditional download method
            downloadWithTraditionalMethod(blob, selectedFilename);
            downloadSuccess = true;
        }
        
        // Show success message if download was successful
        if (downloadSuccess) {
            const successMsg = document.createElement('div');
            successMsg.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-md shadow-lg z-50';
            successMsg.textContent = `✅ File downloaded: ${selectedFilename}`;
            document.body.appendChild(successMsg);
            
            setTimeout(() => {
                if (document.body.contains(successMsg)) {
                    document.body.removeChild(successMsg);
                }
            }, 3000);
        }
        
    } catch (error) {
        console.error('Download error:', error);
        
        // Show error message
        const errorMsg = document.createElement('div');
        errorMsg.className = 'fixed top-4 right-4 bg-red-500 text-white px-4 py-2 rounded-md shadow-lg z-50';
        errorMsg.textContent = `❌ Download failed: ${error.message}`;
        document.body.appendChild(errorMsg);
        
        setTimeout(() => {
            if (document.body.contains(errorMsg)) {
                document.body.removeChild(errorMsg);
            }
        }, 5000);
        
    } finally {
        // Restore button state
        submitButton.disabled = false;
        submitButton.textContent = originalButtonText;
    }
}

/**
 * Initialize enhanced download functionality
 */
export function initializeEnhancedDownload() {
    const generateForm = document.getElementById('generateForm');
    if (generateForm) {
        generateForm.addEventListener('submit', handleEnhancedDownload);
    }
}
