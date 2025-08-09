/**
 * Panel Library Grid - Refactored Main Class
 * Coordinates all panel library functionality using modular components
 */
class PanelLibraryGrid {
    constructor() {
        // Core data
        this.panels = [];
        this.filteredPanels = [];
        this.currentSort = { field: 'created_at', direction: 'desc' };
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
        this.serverPagination = null; // Store server pagination data
        this.useServerPagination = true; // Toggle between server and client pagination
        
        // Initialize module managers
        this.renderer = new PanelRenderer(this);
        this.filterManager = new PanelFilterManager(this);
        this.actionsManager = new PanelActionsManager(this);
        this.paginationManager = new PanelPaginationManager(this);
        
        this.init();
    }

    async init() {
        await this.loadPanels();
        this.setupEventListeners();
        this.render();
        // Initialize active filters indicator after first render
        if (typeof this.filterManager.updateActiveFiltersIndicator === 'function') {
            this.filterManager.updateActiveFiltersIndicator();
        }
        // Capture any pre-selected filter values once DOM is ready
        if (typeof this.filterManager.handleFilterChange === 'function') {
            this.filterManager.handleFilterChange();
        }
        // Initialize sort dropdown
        this.updateSortDropdown();
    }

    async loadPanels(page = 1, preserveFilters = false) {
        console.log("loadPanels");
        try {
            // Prepare query parameters
            const params = new URLSearchParams({
                page: page,
                per_page: this.pageSize
            });
            
            // Add current filters if preserving them
            if (preserveFilters || page > 1) {
                if (this.currentFilters.search) {
                    params.set('search', this.currentFilters.search);
                }
                if (this.currentFilters.status && this.currentFilters.status !== 'all') {
                    params.set('status', this.currentFilters.status);
                }
                if (this.currentFilters.visibility && this.currentFilters.visibility !== 'all') {
                    params.set('visibility', this.currentFilters.visibility);
                }
                // Add gene count range filter
                if (this.currentFilters.geneCountRange.min > 0) {
                    params.set('gene_count_min', this.currentFilters.geneCountRange.min);
                }
                if (this.currentFilters.geneCountRange.max < 10000) {
                    params.set('gene_count_max', this.currentFilters.geneCountRange.max);
                }
                // Add sorting parameters
                params.set('sort_by', this.currentSort.field);
                params.set('sort_order', this.currentSort.direction);
            }
            
            const response = await fetch(`/api/user/panels?${params}`, {
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (response.status === 401) {
                // User not authenticated - show message and use demo data
                PanelUtilities.showError('Please log in to view your panels. Showing demo data.');
                this.panels = []; //this.generateDemoData();
                this.useServerPagination = false;
                this.filterManager.applyFilters();
                return;
            }
            
            if (response.ok) {
                const data = await response.json();
                this.panels = data.panels || [];
                this.serverPagination = data.pagination || null;
                console.log(this.serverPagination)
                this.currentPage = this.serverPagination ? this.serverPagination.page : 1;
                
                // If no panels and it's the first page, show demo data for testing
                if (this.panels.length === 0 && page === 1) {
                    console.log('No panels found');
                    this.panels = []; //this.generateDemoData();
                    this.useServerPagination = false;
                    this.filterManager.applyFilters();
                } else {
                    // Use server pagination data
                    this.useServerPagination = true;
                    this.filteredPanels = this.panels; // With server pagination, panels are already filtered
                    this.filterManager.updateFilterInfo();
                    this.render();
                }
            } else {
                throw new Error('Failed to load panels');
            }
        } catch (error) {
            console.error('Error loading panels:', error);
            PanelUtilities.showError('Failed to load panels.');
            this.panels = []; //this.generateDemoData();
            this.useServerPagination = false;
            this.filterManager.applyFilters();
        }
    }

    generateDemoData() {
        const now = new Date();
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
                created_at: new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString(),
                updated_at: new Date(now.getTime() - 1 * 24 * 60 * 60 * 1000).toISOString(),
                accessed: new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString()
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
                created_at: new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000).toISOString(),
                updated_at: new Date(now.getTime() - 2 * 24 * 60 * 60 * 1000).toISOString(),
                accessed: new Date(now.getTime() - 5 * 60 * 60 * 1000).toISOString()
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
                created_at: new Date(now.getTime() - 1 * 24 * 60 * 60 * 1000).toISOString(),
                updated_at: new Date(now.getTime() - 12 * 60 * 60 * 1000).toISOString(),
                accessed: new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString()
            },
            {
                id: 4,
                name: "Breast Cancer Panel",
                description: "Targeted panel for breast cancer genetic analysis",
                gene_count: 85,
                status: "ACTIVE",
                visibility: "SHARED",
                version_count: 2,
                tags: ["breast-cancer", "oncology"],
                owner: { id: 1, username: "admin", full_name: "Admin User" },
                created_at: new Date(now.getTime() - 14 * 24 * 60 * 60 * 1000).toISOString(),
                updated_at: new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000).toISOString(),
                accessed: new Date(now.getTime() - 1 * 60 * 60 * 1000).toISOString()
            }
        ];
    }

    setupEventListeners() {
        // Panel management elements
        this.createPanelBtn = document.getElementById('create-panel-btn');
        this.panelModal = document.getElementById('panel-modal');
        this.closeModal = document.getElementById('close-modal');
        this.cancelPanel = document.getElementById('cancel-panel');
        this.panelForm = document.getElementById('panel-form');

        // Modal events
        if (this.createPanelBtn) {
            this.createPanelBtn.addEventListener('click', () => this.actionsManager.openPanelModal());
        }
        if (this.closeModal) {
            this.closeModal.addEventListener('click', () => this.actionsManager.closePanelModal());
        }
        if (this.cancelPanel) {
            this.cancelPanel.addEventListener('click', () => this.actionsManager.closePanelModal());
        }
        if (this.panelForm) {
            this.panelForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.actionsManager.savePanelData();
            });
        }

        // Search input
        const searchInput = document.getElementById('panel-search');
        if (searchInput) {
            searchInput.addEventListener('input', PanelUtilities.debounce((e) => {
                this.currentFilters.search = e.target.value;
                this.filterManager.applyFilters();
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

        // Sort dropdown
        const sortSelect = document.getElementById('sort-select');
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                this.handleSortChange(e.target.value);
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
                this.currentFilters.geneCountRange = this.filterManager.parseGeneCountRange(e.target.value);
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
                this.currentFilters.dateRange = this.filterManager.parseDateRange(e.target.value);
            });
        }
        this.filterManager.applyFilters();

        // Unified select-based filters (current template)
        ['source-filter','gene-count-filter','visibility-filter','date-filter','status-filter'].forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.addEventListener('change', () => {
                    this.filterManager.handleFilterChange();
                });
            }
        });

        // Clear filters button
        const clearFiltersBtn = document.getElementById('clear-filters');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', () => {
                this.filterManager.clearFilters();
                if (typeof this.filterManager.updateActiveFiltersIndicator === 'function') {
                    this.filterManager.updateActiveFiltersIndicator();
                }
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
                this.actionsManager.bulkDeletePanels();
            });
        }

        // Bulk export button
        const bulkExportBtn = document.getElementById('bulk-export');
        if (bulkExportBtn) {
            bulkExportBtn.addEventListener('click', () => {
                this.actionsManager.bulkExportPanels();
            });
        }

        // Bulk share button
        const bulkShareBtn = document.getElementById('bulk-share');
        if (bulkShareBtn) {
            bulkShareBtn.addEventListener('click', () => {
                this.actionsManager.bulkSharePanels();
            });
        }
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
            const gridHtml = this.renderer.renderGridView(paginatedPanels);
            container.innerHTML = gridHtml;
        } else {
            container.innerHTML = this.renderer.renderListView(paginatedPanels);
        }

        this.paginationManager.renderPagination();
        this.updateBulkActions();
    }

    // Delegate methods to appropriate managers
    applyFilters() { return this.filterManager.applyFilters(); }
    sortAndRender() { return this.filterManager.sortAndRender(); }
    updateFilterInfo() { return this.filterManager.updateFilterInfo(); }
    updateActiveFiltersIndicator() { return this.filterManager.updateActiveFiltersIndicator(); }
    clearFilters() { return this.filterManager.clearFilters(); }
    handleFilterChange() { return this.filterManager.handleFilterChange(); }
    
    renderPagination() { return this.paginationManager.renderPagination(); }
    goToPage(page) { return this.paginationManager.goToPage(page); }
    
    openPanel(panelId) { return this.actionsManager.openPanel(panelId); }
    editPanel(panelId) { return this.actionsManager.editPanel(panelId); }
    deletePanel(panelId) { return this.actionsManager.deletePanel(panelId); }
    duplicatePanel(panelId) { return this.actionsManager.duplicatePanel(panelId); }
    sharePanel(panelId) { return this.actionsManager.sharePanel(panelId); }
    exportPanel(panelId) { return this.actionsManager.exportPanel(panelId); }
    showVersionTimeline(panelId) { return this.actionsManager.showVersionTimeline(panelId); }
    showPanelDetails(panelId) { return this.actionsManager.showPanelDetails(panelId); }
    toggleDropdown(button) { return this.actionsManager.toggleDropdown(button); }
    toggleActionsMenu() { return this.actionsManager.toggleActionsMenu(); }
    
    // Utility method delegations
    truncateText(text, maxLength) { return PanelUtilities.truncateText(text, maxLength); }
    formatDate(dateString) { return PanelUtilities.formatDate(dateString); }
    showError(message) { return PanelUtilities.showError(message); }
    showSuccess(message) { return PanelUtilities.showSuccess(message); }
    parseTags(tagsText) { return PanelUtilities.parseTags(tagsText); }
    parseGenes(genesText) { return PanelUtilities.parseGenes(genesText); }

    // Local methods that remain in main class
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

    handleSortChange(sortValue) {
        // Parse field_direction format (e.g., "name_asc", "created_at_desc")
        const parts = sortValue.split('_');
        if (parts.length >= 2) {
            const direction = parts.pop(); // Last part is direction
            const field = parts.join('_'); // Rejoin remaining parts for field name
            this.currentSort = { field, direction };
            this.updateSortDropdown();
            this.filterManager.sortAndRender();
        }
    }

    updateSortDropdown() {
        const sortSelect = document.getElementById('sort-select');
        if (sortSelect) {
            const currentValue = `${this.currentSort.field}_${this.currentSort.direction}`;
            sortSelect.value = currentValue;
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

    handleSearch(searchTerm) {
        this.currentFilters.search = searchTerm;
        this.filterManager.applyFilters();
    }
}

console.log('Enhanced panel library initialized successfully');
const panelLibrary = new PanelLibraryGrid();

