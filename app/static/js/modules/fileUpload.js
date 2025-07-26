/**
 * PanelMerge - File Upload Functionality
 * Handles drag-and-drop uploads and file management
 */

import { currentAPI } from './state.js';
import { uploadPanelFiles, removeUserPanel, fetchUploadedFiles } from './api.js';

/**
 * Validate files and show detailed preview
 * @param {Array} files - Array of files to validate
 */
async function validateFilesPreview(files) {
    const validationContainer = getOrCreateValidationContainer();
    validationContainer.innerHTML = '<div class="text-center"><div class="animate-spin rounded-full h-6 w-6 border-b-2 border-sky-600 mx-auto"></div><p class="text-sm text-gray-600 mt-2">Validating files...</p></div>';
    
    const validationResults = [];
    
    for (const file of files) {
        const result = await validateSingleFile(file);
        validationResults.push(result);
    }
    
    displayValidationResults(validationResults, validationContainer);
}

/**
 * Get or create validation results container
 * @returns {HTMLElement} Validation container element
 */
function getOrCreateValidationContainer() {
    let container = document.getElementById('file-validation-preview');
    if (!container) {
        container = document.createElement('div');
        container.id = 'file-validation-preview';
        container.className = 'mt-4 p-4 border border-gray-200 rounded-lg bg-gray-50';
        
        const uploadStatusDiv = document.getElementById('upload-panel-status');
        uploadStatusDiv.parentNode.insertBefore(container, uploadStatusDiv);
    }
    return container;
}

/**
 * Validate a single file and return detailed results
 * @param {File} file - File to validate
 * @returns {Promise<Object>} Validation result object
 */
async function validateSingleFile(file) {
    const result = {
        fileName: file.name,
        fileSize: file.size,
        fileType: file.type,
        isValid: true,
        warnings: [],
        errors: [],
        summary: {},
        preview: []
    };
    
    try {
        const content = await readFileContent(file);
        const ext = file.name.split('.').pop().toLowerCase();
        
        // File size validation
        const maxSize = 10 * 1024 * 1024; // 10MB
        if (file.size > maxSize) {
            result.errors.push(`File size (${formatFileSize(file.size)}) exceeds maximum allowed size (10MB)`);
            result.isValid = false;
        }
        
        // File type validation
        if (!['csv', 'tsv', 'txt', 'xlsx', 'xls'].includes(ext)) {
            result.errors.push(`Unsupported file type: .${ext}. Supported formats: CSV, TSV, TXT, XLSX, XLS`);
            result.isValid = false;
        }
        
        // Content validation for text files
        if (['csv', 'tsv', 'txt'].includes(ext) && content) {
            const textValidation = validateTextFileContent(content, ext);
            Object.assign(result, textValidation);
        }
        
        // Excel file validation (basic)
        if (['xlsx', 'xls'].includes(ext)) {
            result.warnings.push('Excel files will be processed server-side. Preview may be limited.');
            result.summary.format = 'Excel';
            result.summary.requiresServerProcessing = true;
        }
        
    } catch (error) {
        result.errors.push(`Failed to read file: ${error.message}`);
        result.isValid = false;
    }
    
    return result;
}

/**
 * Read file content as text
 * @param {File} file - File to read
 * @returns {Promise<string>} File content
 */
function readFileContent(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = (e) => reject(new Error('Failed to read file'));
        reader.readAsText(file);
    });
}

/**
 * Validate text file content (CSV/TSV/TXT)
 * @param {string} content - File content
 * @param {string} extension - File extension
 * @returns {Object} Validation result details
 */
