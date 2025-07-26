/**
 * PanelMerge - File Upload Functionality
 * Handles drag-and-drop uploads and file management
 */

import { currentAPI } from './state.js';
import { uploadPanelFiles, removeUserPanel, fetchUploadedFiles } from './api.js';

/**
 * Initialize drag-and-drop file upload functionality
 */
export function initializeDragAndDrop() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('user_panel_file');
    const dropZoneText = document.getElementById('drop-zone-text');
    
    if (!dropZone || !fileInput) return;

    // Setup drop zone styling and positioning
    dropZone.style.position = 'relative';
    dropZone.style.cursor = 'pointer';
    if (dropZoneText) dropZoneText.style.pointerEvents = 'none';
    
    // Position file input over drop zone
    fileInput.style.opacity = 0;
    fileInput.style.width = '100%';
    fileInput.style.height = '100%';
    fileInput.style.position = 'absolute';
    fileInput.style.left = 0;
    fileInput.style.top = 0;
    fileInput.style.zIndex = 2;
    fileInput.style.display = 'block';
    dropZone.appendChild(fileInput);
    
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
            fileInput.dispatchEvent(new Event('change'));
        }
    });
    
    // Handle click to select files
    dropZone.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.click();
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
            li.textContent = file.name;
            
            const removeBtn = document.createElement('button');
            removeBtn.textContent = 'Remove';
            removeBtn.className = 'ml-2 text-xs text-red-600 hover:underline';
            removeBtn.onclick = function() {
                uploadedFiles.splice(idx, 1);
                renderUploadedFiles();
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
        fileInput.addEventListener('change', () => {
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
            }
            
            renderUploadedFiles();
            
            // Update drop zone text
            if (fileInput.files.length > 0) {
                if (dropZoneText) dropZoneText.textContent = fileInput.files[0].name;
            } else {
                if (dropZoneText) dropZoneText.textContent = 'Drag & drop your file here, or click to select';
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
            
            // Preview logic for CSV/TSV files
            const file = uploadedFiles[0];
            const ext = file.name.split('.').pop().toLowerCase();
            
            if (ext === 'csv' || ext === 'tsv') {
                const reader = new FileReader();
                reader.onload = function(evt) {
                    let genes = [];
                    let delimiter = (ext === 'tsv') ? '\t' : ',';
                    let lines = evt.target.result.split(/\r?\n/);
                    let header = lines[0].split(delimiter);
                    
                    let geneIdx = header.findIndex(h => {
                        const colName = h.trim().toLowerCase();
                        return ['gene', 'genes', 'entity_name', 'genesymbol'].includes(colName);
                    });
                    
                    if (geneIdx !== -1) {
                        for (let i = 1; i < lines.length; i++) {
                            let row = lines[i].split(delimiter);
                            if (row[geneIdx]) genes.push(row[geneIdx].trim());
                        }
                        
                        if (genes.length > 0) {
                            uploadStatusDiv.textContent = `Loaded ${genes.length} genes from first file. Uploading...`;
                            uploadStatusDiv.style.color = 'green';
                        } else {
                            uploadStatusDiv.textContent = 'No genes found in first file. Uploading anyway...';
                            uploadStatusDiv.style.color = 'orange';
                        }
                    } else {
                        uploadStatusDiv.textContent = 'No gene column found in first file. Looking for: gene, genes, entity_name, or genesymbol. Uploading anyway...';
                        uploadStatusDiv.style.color = 'orange';
                    }
                };
                reader.readAsText(file);
            }
            
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
