/**
 * Enhanced Panel Library Grid Component
 * Comprehensive panel management interface with advanced features
 */

class PanelLibraryGrid {
    constructor() {
        this.panels = [];
        this.filteredPanels = [];
        this.currentSort = { field: 'updated_at', direction: 'desc' };
        this.currentFilters = {
            search: '',
            dateRange: { start: null, end: null },
            source: 'all',
            geneCountRange: { min: 0, max: 10000 },
            status: 'all',
            visibility: 'all',
            tags: []
        };
        this.selectedPanels = new Set();
        this.viewMode = 'grid'; // grid or list
        this.pageSize = 20;
        this.currentPage = 1;
        
        this.init();
    }

    async init() {
        await this.loadPanels();
        this.setupEventListeners();
        this.render();
        // Initialize active filters indicator after first render
        if (typeof this.updateActiveFiltersIndicator === 'function') {
            this.updateActiveFiltersIndicator();
        }
        // Capture any pre-selected filter values once DOM is ready
        if (typeof this.handleFilterChange === 'function') {
            this.handleFilterChange();
        }
    }

    async loadPanels() {
        try {
            const params = new URLSearchParams({
                page: 1,
                per_page: 100 // Load all panels for enhanced library
            });
            
            const response = await fetch(`/api/user/panels?${params}`, {
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (response.status === 401) {
                // User not authenticated - show message and use demo data
                this.showError('Please log in to view your panels. Showing demo data.');
                this.panels = this.generateDemoData();
                this.applyFilters();
                return;
            }
            
            if (response.ok) {
                const data = await response.json();
                this.panels = data.panels || [];                
                this.applyFilters();
            } else {
                throw new Error('Failed to load panels');
            }
        } catch (error) {
            console.error('Error loading panels:', error);
            this.applyFilters();
        }
    }

    setupEventListeners() {

        // Create new panel button
        const createPanelBtn = document.getElementById('create-panel-btn');
        if (createPanelBtn) {
            createPanelBtn.addEventListener('click', () => {
                this.createNewPanel();
           });
        }

        // Search input
        const searchInput = document.getElementById('panel-search');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce((e) => {
                this.currentFilters.search = e.target.value;
                this.applyFilters();
            }, 300));
            // Initial visibility check (fallback)
            setTimeout(() => {
                const clearBtn = document.getElementById('clear-search-btn');
                if (clearBtn) {
                    if (searchInput.value && searchInput.value.length > 0) {
                        clearBtn.classList.remove('hidden');
                    }
                }
            }, 0);
        }

        // Clear search button
        const clearBtn = document.getElementById('clear-search-btn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                this.clearSearch();
            });
        }

        /*
        const sortSelect = document.getElementById('sort-select');
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                handleSortChange(e.target.value);
            });
        }
        */

        // Sort dropdown
        const sortSelect = document.getElementById('panel-sort');
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                const [field, direction] = e.target.value.split('-');
                this.currentSort = { field, direction };
                this.sortAndRender();
            });
        }

        // View mode toggle
        const viewToggle = document.querySelectorAll('.view-mode-btn');
        viewToggle.forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.viewMode = e.target.dataset.mode;
                document.querySelectorAll('.view-mode-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.render();
            });
        });

        // Filter controls
        this.setupFilterListeners();
        
        // Bulk action buttons
        this.setupBulkActionListeners();
    }

    setupFilterListeners() {
        // Source filter
        const sourceSelect = document.getElementById('filter-source');
        if (sourceSelect) {
            sourceSelect.addEventListener('change', (e) => {
                this.currentFilters.source = e.target.value;
            });
        }

        // Gene count range filter
        const geneCountSelect = document.getElementById('gene-count-filter');
        if (geneCountSelect) {
            geneCountSelect.addEventListener('change', (e) => {
                this.currentFilters.geneCountRange = this.parseGeneCountRange(e.target.value);
            });
        }

        // Status filter
        const statusSelect = document.getElementById('filter-status');
        if (statusSelect) {
            statusSelect.addEventListener('change', (e) => {
                this.currentFilters.status = e.target.value;
            });
        }

        // Visibility filter
        const visibilitySelect = document.getElementById('visibility-filter');
        if (visibilitySelect) {
            visibilitySelect.addEventListener('change', (e) => {
                this.currentFilters.visibility = e.target.value;
            });
        }

        // Date range filter
        const dateRangeSelect = document.getElementById('date-filter');
        if (dateRangeSelect) {
            dateRangeSelect.addEventListener('change', (e) => {
                this.currentFilters.dateRange = this.parseDateRange(e.target.value);
            });
        }
        this.applyFilters();

        // Unified select-based filters (current template)
        ['source-filter','gene-count-filter','visibility-filter','date-filter','status-filter'].forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.addEventListener('change', () => {
                    this.handleFilterChange();
                });
            }
        });

        // Clear filters button
        const clearFiltersBtn = document.getElementById('clear-filters');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', () => {
                this.clearFilters();
                if (typeof this.updateActiveFiltersIndicator === 'function') this.updateActiveFiltersIndicator();
            });
        }
    }

    setupBulkActionListeners() {
        // Select all checkbox
        const selectAllCheckbox = document.getElementById('select-all-panels');
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.filteredPanels.forEach(panel => this.selectedPanels.add(panel.id));
                } else {
                    this.selectedPanels.clear();
                }
                this.updateBulkActions();
                this.render();
            });
        }

        // Bulk delete button
        const bulkDeleteBtn = document.getElementById('bulk-delete');
        if (bulkDeleteBtn) {
            bulkDeleteBtn.addEventListener('click', () => {
                this.bulkDeletePanels();
            });
        }

        // Bulk export button
        const bulkExportBtn = document.getElementById('bulk-export');
        if (bulkExportBtn) {
            bulkExportBtn.addEventListener('click', () => {
                this.bulkExportPanels();
            });
        }

        // Bulk share button
        const bulkShareBtn = document.getElementById('bulk-share');
        if (bulkShareBtn) {
            bulkShareBtn.addEventListener('click', () => {
                this.bulkSharePanels();
            });
        }
    }

    applyFilters() {
        let filtered = [...this.panels];

        // Text search
        if (this.currentFilters.search) {
            const clearBtn = document.getElementById('clear-search-btn');
            if (clearBtn) {
                clearBtn.classList.remove('hidden');
            }
            const searchTerm = this.currentFilters.search.toLowerCase();
            filtered = filtered.filter(panel => 
                panel.name.toLowerCase().includes(searchTerm) ||
                panel.description?.toLowerCase().includes(searchTerm) ||
                panel.tags?.some(tag => tag.toLowerCase().includes(searchTerm))
            );
        } else {
            const clearBtn = document.getElementById('clear-search-btn');
            if (clearBtn) {
                clearBtn.classList.add('hidden');
            }
        }

        // Date bucket / range filter
        if (this.currentFilters.dateRange && (this.currentFilters.dateRange.start || this.currentFilters.dateRange.end)) {
            const startDate = this.currentFilters.dateRange.start ? new Date(this.currentFilters.dateRange.start) : null;
            const endDate = this.currentFilters.dateRange.end ? new Date(this.currentFilters.dateRange.end) : null;
            if (endDate) endDate.setHours(23,59,59,999);
            filtered = filtered.filter(panel => {
                if (!panel.created_at) return true; // If missing, don't exclude
                const created = new Date(panel.created_at);
                if (startDate && created < startDate) return false;
                if (endDate && created > endDate) return false;
                return true;
            });
        }

        // Source filter (tolerant of multiple possible property names, case-insensitive)
        if (this.currentFilters.source && this.currentFilters.source !== 'all') {
            const desired = String(this.currentFilters.source).toLowerCase();
            filtered = filtered.filter(panel => {
                const panelSource = panel.source_type || panel.source || panel.source_name || panel.sourceOrganisation || panel.source_organization || panel.source_org;
                if (!panelSource) return false;
                return String(panelSource).toLowerCase() === desired;
            });
        }

        // Gene count range filter (only if user narrowed it via bucket select)
        const geneBucketSelect = document.getElementById('gene-count-filter');
        if (geneBucketSelect && geneBucketSelect.value) {
            filtered = filtered.filter(panel => {
                const gc = typeof panel.gene_count === 'number' ? panel.gene_count : parseInt(panel.gene_count) || 0;
                return gc >= this.currentFilters.geneCountRange.min && gc <= this.currentFilters.geneCountRange.max;
            });
        }

        // Visibility status filter
        if (this.currentFilters.visibility && this.currentFilters.visibility !== 'all') {
            const desiredVis = this.currentFilters.visibility.toLowerCase();
            filtered = filtered.filter(panel => {
                const visRaw = panel.visibility.includes('.') ? panel.visibility.split('.').pop().toLowerCase() : panel.visibility.toLowerCase();
                if (!visRaw) return false; // if filter active and no visibility info, exclude
                const vis = visRaw.toLowerCase();
                if (['private','shared','public'].includes(desiredVis)) return vis === desiredVis;
                return true;
            });
        }

        // Status filter
        if (this.currentFilters.status) {
            const desiredStatus = this.currentFilters.status.toUpperCase();
            filtered = filtered.filter(panel => {
                const status = panel.status.includes('.') ? panel.status.split('.').pop().toUpperCase() : panel.status.toUpperCase();
                return !status || status === desiredStatus;
            });
        }

    this.filteredPanels = filtered;
    this.sortAndRender();
    this.updateFilterInfo();
    this.updateActiveFiltersIndicator();
    }

    sortAndRender() {
        // Sort filtered panels
        this.filteredPanels.sort((a, b) => {
            const aVal = a[this.currentSort.field];
            const bVal = b[this.currentSort.field];
            
            let comparison = 0;
            if (aVal < bVal) comparison = -1;
            else if (aVal > bVal) comparison = 1;
            
            return this.currentSort.direction === 'desc' ? -comparison : comparison;
        });

        this.render();
    }

    render() {
        // Check for different possible container IDs
        let container = document.getElementById('panel-library-grid');
        if (!container) {
            container = document.getElementById('panels-grid');
        }
        if (!container) {
            container = document.getElementById('panels-container');
        }
        
        if (!container) {
            return;
        }

        // Hide loading state if it exists
        const loadingElement = document.getElementById('panels-loading');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }

        // Calculate pagination
        const startIndex = (this.currentPage - 1) * this.pageSize;
        const endIndex = startIndex + this.pageSize;
        const paginatedPanels = this.filteredPanels.slice(startIndex, endIndex);

        if (this.viewMode === 'grid') {
            const gridHtml = this.renderGridView(paginatedPanels);
            container.innerHTML = gridHtml;
        } else {
            container.innerHTML = this.renderListView(paginatedPanels);
        }

        this.renderPagination();
        this.updateBulkActions();
    }

    renderGridView(panels) {
        // Hide existing empty state if it exists
        const existingEmpty = document.getElementById('panels-empty');
        if (existingEmpty) {
            existingEmpty.classList.add('hidden');
        }
        
        if (panels.length === 0) {
            return this.renderEmptyState();
        }

        return `
            <div class="panels-grid">
                ${panels.map(panel => this.renderPanelCard(panel)).join('')}
            </div>
        `;
    }

    renderListView(panels) {
        // Hide existing empty state if it exists
        const existingEmpty = document.getElementById('panels-empty');
        if (existingEmpty) {
            existingEmpty.classList.add('hidden');
        }
        
        if (panels.length === 0) {
            return this.renderEmptyState();
        }

        return `
            <div class="panel-list">
                <div class="panel-list-header">
                    <div class="list-column list-select">
                        <input type="checkbox" id="select-all-visible" />
                    </div>
                    <div class="list-column list-name">Name</div>
                    <div class="list-column list-genes">Genes</div>
                    <div class="list-column list-source">Source</div>
                    <div class="list-column list-updated">Updated</div>
                    <div class="list-column list-sharing">Visiblity</div>
                    <div class="list-column list-actions">Actions</div>
                </div>
                ${panels.map(panel => this.renderPanelRow(panel)).join('')}
            </div>
        `;
    }

    renderPanelCard(panel) {
        const isSelected = this.selectedPanels.has(panel.id);
        const thumbnail = this.generatePanelThumbnail(panel);
        const statusColor = this.getStatusColor(panel.status);
        const sharingIcon = this.getSharingIcon(panel.visibility);

        return `
            <div class="panel-card ${isSelected ? 'selected' : ''}" data-panel-id="${panel.id}">
                <div class="panel-card-header">
                    <div class="panel-select">
                        <input type="checkbox" ${isSelected ? 'checked' : ''} 
                               onchange="panelLibrary.togglePanelSelection(${panel.id})" />
                    </div>
                    <div class="panel-status">
                        <span class="status-dot" style="background-color: ${statusColor}"></span>
                    </div>
                    <div class="panel-sharing">
                        <i class="fas ${sharingIcon}" title="${panel.visibility}"></i>
                    </div>
                </div>
                
                <div class="panel-thumbnail" onclick="panelLibrary.openPanel(${panel.id})">
                    ${thumbnail}
                </div>
                
                <div class="panel-info">
                    <h3 class="panel-title" title="${panel.name}">${this.truncateText(panel.name, 30)}</h3>
                    <p class="panel-description">${this.truncateText(panel.description || 'No description available', 50)}</p>
                    
                    <div class="panel-metadata">
                        <div class="metadata-item">
                            <i class="fas fa-dna"></i>
                            <span>${panel.gene_count || 0} genes</span>
                        </div>
                        <div class="metadata-item">
                            <i class="fas fa-code-branch"></i>
                            <span>v${panel.version_count || 1}</span>
                        </div>
                        <div class="metadata-item">
                            <i class="fas fa-clock"></i>
                            <span>${this.formatDate(panel.updated_at || panel.created_at)}</span>
                        </div>
                        <div class="metadata-item">
                            <i class="fas fa-user"></i>
                            <span>${panel.owner ? panel.owner.username : 'Unknown'}</span>
                        </div>
                    </div>
                    
                    <div class="panel-tags">
                        ${(panel.tags || []).slice(0, 3).map(tag => 
                            `<span class="tag">${tag}</span>`
                        ).join('')}
                        ${(panel.tags || []).length > 3 ? `<span class="tag-more">+${(panel.tags || []).length - 3}</span>` : ''}
                    </div>
                </div>
                
                <div class="panel-actions">
                    <button class="btn btn-outline-primary" onclick="panelLibrary.openPanel(${panel.id})">
                        <i class="fas fa-eye"></i> View
                    </button>
                    <button class="btn btn-outline-secondary" onclick="panelLibrary.showVersionTimeline(${panel.id})">
                        <i class="fas fa-history"></i> History
                    </button>
                    <div class="dropdown">
                        <button class="btn btn-outline-secondary dropdown-toggle" onclick="panelLibrary.toggleDropdown(this)">
                            <i class="fas fa-ellipsis-v"></i>
                        </button>
                        <ul class="dropdown-menu hidden">
                            <li><a class="dropdown-item" href="#" onclick="panelLibrary.editPanel(${panel.id})">
                                <i class="fas fa-edit"></i> Edit
                            </a></li>
                            <li><a class="dropdown-item" href="#" onclick="panelLibrary.duplicatePanel(${panel.id})">
                                <i class="fas fa-copy"></i> Duplicate
                            </a></li>
                            <li><a class="dropdown-item" href="#" onclick="panelLibrary.sharePanel(${panel.id})">
                                <i class="fas fa-share"></i> Share
                            </a></li>
                            <li><a class="dropdown-item" href="#" onclick="panelLibrary.exportPanel(${panel.id})">
                                <i class="fas fa-download"></i> Export
                            </a></li>
                            <li><hr style="border-color: #f8f9fa; margin: 4px 0;"></li>
                            <li><a class="dropdown-item" href="#" onclick="panelLibrary.deletePanel(${panel.id})" style="color: #dc3545 !important;">
                                <i class="fas fa-trash"></i> Delete
                            </a></li>
                        </ul>
                    </div>
                </div>
            </div>
        `;
    }

    renderPanelRow(panel) {
        const isSelected = this.selectedPanels.has(panel.id);
        const statusColor = this.getStatusColor(panel.status);
        const sharingIcon = this.getSharingIcon(panel.visibility);

        return `
            <div class="panel-row ${isSelected ? 'selected' : ''}" data-panel-id="${panel.id}">
                <div class="list-column list-select">
                    <input type="checkbox" ${isSelected ? 'checked' : ''} 
                           onchange="panelLibrary.togglePanelSelection(${panel.id})" />
                </div>
                <div class="list-column list-name">
                    <div class="panel-name-cell">
                        <span class="status-dot" style="background-color: ${statusColor}"></span>
                        <div class="name-info">
                            <h4 class="panel-name">${panel.name}</h4>
                            <p class="panel-description-short">${this.truncateText(panel.description || '', 40)}</p>
                        </div>
                    </div>
                </div>
                <div class="list-column list-genes">
                    <span class="gene-count">${panel.gene_count}</span>
                </div>
                <div class="list-column list-source">
                    <span class="source-badge">${panel.source_type}</span>
                </div>
                <div class="list-column list-updated">
                    <span class="updated-date">${this.formatDate(panel.updated_at)}</span>
                    <small class="version-info">v${panel.version_count}</small>
                </div>
                <div class="list-column list-sharing">
                    <i class="fas ${sharingIcon}" title="${panel.visibility}"></i>
                </div>
                <div class="list-column list-actions">
                    <button class="btn btn-sm btn-outline-primary" onclick="panelLibrary.openPanel(${panel.id})">
                        View
                    </button>
                    <button class="btn btn-sm btn-outline-secondary" onclick="panelLibrary.showVersionTimeline(${panel.id})">
                        History
                    </button>
                    <div class="dropdown relative">
                        <button class="btn btn-sm btn-outline-secondary dropdown-toggle" onclick="panelLibrary.toggleDropdown(this)">
                            <i class="fas fa-ellipsis-v"></i>
                        </button>
                        <ul class="dropdown-menu absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200 hidden z-50">
                            <li><a class="dropdown-item block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100" href="#" onclick="panelLibrary.editPanel(${panel.id})">Edit</a></li>
                            <li><a class="dropdown-item block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100" href="#" onclick="panelLibrary.duplicatePanel(${panel.id})">Duplicate</a></li>
                            <li><a class="dropdown-item block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100" href="#" onclick="panelLibrary.sharePanel(${panel.id})">Share</a></li>
                            <li><a class="dropdown-item block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100" href="#" onclick="panelLibrary.exportPanel(${panel.id})">Export</a></li>
                            <li><hr class="border-gray-200 my-1"></li>
                            <li><a class="dropdown-item block px-4 py-2 text-sm text-red-600 hover:bg-red-50" href="#" onclick="panelLibrary.deletePanel(${panel.id})">Delete</a></li>
                        </ul>
                    </div>
                </div>
            </div>
        `;
    }

    renderEmptyState() {
        // Check if there's an existing empty state element to show
        const existingEmpty = document.getElementById('panels-empty');
        if (existingEmpty) {
            existingEmpty.classList.remove('hidden');
            return ''; // Return empty string since we're showing the existing element
        }
        
        // Otherwise render our own empty state
        return `
            <div class="empty-state">
                <div class="empty-state-icon">
                    <i class="fas fa-folder-open"></i>
                </div>
                <h3>No panels found</h3>
                <p>You haven't saved any panels yet, or no panels match your current filters.</p>
                <div class="empty-state-actions">
                    <button class="px-4 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700" onclick="panelLibrary.clearFilters()">
                        Clear Filters
                    </button>
                    <a href="/" class="px-4 py-2 text-blue-600 bg-white border border-blue-600 rounded-lg hover:bg-blue-50">
                        Browse Panels
                    </a>
                </div>
            </div>
        `;
    }

    generatePanelThumbnail(panel) {
        // Generate a visual representation of the panel
        const colors = ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1', '#fd7e14'];
        const geneCount = Math.min(panel.gene_count, 100);
        const cellCount = Math.min(geneCount, 25);
        
        let thumbnail = '<div class="panel-thumbnail-grid">';
        for (let i = 0; i < cellCount; i++) {
            const color = colors[i % colors.length];
            thumbnail += `<div class="thumbnail-cell" style="background-color: ${color}"></div>`;
        }
        
        if (geneCount > cellCount) {
            thumbnail += `<div class="thumbnail-more">+${geneCount - cellCount}</div>`;
        }
        
        thumbnail += '</div>';
        return thumbnail;
    }

    getStatusColor(status) {
        const colors = {
            'ACTIVE': '#28a745',
            'DRAFT': '#ffc107',
            'ARCHIVED': '#6c757d',
            'DELETED': '#dc3545'
        };
        return colors[status] || '#6c757d';
    }

    getSharingIcon(visibility) {
        const icons = {
            'PRIVATE': 'fa-lock',
            'SHARED': 'fa-users',
            'PUBLIC': 'fa-globe'
        };
        return icons[visibility] || 'fa-lock';
    }

    togglePanelSelection(panelId) {
        if (this.selectedPanels.has(panelId)) {
            this.selectedPanels.delete(panelId);
        } else {
            this.selectedPanels.add(panelId);
        }
        this.updateBulkActions();
        this.render();
    }

    updateBulkActions() {
        const bulkActionsBar = document.getElementById('bulk-actions-bar');
        const selectedCount = this.selectedPanels.size;
        
        if (bulkActionsBar) {
            if (selectedCount > 0) {
                bulkActionsBar.style.display = 'flex';
                bulkActionsBar.querySelector('.selected-count').textContent = `${selectedCount} selected`;
            } else {
                bulkActionsBar.style.display = 'none';
            }
        }
    }

    renderPagination() {
        // Check for different possible pagination container IDs
        let paginationContainer = document.getElementById('panel-pagination');
        if (!paginationContainer) {
            paginationContainer = document.getElementById('panels-pagination');
        }
        
        if (!paginationContainer) return;

        const totalPages = Math.ceil(this.filteredPanels.length / this.pageSize);
        if (totalPages <= 1) {
            paginationContainer.innerHTML = '';
            return;
        }

        let pagination = '<nav><ul class="pagination">';
        
        // Previous button
        pagination += `
            <li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="panelLibrary.goToPage(${this.currentPage - 1})">Previous</a>
            </li>
        `;
        
        // Page numbers
        for (let i = 1; i <= totalPages; i++) {
            if (i === 1 || i === totalPages || (i >= this.currentPage - 2 && i <= this.currentPage + 2)) {
                pagination += `
                    <li class="page-item ${i === this.currentPage ? 'active' : ''}">
                        <a class="page-link" href="#" onclick="panelLibrary.goToPage(${i})">${i}</a>
                    </li>
                `;
            } else if (i === this.currentPage - 3 || i === this.currentPage + 3) {
                pagination += '<li class="page-item disabled"><span class="page-link">...</span></li>';
            }
        }
        
        // Next button
        pagination += `
            <li class="page-item ${this.currentPage === totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="panelLibrary.goToPage(${this.currentPage + 1})">Next</a>
            </li>
        `;
        
        pagination += '</ul></nav>';
        paginationContainer.innerHTML = pagination;
    }

    goToPage(page) {
        const totalPages = Math.ceil(this.filteredPanels.length / this.pageSize);
        if (page < 1 || page > totalPages) return;
        
        this.currentPage = page;
        this.render();
    }

    updateFilterInfo() {
        // Check for different possible filter info container IDs
        let filterInfo = document.getElementById('filter-info');
        if (!filterInfo) {
            filterInfo = document.getElementById('panels-filter-info');
        }
        if (!filterInfo) {
            filterInfo = document.getElementById('total-panels');
        }
        
        if (filterInfo) {
            const totalCount = this.panels.length;
            const filteredCount = this.filteredPanels.length;
            
            // Update total panels (reflect current filtered view)
            filterInfo.textContent = `${filteredCount}`;
        }

        // Also update total versions and total genes if present
        const versionsEl = document.getElementById('total-versions');
        const genesEl = document.getElementById('total-genes');
        if (versionsEl || genesEl) {
            const panelsForStats = this.filteredPanels && this.filteredPanels.length >= 0 ? this.filteredPanels : this.panels;
            const totals = panelsForStats.reduce((acc, p) => {
                const v = typeof p.version_count === 'number' ? p.version_count : parseInt(p.version_count) || 0;
                const g = typeof p.gene_count === 'number' ? p.gene_count : parseInt(p.gene_count) || 0;
                acc.versions += v;
                acc.genes += g;
                return acc;
            }, { versions: 0, genes: 0 });
            if (versionsEl) versionsEl.textContent = `${totals.versions}`;
            if (genesEl) genesEl.textContent = `${totals.genes}`;
        }
    }

    updateActiveFiltersIndicator() {
        const indicatorWrapper = document.getElementById('active-filters-indicator');
        const countEl = document.getElementById('active-filters-count');
        if (!indicatorWrapper || !countEl) return;

        const flags = new Set();
        // DOM-based filters
        const sourceVal = document.getElementById('source-filter')?.value;
        if (sourceVal) flags.add('source');
        const statusVal = document.getElementById('status-filter')?.value;
        if (statusVal) flags.add('status');
        const visibilityVal = document.getElementById('visibility-filter')?.value;
        if (visibilityVal) flags.add('visibility');
        const geneBucket = document.getElementById('gene-count-filter')?.value;
        if (geneBucket) flags.add('geneBucket');
        const dateBucket = document.getElementById('date-filter')?.value;
        if (dateBucket) flags.add('dateBucket');
        if (Array.isArray(this.currentFilters?.tags) && this.currentFilters.tags.length) flags.add('tags');

        const count = flags.size;
        if (count > 0) {
            countEl.textContent = count + "\x20filter";
            countEl.textContent += (count === 1 ? '' : 's');
            indicatorWrapper.classList.remove('hidden');
        } else {
            indicatorWrapper.classList.add('hidden');
        }
    }

    forceActiveFilterRefresh() {
        this.handleFilterChange();
        this.updateActiveFiltersIndicator();
    }

    clearFilters() {
        // Preserve existing search; only reset non-search filters
        const existingSearch = this.currentFilters?.search || '';
        this.currentFilters = {
            search: existingSearch,
            dateRange: { start: null, end: null },
            source: 'all',
            geneCountRange: { min: 0, max: 10000 },
            sharingStatus: 'all',
            status: null,
            tags: []
        };
        
        // Do NOT reset the search input (separate clear button handles that)
        
        // Current select-based filters in template
        const dateSelect = document.getElementById('date-filter');
        if (dateSelect) dateSelect.value = '';
        const sourceSelect = document.getElementById('source-filter') || document.getElementById('filter-source');
        if (sourceSelect) sourceSelect.value = '';
        const geneCountBucket = document.getElementById('gene-count-filter');
        if (geneCountBucket) geneCountBucket.value = '';
        const visibilitySelect = document.getElementById('visibility-filter');
        if (visibilitySelect) visibilitySelect.value = '';
        const statusSelect = document.getElementById('status-filter');
        if (statusSelect) statusSelect.value = '';
        
        this.applyFilters();
        if (typeof this.updateActiveFiltersIndicator === 'function') {
            this.updateActiveFiltersIndicator();
        }
    }

    // Utility methods
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays === 1) return 'Yesterday';
        if (diffDays < 7) return `${diffDays} days ago`;
        if (diffDays < 30) return `${Math.ceil(diffDays / 7)} weeks ago`;
        if (diffDays < 365) return `${Math.ceil(diffDays / 30)} months ago`;
        
        return date.toLocaleDateString();
    }

    showError(message) {
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded z-50';
        notification.style.zIndex = '9999';
        notification.innerHTML = `
            <div class="flex items-center">
                <span class="flex-1">${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-2 text-red-700 hover:text-red-900">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    showSuccess(message) {
        // Simple success notification
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded z-50';
        notification.style.zIndex = '9999';
        notification.innerHTML = `
            <div class="flex items-center">
                <span class="flex-1">${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-2 text-green-700 hover:text-green-900">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 3000);
    }

    // Panel action methods (to be implemented)
    async openPanel(panelId) {
        // Open panel details modal
        console.log('Opening panel:', panelId);
        this.showPanelDetails(panelId);
    }

    async editPanel(panelId) {
        // Open panel editor
        console.log('Editing panel:', panelId);
        // For now, just show an alert
        alert('Edit panel functionality coming soon!');
    }

    async duplicatePanel(panelId) {
        // Duplicate panel
        console.log('Duplicating panel:', panelId);
        alert('Duplicate panel functionality coming soon!');
    }

    async sharePanel(panelId) {
        // Open sharing dialog
        console.log('Sharing panel:', panelId);
        alert('Share panel functionality coming soon!');
    }

    async exportPanel(panelId) {
        // Export panel
        console.log('Exporting panel:', panelId);
        alert('Export panel functionality coming soon!');
    }

    async deletePanel(panelId) {
        // Delete panel with confirmation
        if (!confirm('Are you sure you want to delete this panel? This action cannot be undone.')) {
            return;
        }
        console.log('Deleting panel:', panelId);
        alert('Delete panel functionality coming soon!');
    }

    async showVersionTimeline(panelId) {
        // Show version timeline
        console.log('Showing version timeline for panel:', panelId);
        if (typeof showVersionTimeline === 'function') {
            showVersionTimeline(panelId);
        }
    }

    async showPanelDetails(panelId) {
        // Show panel details
        console.log('Showing panel details for:', panelId);
        if (typeof showPanelDetails === 'function') {
            showPanelDetails(panelId);
        }
    }

    // Search and filter methods
    handleSearch(searchTerm) {
        this.currentFilters.search = searchTerm;
        this.applyFilters();
    }

    handleSortChange(sortValue) {
        const [field, direction] = sortValue.split('_');
        this.currentSort = { field, direction };
        this.sortAndRender();
    }

    parseGeneCountRange(value) {
        switch (value) {
            case '1-10': return { min: 1, max: 10 };
            case '11-50': return { min: 11, max: 50 };
            case '51-100': return { min: 51, max: 100 };
            case '101+': return { min: 101, max: 10000 };
            default: return { min: 0, max: 10000 };
        }
    }

    parseDateRange(value) {
        const now = new Date();
        switch (value) {
            case 'today':
                return { start: new Date(now.setHours(0,0,0,0)), end: new Date(now.setHours(23,59,59,999)) };
            case 'week':
                const weekStart = new Date(now.setDate(now.getDate() - 7));
                return { start: weekStart, end: new Date() };
            case 'month':
                const monthStart = new Date(now.setMonth(now.getMonth() - 1));
                return { start: monthStart, end: new Date() };
            case 'year':
                const yearStart = new Date(now.setFullYear(now.getFullYear() - 1));
                return { start: yearStart, end: new Date() };
            default:
                return { start: null, end: null };
        }
    }

    // View mode methods
    setViewMode(mode) {
        this.viewMode = mode;
        this.render();
        
        // Update button states
        const gridBtn = document.querySelector('[onclick="panelLibrary.setViewMode(\'grid\')"]');
        const listBtn = document.querySelector('[onclick="panelLibrary.setViewMode(\'list\')"]');
        
        if (gridBtn && listBtn) {
            gridBtn.classList.toggle('bg-gray-200', mode === 'grid');
            listBtn.classList.toggle('bg-gray-200', mode === 'list');
        }
    }

    // Selection methods
    selectAll() {
        this.filteredPanels.forEach(panel => this.selectedPanels.add(panel.id));
        this.updateBulkActions();
        this.render();
    }

    clearSelection() {
        this.selectedPanels.clear();
        this.updateBulkActions();
        this.render();
    }

    clearSearch() {
        const searchInput = document.getElementById('panel-search');
        if (searchInput) {
            searchInput.value = '';
            this.handleSearch('');
        }
        const clearBtn = document.getElementById('clear-search-btn');
        if (clearBtn) clearBtn.classList.add('hidden');
    }

    deleteSelected() {
        const selectedIds = Array.from(this.selectedPanels);
        if (selectedIds.length === 0) {
            alert('Please select panels to delete');
            return;
        }
        
        if (!confirm(`Are you sure you want to delete ${selectedIds.length} selected panels? This action cannot be undone.`)) {
            return;
        }
        
        console.log('Deleting panels:', selectedIds);
        alert('Delete functionality coming soon!');
    }

    createNewPanel() {
        // Show create panel modal
        const modal = document.getElementById('createPanelModal');
        if (modal) {
            modal.classList.remove('hidden');
        }
    }

    submitNewPanel() {
        // Submit new panel form
        const form = document.getElementById('create-panel-form');
        if (form) {
            const formData = new FormData(form);
            console.log('Creating new panel with data:', Object.fromEntries(formData));
            alert('Create panel functionality coming soon!');
            
            // Close modal
            document.getElementById('createPanelModal').classList.add('hidden');
        }
    }

    async bulkDeletePanels() {
        if (this.selectedPanels.size === 0) return;
        console.log('Bulk deleting panels:', Array.from(this.selectedPanels));
    }

    async bulkExportPanels() {
        if (this.selectedPanels.size === 0) return;
        console.log('Bulk exporting panels:', Array.from(this.selectedPanels));
    }

    async bulkSharePanels() {
        if (this.selectedPanels.size === 0) return;
        console.log('Bulk sharing panels:', Array.from(this.selectedPanels));
    }

    // Dropdown functionality
    toggleDropdown(button) {
        const dropdown = button.parentElement;
        const menu = dropdown.querySelector('.dropdown-menu');
        
        // Close all other dropdowns first
        document.querySelectorAll('.dropdown-menu').forEach(otherMenu => {
            if (otherMenu !== menu) {
                otherMenu.classList.add('hidden');
            }
        });
        
        // Toggle this dropdown
        menu.classList.toggle('hidden');
        
        // Close dropdown when clicking outside
        if (!menu.classList.contains('hidden')) {
            const closeDropdown = (e) => {
                if (!dropdown.contains(e.target)) {
                    menu.classList.add('hidden');
                    document.removeEventListener('click', closeDropdown);
                }
            };
            setTimeout(() => document.addEventListener('click', closeDropdown), 0);
        }
    }

    // Actions menu toggle
    toggleActionsMenu() {
        const menu = document.getElementById('actions-menu');
        if (menu) {
            menu.classList.toggle('hidden');
        }
    }

    handleFilterChange() {
        // Update filters based on UI elements
        // Source
        this.currentFilters.source = document.getElementById('source-filter')?.value || 'all';
        // Sharing / visibility (support multiple possible IDs and take first non-empty value)
        const visEl = document.getElementById('visibility-filter');
        if (visEl && visEl.value) {
            this.currentFilters.sharingStatus = visEl.value;
        }

        // Status
        const statusVal = document.getElementById('status-filter')?.value || '';
        this.currentFilters.status = statusVal ? statusVal : null;
        // Date bucket
        const dateBucket = document.getElementById('date-filter')?.value || '';
        if (dateBucket) {
            this.currentFilters.dateRange = this.parseDateRange(dateBucket);
        } else {
            this.currentFilters.dateRange = { start: null, end: null };
        }
        // Gene count bucket -> range
        const geneBucket = document.getElementById('gene-count-filter')?.value || '';
        if (geneBucket) {
            this.currentFilters.geneCountRange = this.parseGeneCountRange(geneBucket);
        } else {
            // Reset to full range unless user provided manual min/max inputs already
            if (this.currentFilters.geneCountRange.min === undefined || this.currentFilters.geneCountRange.max === undefined) {
                this.currentFilters.geneCountRange = { min: 0, max: 10000 };
            }
        }
        this.applyFilters();
        if (typeof this.updateActiveFiltersIndicator === 'function') this.updateActiveFiltersIndicator();
    }

    compareSelected() {
        const selectedIds = Array.from(this.selectedPanels);
        if (selectedIds.length !== 2) {
            alert('Please select exactly 2 panels to compare');
            return;
        }
        // Implementation for comparison
        console.log('Comparing panels:', selectedIds);
    }

    exportSelected() {
        const selectedIds = Array.from(this.selectedPanels);
        if (selectedIds.length === 0) {
            alert('Please select panels to export');
            return;
        }
        // Implementation for export
        console.log('Exporting panels:', selectedIds);
    }
}

// Initialize when document is ready
let panelLibrary;
document.addEventListener('DOMContentLoaded', () => {
    // Check for different possible container IDs
    const containers = ['panel-library-grid', 'panels-grid', 'panels-container'];
    const hasContainer = containers.some(id => document.getElementById(id));
    
    if (hasContainer) {
        console.log('Enhanced panel library initialized successfully');
        panelLibrary = new PanelLibraryGrid();
        // Expose globally for inline onclick handlers and other modules
        if (typeof window !== 'undefined') {
            window.panelLibrary = panelLibrary;
        }
    }
});