function validateTextFileContent(content, extension) {
    const result = {
        warnings: [],
        errors: [],
        summary: {},
        preview: []
    };
    
    try {
        const lines = content.split(/\r?\n/).filter(line => line.trim());
        if (lines.length === 0) {
            result.errors.push('File appears to be empty');
            return result;
        }
        
        const delimiter = extension === 'tsv' ? '\t' : ',';
        result.summary.totalRows = lines.length;
        result.summary.format = extension.toUpperCase();
        
        // Parse header
        const header = lines[0].split(delimiter).map(h => h.trim());
        result.summary.columns = header.length;
        result.summary.columnNames = header;
        
        // Look for gene column
        const geneColumnIndex = findGeneColumn(header);
        result.summary.geneColumnIndex = geneColumnIndex;
        result.summary.geneColumnName = geneColumnIndex !== -1 ? header[geneColumnIndex] : null;
        
        if (geneColumnIndex === -1) {
            result.warnings.push('No recognized gene column found. Looking for: gene, genes, entity_name, genesymbol, symbol, gene_symbol');
        }
        
        // Parse data rows and extract genes
        const genes = new Set();
        const invalidRows = [];
        const sampleRows = [];
        
        for (let i = 1; i < Math.min(lines.length, 101); i++) { // Process first 100 rows for preview
            const row = lines[i].split(delimiter);
            
            if (row.length !== header.length) {
                invalidRows.push(i + 1);
                continue;
            }
            
            if (geneColumnIndex !== -1 && row[geneColumnIndex]) {
                const gene = row[geneColumnIndex].trim();
                if (gene) {
                    genes.add(gene);
                }
            }
            
            // Store first 5 rows for preview
            if (sampleRows.length < 5) {
                sampleRows.push(row);
            }
        }
        
        result.summary.uniqueGenes = genes.size;
        result.summary.geneList = Array.from(genes).slice(0, 20); // First 20 genes for preview
        result.preview = sampleRows;
        
        // Validation checks
        if (invalidRows.length > 0) {
            result.warnings.push(`${invalidRows.length} rows have incorrect number of columns (expected ${header.length})`);
        }
        
        if (genes.size === 0 && geneColumnIndex !== -1) {
            result.warnings.push('No valid genes found in the gene column');
        }
        
        if (lines.length > 10000) {
            result.warnings.push(`Large file with ${lines.length} rows. Processing may take longer.`);
        }
        
        // Gene symbol validation
        if (genes.size > 0) {
            validateGeneSymbols(Array.from(genes).slice(0, 50), result); // Validate first 50 genes
        }
        
    } catch (error) {
        result.errors.push(`Failed to parse file content: ${error.message}`);
    }
    
    return result;
}

/**
 * Find gene column in header
 * @param {Array} header - Column headers
 * @returns {number} Index of gene column or -1 if not found
 */
function findGeneColumn(header) {
    const geneColumnNames = ['gene', 'genes', 'entity_name', 'genesymbol', 'symbol', 'gene_symbol', 'hgnc_symbol'];
    return header.findIndex(h => {
        const colName = h.trim().toLowerCase();
        return geneColumnNames.includes(colName);
    });
}

/**
 * Validate gene symbols (basic validation)
 * @param {Array} genes - Array of gene symbols
 * @param {Object} result - Result object to update
 */
function validateGeneSymbols(genes, result) {
    const suspiciousGenes = [];
    const validPattern = /^[A-Z][A-Z0-9-]*$/; // Basic gene symbol pattern
    
    genes.forEach(gene => {
        if (!validPattern.test(gene)) {
            suspiciousGenes.push(gene);
        }
    });
    
    if (suspiciousGenes.length > 0) {
        result.warnings.push(`${suspiciousGenes.length} genes may have invalid symbols (e.g., ${suspiciousGenes.slice(0, 3).join(', ')})`);
    }
}

/**
 * Display validation results in the container
 * @param {Array} results - Array of validation results
 * @param {HTMLElement} container - Container element
 */
