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
            sharingStatus: 'all',
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
                
                // If no panels, show demo data for testing
                if (this.panels.length === 0) {
                    console.log('No panels found, showing demo data');
                    this.panels = this.generateDemoData();
                }
                
                this.applyFilters();
            } else {
                throw new Error('Failed to load panels');
            }
        } catch (error) {
            console.error('Error loading panels:', error);
            this.showError('Failed to load panels. Showing demo data.');
            this.panels = this.generateDemoData();
            this.applyFilters();
        }
    }

    generateDemoData() {
        return [
            {
                id: 1,
                name: "Solid tumours",
                description: "Comprehensive panel for solid tumor analysis including oncogenes and tumor suppressor genes",
                gene_count: 127,
                status: "ACTIVE",
                visibility: "PRIVATE",
                version_count: 3,
                tags: ["cancer", "solid-tumor", "oncogenes"],
                owner: { id: 1, username: "admin", full_name: "Admin User" },
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
            },
            {
                id: 2,
                name: "Combined: 2 panels (2025-08-07 17:08)",
                description: "Combined panel created from multiple sources for comprehensive genetic analysis",
                gene_count: 95,
                status: "ACTIVE",
                visibility: "PRIVATE",
                version_count: 1,
                tags: ["combined", "multi-source"],
                owner: { id: 1, username: "admin", full_name: "Admin User" },
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
            },
            {
                id: 3,
                name: "Combined: 2 panels (2025-08-07 14:53)",
                description: "Earlier combined panel version for testing and validation purposes",
                gene_count: 4,
                status: "DRAFT",
                visibility: "PRIVATE",
                version_count: 1,
                tags: ["test", "validation"],
                owner: { id: 1, username: "admin", full_name: "Admin User" },
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
            }
        ];
    }

    setupEventListeners() {
        // Search input
        const searchInput = document.getElementById('panel-search');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce((e) => {
                this.currentFilters.search = e.target.value;
                this.applyFilters();
            }, 300));
        }

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
        // Date range filter
        const startDate = document.getElementById('filter-start-date');
        const endDate = document.getElementById('filter-end-date');
        
        if (startDate) {
            startDate.addEventListener('change', (e) => {
                this.currentFilters.dateRange.start = e.target.value;
                this.applyFilters();
            });
        }
        
        if (endDate) {
            endDate.addEventListener('change', (e) => {
                this.currentFilters.dateRange.end = e.target.value;
                this.applyFilters();
            });
        }

        // Source filter
        const sourceSelect = document.getElementById('filter-source');
        if (sourceSelect) {
            sourceSelect.addEventListener('change', (e) => {
                this.currentFilters.source = e.target.value;
                this.applyFilters();
            });
        }

        // Gene count range
        const geneCountMin = document.getElementById('filter-gene-count-min');
        const geneCountMax = document.getElementById('filter-gene-count-max');
        
        if (geneCountMin) {
            geneCountMin.addEventListener('input', (e) => {
                this.currentFilters.geneCountRange.min = parseInt(e.target.value) || 0;
                this.applyFilters();
            });
        }
        
        if (geneCountMax) {
            geneCountMax.addEventListener('input', (e) => {
                this.currentFilters.geneCountRange.max = parseInt(e.target.value) || 10000;
                this.applyFilters();
            });
        }

        // Sharing status filter
        const sharingSelect = document.getElementById('filter-sharing');
        if (sharingSelect) {
            sharingSelect.addEventListener('change', (e) => {
                this.currentFilters.sharingStatus = e.target.value;
                this.applyFilters();
            });
        }

        // Clear filters button
        const clearFiltersBtn = document.getElementById('clear-filters');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', () => {
                this.clearFilters();
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
            const searchTerm = this.currentFilters.search.toLowerCase();
            filtered = filtered.filter(panel => 
                panel.name.toLowerCase().includes(searchTerm) ||
                panel.description?.toLowerCase().includes(searchTerm) ||
                panel.tags?.some(tag => tag.toLowerCase().includes(searchTerm))
            );
        }

        // Date range filter
        if (this.currentFilters.dateRange.start) {
            const startDate = new Date(this.currentFilters.dateRange.start);
            filtered = filtered.filter(panel => new Date(panel.created_at) >= startDate);
        }
        
        if (this.currentFilters.dateRange.end) {
            const endDate = new Date(this.currentFilters.dateRange.end);
            endDate.setHours(23, 59, 59, 999); // End of day
            filtered = filtered.filter(panel => new Date(panel.created_at) <= endDate);
        }

        // Source filter
        if (this.currentFilters.source !== 'all') {
            filtered = filtered.filter(panel => panel.source_type === this.currentFilters.source);
        }

        // Gene count range filter
        filtered = filtered.filter(panel => 
            panel.gene_count >= this.currentFilters.geneCountRange.min &&
            panel.gene_count <= this.currentFilters.geneCountRange.max
        );

        // Sharing status filter
        if (this.currentFilters.sharingStatus !== 'all') {
            filtered = filtered.filter(panel => {
                switch (this.currentFilters.sharingStatus) {
                    case 'private': return panel.visibility === 'PRIVATE';
                    case 'shared': return panel.visibility === 'SHARED';
                    case 'public': return panel.visibility === 'PUBLIC';
                    default: return true;
                }
            });
        }

        this.filteredPanels = filtered;
        this.sortAndRender();
        this.updateFilterInfo();
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
                    <div class="list-column list-sharing">Sharing</div>
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
            
            if (filteredCount === totalCount) {
                filterInfo.textContent = `${totalCount}`;
            } else {
                filterInfo.textContent = `${filteredCount}`;
            }
        }
    }

    clearFilters() {
        this.currentFilters = {
            search: '',
            dateRange: { start: null, end: null },
            source: 'all',
            geneCountRange: { min: 0, max: 10000 },
            sharingStatus: 'all',
            tags: []
        };
        
        // Reset UI elements
        const searchInput = document.getElementById('panel-search');
        if (searchInput) searchInput.value = '';
        
        const startDate = document.getElementById('filter-start-date');
        if (startDate) startDate.value = '';
        
        const endDate = document.getElementById('filter-end-date');
        if (endDate) endDate.value = '';
        
        const sourceSelect = document.getElementById('filter-source');
        if (sourceSelect) sourceSelect.value = 'all';
        
        const geneCountMin = document.getElementById('filter-gene-count-min');
        if (geneCountMin) geneCountMin.value = '';
        
        const geneCountMax = document.getElementById('filter-gene-count-max');
        if (geneCountMax) geneCountMax.value = '';
        
        const sharingSelect = document.getElementById('filter-sharing');
        if (sharingSelect) sharingSelect.value = 'all';
        
        this.applyFilters();
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

    handleFilterChange() {
        // Update filters based on UI elements
        const sourceFilter = document.getElementById('source-filter');
        const geneCountFilter = document.getElementById('gene-count-filter');
        const sharingFilter = document.getElementById('sharing-filter');
        const dateFilter = document.getElementById('date-filter');

        if (sourceFilter) this.currentFilters.source = sourceFilter.value;
        if (geneCountFilter) this.currentFilters.geneCountRange = this.parseGeneCountRange(geneCountFilter.value);
        if (sharingFilter) this.currentFilters.sharingStatus = sharingFilter.value;
        if (dateFilter) this.currentFilters.dateRange = this.parseDateRange(dateFilter.value);

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
    }

    compareSelected() {
        const selectedIds = Array.from(this.selectedPanels);
        if (selectedIds.length !== 2) {
            alert('Please select exactly 2 panels to compare');
            return;
        }
        
        if (typeof comparePanels === 'function') {
            comparePanels(selectedIds);
        }
    }

    exportSelected() {
        const selectedIds = Array.from(this.selectedPanels);
        if (selectedIds.length === 0) {
            alert('Please select panels to export');
            return;
        }
        console.log('Exporting panels:', selectedIds);
        alert('Export functionality coming soon!');
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

    // Additional utility methods
    clearSearch() {
        const searchInput = document.getElementById('panel-search');
        if (searchInput) {
            searchInput.value = '';
            this.handleSearch('');
        }
    }

    createNewPanel() {
        const modal = document.getElementById('createPanelModal');
        if (modal) {
            modal.classList.remove('hidden');
        }
    }

    submitNewPanel() {
        // Implementation for creating new panel
        console.log('Creating new panel...');
        // Add form validation and submission logic here
    }

    handleSearch(searchTerm) {
        this.currentFilters.search = searchTerm;
        this.applyFilters();
    }

    handleFilterChange() {
        // Update filters based on UI elements
        this.currentFilters.source = document.getElementById('source-filter')?.value || '';
        this.currentFilters.sharingStatus = document.getElementById('sharing-filter')?.value || '';
        this.applyFilters();
    }

    handleSortChange(sortValue) {
        const [field, direction] = sortValue.split('_');
        this.currentSort = { field, direction };
        this.sortAndRender();
    }

    setViewMode(mode) {
        this.viewMode = mode;
        
        // Update button states
        const gridBtn = document.querySelector('[onclick="panelLibrary.setViewMode(\'grid\')"]');
        const listBtn = document.querySelector('[onclick="panelLibrary.setViewMode(\'list\')"]');
        
        if (gridBtn && listBtn) {
            gridBtn.classList.toggle('bg-gray-100', mode === 'grid');
            listBtn.classList.toggle('bg-gray-100', mode === 'list');
        }
        
        this.render();
    }

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

    deleteSelected() {
        const selectedIds = Array.from(this.selectedPanels);
        if (selectedIds.length === 0) {
            alert('Please select panels to delete');
            return;
        }
        if (confirm(`Are you sure you want to delete ${selectedIds.length} panel(s)?`)) {
            // Implementation for deletion
            console.log('Deleting panels:', selectedIds);
        }
    }

    showPanelDetails(panelId) {
        // Implementation for showing panel details
        console.log('Showing details for panel:', panelId);
    }

    // Actions menu toggle (for main actions menu)
    toggleActionsMenu() {
        const menu = document.getElementById('actions-menu');
        if (menu) {
            menu.classList.toggle('hidden');
        }
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
    }
});
