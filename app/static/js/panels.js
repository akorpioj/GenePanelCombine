let allPanels = { uk: [], aus: [] };
let currentAPI = 'uk';

function fetchPanels(apiSource) {
    const url = `/api/panels?source=${apiSource}`;
    fetch(url)
        .then(r => r.json())
        .then(data => {
            allPanels[apiSource] = data;
            if (apiSource === currentAPI) {
                populateAll().catch(console.error);
            }
        });
}

function switchAPI(apiSource) {
    currentAPI = apiSource;
    // Update tab styling
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById(`${apiSource}-tab`).classList.add('active');
    // Show/hide upload form
    document.getElementById('upload-panel-form').style.display = (apiSource === 'upload') ? '' : 'none';
    // Show/hide panelapp-section
    var panelAppSection = document.getElementById('panelapp-section');
    if (panelAppSection) {
        panelAppSection.style.display = (apiSource === 'upload') ? 'none' : '';
    }
    // Update panel lists
    if (apiSource !== 'upload') {
        populateAll().catch(console.error);
    }
}

// list all the string fields you want to search
const fieldsToSearch = [
    'display_name',
    'description',
    'disease_group',
    'disease_sub_group',
];

function matches(panel, term) {
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

async function populateAll() {
    const term = document.getElementById("search_term_input")
        .value.trim().toLowerCase();

    // Start with text-based filtering
    let filtered = allPanels[currentAPI].filter(p => matches(p, term));

    // If the search term is a single word, also try fetching panels by gene name
    if (term && !term.includes(' ') && term.length > 1) {
        try {
            const geneUrl = `/api/genes/${encodeURIComponent(term)}?source=${currentAPI}`;
            const response = await fetch(geneUrl);
            if (response.ok) {
                const genePanels = await response.json();
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
            (allPanels.uk.concat(allPanels.aus)).find(p => (String(p.id) + '-' + p.api_source) === current));
        
        updateSelectOptions(select, filtered, current, currentPanel);
    }
}

function updateSelectOptions(select, list, current, currentPanel) {
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

function clearPanel(i) {
    const sel = document.getElementById(`panel_id_${i}`);
    const sel2 = document.getElementById(`list_type_${i}`);
    sel.value = "None";
    sel2.value = listTypeOptions[0];
    sel.classList.remove('panel-source-uk', 'panel-source-aus');
}

function clearAll() {
    // Clear search input
    document.getElementById('search_term_input').value = '';
    
    // Clear all panel selections
    for (let i = 1; i <= maxPanels; i++) {
        clearPanel(i);
    }
    
    // Refresh the panel list without any filters
    populateAll().catch(console.error);
}

function debounce(fn, delay) {
    let t;
    return (...args) => {
        clearTimeout(t);
        t = setTimeout(() => fn(...args), delay);
    };
}

// Fetch UK and AUS panels immediately on script load
fetchPanels('uk');
fetchPanels('aus');

// All DOM-related code must be inside DOMContentLoaded

document.addEventListener("DOMContentLoaded", () => {
    // Logging for debug
    console.log("Event: DOMContentLoaded");
    
    // Search input event with autocomplete
    const searchInput = document.getElementById("search_term_input");
    if (searchInput) {
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
                const response = await fetch(`/api/gene-suggestions?q=${encodeURIComponent(query)}&source=${currentAPI}&limit=8`);
                if (response.ok) {
                    const suggestions = await response.json();
                    displaySuggestions(suggestions, query);
                } else {
                    hideAutocomplete();
                }
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
        
        // Hide autocomplete when clicking outside
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !autocompleteDiv.contains(e.target)) {
                hideAutocomplete();
            }
        });
    }
    // Drag-and-drop support for user panel upload
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('user_panel_file');
    const dropZoneText = document.getElementById('drop-zone-text');
    if (dropZone && fileInput) {
        dropZone.style.position = 'relative';
        dropZone.style.cursor = 'pointer';
        if (dropZoneText) dropZoneText.style.pointerEvents = 'none';
        fileInput.style.opacity = 0;
        fileInput.style.width = '100%';
        fileInput.style.height = '100%';
        fileInput.style.position = 'absolute';
        fileInput.style.left = 0;
        fileInput.style.top = 0;
        fileInput.style.zIndex = 2;
        fileInput.style.display = 'block';
        dropZone.appendChild(fileInput);
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.add('bg-sky-100', 'border-sky-600');
            });
        });
        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.remove('bg-sky-100', 'border-sky-600');
            });
        });
        dropZone.addEventListener('drop', (e) => {
            if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                fileInput.files = e.dataTransfer.files;
                if (dropZoneText) dropZoneText.textContent = fileInput.files[0].name;
                fileInput.dispatchEvent(new Event('change'));
            }
        });
        dropZone.addEventListener('click', () => {
            e.stopPropagation(); // Prevents the event from reaching uploadArea
            fileInput.click()
        });
    }
    // User panel upload form submit
    const userPanelForm = document.getElementById('userPanelForm');
    // --- User Panel Upload: Track and manage uploaded files ---
    if (userPanelForm) {
        userPanelForm.addEventListener('submit', function(e) {
            e.preventDefault();
            if (uploadedFiles.length === 0) {
                uploadStatusDiv.textContent = 'No file selected.';
                uploadStatusDiv.style.color = 'red';
                switchAPI('upload');
                return;
            }
            // Optional: preview logic for CSV/TSV (show for first file only)
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
            // Actual upload to /upload_user_panel
            const formData = new FormData();
            uploadedFiles.forEach(f => formData.append('user_panel_file', f));
            fetch('/upload_user_panel', {
                method: 'POST',
                body: formData
            })
            .then(response => {
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
            })
            .catch(() => {
                uploadStatusDiv.textContent = 'Upload failed.';
                uploadStatusDiv.style.color = 'red';
            });
        });
    }
    let uploadedFiles = [];
    const uploadStatusDiv = document.getElementById('upload-panel-status');
    const uploadedListDiv = document.createElement('div');
    uploadedListDiv.id = 'uploaded-files-list';
    uploadStatusDiv.parentNode.insertBefore(uploadedListDiv, uploadStatusDiv.nextSibling);

    function renderUploadedFiles() {
        uploadedListDiv.innerHTML = '';
        if (uploadedFiles.length === 0) {
            // Also clear the drop zone text if no files are selected
            if (dropZoneText) dropZoneText.textContent = 'Drag & drop your file here, or click to select';
            /*fileInput.value = '';*/
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

    // Intercept file input changes to prevent duplicate names and update list
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
        // Clear file input so same file can be reselected if removed
        if (fileInput.files.length > 0) {
            if (dropZoneText) dropZoneText.textContent = fileInput.files[0].name;
        } else {
            if (dropZoneText) dropZoneText.textContent = 'Drag & drop your file here, or click to select';
            /*fileInput.value = '';*/
        }
    });

    // --- Fetch and display already uploaded files from backend on tab switch ---
    async function fetchUploadedFilesFromBackend() {
        try {
            const resp = await fetch('/uploaded_user_panels');
            if (!resp.ok) return [];
            const data = await resp.json();
            return data.files || [];
        } catch (e) {
            return [];
        }
    }

    async function showBackendUploadedFiles() {
        const backendFiles = await fetchUploadedFilesFromBackend();
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
                const resp = await fetch('/remove_user_panel', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ sheet_name: name })
                });
                if (resp.ok) {
                    li.remove();
                    uploadStatusDiv.textContent = `Removed ${name}`;
                    uploadStatusDiv.style.color = 'green';
                } else {
                    uploadStatusDiv.textContent = `Failed to remove ${name}`;
                    uploadStatusDiv.style.color = 'red';
                }
            };
            li.appendChild(removeBtn);
            ul.appendChild(li);
        });
        backendListDiv.appendChild(ul);
    }

    // Show backend files when switching to upload tab
    document.getElementById('upload-tab').addEventListener('click', showBackendUploadedFiles);
    // Also show on page load if upload tab is default
    if (currentAPI === 'upload') showBackendUploadedFiles();
});