function displayValidationResults(results, container) {
    const html = `
        <div class="validation-results">
            <h3 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <svg class="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                File Validation Results
            </h3>
            ${results.map(result => createValidationResultCard(result)).join('')}
            <div class="mt-4 flex justify-end">
                ${results.every(r => r.isValid) ? 
                    '<span class="text-green-600 font-medium">✅ All files passed validation</span>' :
                    '<span class="text-red-600 font-medium">❌ Some files have validation errors</span>'
                }
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

/**
 * Create validation result card for a single file
 * @param {Object} result - Validation result
 * @returns {string} HTML string for the card
 */
function createValidationResultCard(result) {
    const statusColor = result.isValid ? 'green' : 'red';
    const statusIcon = result.isValid ? '✅' : '❌';
    
    return `
        <div class="border border-gray-200 rounded-lg p-4 mb-4 bg-white">
            <div class="flex justify-between items-start mb-3">
                <div>
                    <h4 class="font-semibold text-gray-900">${statusIcon} ${result.fileName}</h4>
                    <p class="text-sm text-gray-500">${formatFileSize(result.fileSize)} • ${result.summary.format || 'Unknown format'}</p>
                </div>
                <span class="px-2 py-1 text-xs font-medium rounded ${result.isValid ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                    ${result.isValid ? 'Valid' : 'Invalid'}
                </span>
            </div>
            
            ${result.errors.length > 0 ? `
                <div class="mb-3 p-3 bg-red-50 border border-red-200 rounded">
                    <h5 class="font-medium text-red-800 mb-1">Errors:</h5>
                    <ul class="text-sm text-red-700 list-disc list-inside">
                        ${result.errors.map(error => `<li>${error}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            
            ${result.warnings.length > 0 ? `
                <div class="mb-3 p-3 bg-yellow-50 border border-yellow-200 rounded">
                    <h5 class="font-medium text-yellow-800 mb-1">Warnings:</h5>
                    <ul class="text-sm text-yellow-700 list-disc list-inside">
                        ${result.warnings.map(warning => `<li>${warning}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            
            ${result.summary.totalRows ? `
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3 text-sm">
                    <div class="text-center p-2 bg-blue-50 rounded">
                        <div class="font-semibold text-blue-600">${result.summary.totalRows - 1}</div>
                        <div class="text-gray-600">Data Rows</div>
                    </div>
                    <div class="text-center p-2 bg-green-50 rounded">
                        <div class="font-semibold text-green-600">${result.summary.columns}</div>
                        <div class="text-gray-600">Columns</div>
                    </div>
                    <div class="text-center p-2 bg-purple-50 rounded">
                        <div class="font-semibold text-purple-600">${result.summary.uniqueGenes || 0}</div>
                        <div class="text-gray-600">Unique Genes</div>
                    </div>
                    <div class="text-center p-2 bg-orange-50 rounded">
                        <div class="font-semibold text-orange-600">${result.summary.geneColumnName || 'None'}</div>
                        <div class="text-gray-600">Gene Column</div>
                    </div>
                </div>
            ` : ''}
            
            ${result.summary.geneList && result.summary.geneList.length > 0 ? `
                <div class="mb-3">
                    <h6 class="font-medium text-gray-700 mb-2">Sample Genes:</h6>
                    <div class="flex flex-wrap gap-1">
                        ${result.summary.geneList.map(gene => 
                            `<span class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">${gene}</span>`
                        ).join('')}
                        ${result.summary.uniqueGenes > result.summary.geneList.length ? 
                            `<span class="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">+${result.summary.uniqueGenes - result.summary.geneList.length} more</span>` : ''
                        }
                    </div>
                </div>
            ` : ''}
            
            ${result.preview && result.preview.length > 0 ? `
                <details class="mt-3">
                    <summary class="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900">
                        View Data Preview (${result.preview.length} rows)
                    </summary>
                    <div class="mt-2 overflow-x-auto">
                        <table class="min-w-full text-xs border border-gray-200">
                            <thead class="bg-gray-50">
                                <tr>
                                    ${result.summary.columnNames.map(col => `<th class="px-2 py-1 border-b text-left">${col}</th>`).join('')}
                                </tr>
                            </thead>
                            <tbody>
                                ${result.preview.map(row => `
                                    <tr class="hover:bg-gray-50">
                                        ${row.map(cell => `<td class="px-2 py-1 border-b">${cell || ''}</td>`).join('')}
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </details>
            ` : ''}
        </div>
    `;
}

/**
 * Format file size in human readable format
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Initialize drag-and-drop file upload functionality
 */
export function initializeDragAndDrop() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('user_panel_file');
    const dropZoneText = document.getElementById('drop-zone-text');
    
    if (!dropZone || !fileInput) {
        console.error('Drop zone or file input not found:', { dropZone, fileInput });
        return;
    }

    console.log('Initializing drag and drop for:', { dropZone, fileInput });

    // Setup drop zone styling
    dropZone.style.position = 'relative';
    dropZone.style.cursor = 'pointer';
    if (dropZoneText) dropZoneText.style.pointerEvents = 'none';
    
    // Remove problematic attributes and override CSS
    fileInput.removeAttribute('required');
    fileInput.classList.remove('hidden');
    
    // Ensure file input is properly hidden but accessible
    fileInput.style.position = 'absolute';
    fileInput.style.left = '-9999px';
    fileInput.style.opacity = '0';
    fileInput.style.width = '1px';
    fileInput.style.height = '1px';
    fileInput.style.overflow = 'hidden';
    fileInput.style.clip = 'rect(1px, 1px, 1px, 1px)';
    
    // Drag enter/over events
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add('bg-sky-100', 'border-sky-600');
        });
    });
    
    // Drag leave/drop events
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('bg-sky-100', 'border-sky-600');
        });
    });
    
    // Handle file drop
    dropZone.addEventListener('drop', (e) => {
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            fileInput.files = e.dataTransfer.files;
            if (dropZoneText) dropZoneText.textContent = fileInput.files[0].name;
            fileInput.dispatchEvent(new Event('change', { bubbles: true }));
        }
    });
    
    // Handle click to select files - prevent multiple triggers
    dropZone.addEventListener('click', (e) => {
        // Only handle direct clicks on the drop zone, not bubbled events
        if (e.target !== dropZone && e.target !== dropZoneText) return;
        
        console.log('Drop zone clicked!');
        e.preventDefault();
        e.stopPropagation();
        
        // Trigger file input click
        console.log('Triggering file input click...');
        try {
            fileInput.click();
            console.log('File input click triggered successfully');
        } catch (error) {
            console.error('Error triggering file input click:', error);
        }
    });
}

/**
 * Initialize file upload form and tracking
 */
export function initializeFileUpload() {
    let uploadedFiles = [];
    const uploadStatusDiv = document.getElementById('upload-panel-status');
    const uploadedListDiv = document.createElement('div');
    uploadedListDiv.id = 'uploaded-files-list';
    uploadStatusDiv.parentNode.insertBefore(uploadedListDiv, uploadStatusDiv.nextSibling);

    const userPanelForm = document.getElementById('userPanelForm');
    const fileInput = document.getElementById('user_panel_file');
    const dropZoneText = document.getElementById('drop-zone-text');
    const validateBtn = document.getElementById('validate-files-btn');

    /**
     * Render the list of uploaded files
     */
    function renderUploadedFiles() {
        uploadedListDiv.innerHTML = '';
        if (uploadedFiles.length === 0) {
            if (dropZoneText) dropZoneText.textContent = 'Drag & drop your file here, or click to select';
            return;
        }
        
        const ul = document.createElement('ul');
        ul.className = 'mt-2 mb-2';
        uploadedFiles.forEach((file, idx) => {
            const li = document.createElement('li');
            li.className = 'flex items-center justify-between bg-sky-50 border border-sky-200 rounded px-2 py-1 mb-1';
            
            // File info with validation status
            const fileInfo = document.createElement('div');
            fileInfo.className = 'flex items-center flex-grow';
            
            const fileName = document.createElement('span');
            fileName.textContent = file.name;
            fileName.className = 'font-medium';
            
            const fileSize = document.createElement('span');
            fileSize.textContent = ` (${formatFileSize(file.size)})`;
            fileSize.className = 'text-xs text-gray-500 ml-1';
            
            fileInfo.appendChild(fileName);
            fileInfo.appendChild(fileSize);
            
            // Add validation status indicator
            const validationContainer = document.getElementById('file-validation-preview');
            if (validationContainer) {
                const statusIndicator = document.createElement('span');
                statusIndicator.className = 'ml-2 px-2 py-1 text-xs rounded';
                statusIndicator.textContent = '✅ Validated';
                statusIndicator.className += ' bg-green-100 text-green-800';
                fileInfo.appendChild(statusIndicator);
            } else {
                const statusIndicator = document.createElement('span');
                statusIndicator.className = 'ml-2 px-2 py-1 text-xs rounded bg-yellow-100 text-yellow-800';
                statusIndicator.textContent = '⏳ Pending validation';
                fileInfo.appendChild(statusIndicator);
            }
            
            li.appendChild(fileInfo);
            
            const removeBtn = document.createElement('button');
            removeBtn.textContent = 'Remove';
            removeBtn.className = 'ml-2 text-xs text-red-600 hover:underline';
            removeBtn.onclick = function() {
                uploadedFiles.splice(idx, 1);
                renderUploadedFiles();
                // Hide validate button if no files left
                if (uploadedFiles.length === 0 && validateBtn) {
                    validateBtn.style.display = 'none';
                }
                // Clear validation preview if no files left
                if (uploadedFiles.length === 0) {
                    const validationContainer = document.getElementById('file-validation-preview');
                    if (validationContainer) {
                        validationContainer.remove();
                    }
                } else {
                    // Re-validate remaining files
                    validateFilesPreview(uploadedFiles);
                }
            };
            
            li.appendChild(removeBtn);
            ul.appendChild(li);
        });
        uploadedListDiv.appendChild(ul);
    }

    /**
     * Show backend uploaded files
     */
    async function showBackendUploadedFiles() {
        const backendFiles = await fetchUploadedFiles();
        let backendListDiv = document.getElementById('backend-uploaded-files-list');
        
        if (!backendListDiv) {
            backendListDiv = document.createElement('div');
            backendListDiv.id = 'backend-uploaded-files-list';
            uploadedListDiv.parentNode.insertBefore(backendListDiv, uploadedListDiv);
        }
        
        backendListDiv.innerHTML = '';
        if (backendFiles.length === 0) return;
        
        const ul = document.createElement('ul');
        ul.className = 'mb-2';
        backendFiles.forEach(name => {
            const li = document.createElement('li');
            li.className = 'flex items-center bg-green-50 border border-green-200 rounded px-2 py-1 mb-1 text-green-800';
            li.textContent = name + ' (already uploaded)';
            
            const removeBtn = document.createElement('button');
            removeBtn.textContent = 'Remove';
            removeBtn.className = 'ml-2 text-xs text-red-600 hover:underline';
            removeBtn.onclick = async function() {
                try {
                    const resp = await removeUserPanel(name);
                    if (resp.ok) {
                        li.remove();
                        uploadStatusDiv.textContent = `Removed ${name}`;
                        uploadStatusDiv.style.color = 'green';
                    } else {
                        uploadStatusDiv.textContent = `Failed to remove ${name}`;
                        uploadStatusDiv.style.color = 'red';
                    }
                } catch (error) {
                    uploadStatusDiv.textContent = `Error removing ${name}`;
                    uploadStatusDiv.style.color = 'red';
                }
            };
            li.appendChild(removeBtn);
            ul.appendChild(li);
        });
        backendListDiv.appendChild(ul);
    }

    // Handle file input changes
    if (fileInput) {
        let isProcessingFileChange = false;
        
        fileInput.addEventListener('change', (e) => {
            // Prevent multiple rapid fire events
            if (isProcessingFileChange) return;
            isProcessingFileChange = true;
            
            const newFiles = Array.from(fileInput.files);
            let added = false, duplicate = false;
            
            newFiles.forEach(f => {
                if (uploadedFiles.some(u => u.name === f.name)) {
                    duplicate = true;
                } else {
                    uploadedFiles.push(f);
                    added = true;
                }
            });
            
            if (duplicate) {
                uploadStatusDiv.textContent = 'Duplicate file name(s) not allowed.';
                uploadStatusDiv.style.color = 'red';
            } else if (added) {
                uploadStatusDiv.textContent = '';
                // Show validate button when files are added
                if (validateBtn && uploadedFiles.length > 0) {
                    validateBtn.style.display = 'inline-block';
                }
                // Trigger validation preview for newly added files
                if (uploadedFiles.length > 0) {
                    validateFilesPreview(uploadedFiles);
                }
            }
            
            renderUploadedFiles();
            
            // Update drop zone text
            if (fileInput.files.length > 0) {
                if (dropZoneText) dropZoneText.textContent = fileInput.files[0].name;
            } else {
                if (dropZoneText) dropZoneText.textContent = 'Drag & drop your file here, or click to select';
                // Hide validate button when no files
                if (validateBtn) {
                    validateBtn.style.display = 'none';
                }
            }
            
            // Reset the processing flag after a short delay
            setTimeout(() => {
                isProcessingFileChange = false;
            }, 500);
        });
    }

    // Handle manual validation button
    if (validateBtn) {
        validateBtn.addEventListener('click', () => {
            if (uploadedFiles.length > 0) {
                validateFilesPreview(uploadedFiles);
            }
        });
    }

    // Handle form submission
    if (userPanelForm) {
        userPanelForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            if (uploadedFiles.length === 0) {
                uploadStatusDiv.textContent = 'No file selected.';
                uploadStatusDiv.style.color = 'red';
                return;
            }
            
            // Check if validation has been run and files are valid
            const validationContainer = document.getElementById('file-validation-preview');
            if (!validationContainer) {
                // Run validation first if not done yet
                uploadStatusDiv.textContent = 'Running validation before upload...';
                uploadStatusDiv.style.color = 'blue';
                await validateFilesPreview(uploadedFiles);
                return; // Stop here, user can submit again after seeing validation
            }
            
            // Check validation results
            const hasErrors = uploadedFiles.some(file => {
                // This is a simple check - in a real implementation you'd store validation results
                const errorElements = validationContainer.querySelectorAll('.bg-red-50');
                return errorElements.length > 0;
            });
            
            if (hasErrors) {
                if (!confirm('Some files have validation errors. Do you want to proceed with upload anyway?')) {
                    return;
                }
            }
            
            uploadStatusDiv.textContent = 'Uploading files...';
            uploadStatusDiv.style.color = 'blue';
            
            // Upload files to server
            const formData = new FormData();
            uploadedFiles.forEach(f => formData.append('user_panel_file', f));
            
            try {
                const response = await uploadPanelFiles(formData);
                if (response.ok) {
                    uploadStatusDiv.textContent = 'Upload successful!';
                    uploadStatusDiv.style.color = 'green';
                    uploadedFiles = [];
                    renderUploadedFiles();
                    showBackendUploadedFiles();
                    // Clear validation preview after successful upload
                    if (validationContainer) {
                        validationContainer.remove();
                    }
                } else {
                    uploadStatusDiv.textContent = 'Upload failed.';
                    uploadStatusDiv.style.color = 'red';
                }
            } catch (error) {
                uploadStatusDiv.textContent = 'Upload failed.';
                uploadStatusDiv.style.color = 'red';
            }
        });
    }

    // Show backend files when switching to upload tab
    const uploadTab = document.getElementById('upload-tab');
    if (uploadTab) {
        uploadTab.addEventListener('click', showBackendUploadedFiles);
        // Also show on page load if upload tab is default
        if (currentAPI === 'upload') showBackendUploadedFiles();
    }
}
