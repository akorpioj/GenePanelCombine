/**
 * Panel Filter Manager
 * Handles all filtering, searching, and sorting logic
 */
class PanelFilterManager {
    constructor(panelLibrary) {
        this.panelLibrary = panelLibrary;
    }

    applyFilters() {
        // If using server pagination, reload from server with filters
        if (this.panelLibrary.useServerPagination) {
            this.panelLibrary.currentPage = 1; // Reset to first page when filters change
            this.panelLibrary.loadPanels(1, true);
            return;
        }
        
        // Client-side filtering for demo data
        let filtered = [...this.panelLibrary.panels];

        // Text search
        if (this.panelLibrary.currentFilters.search) {
            const clearBtn = document.getElementById('clear-search-btn');
            if (clearBtn) {
                clearBtn.classList.remove('hidden');
            }
            const searchTerm = this.panelLibrary.currentFilters.search.toLowerCase();
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
        if (this.panelLibrary.currentFilters.dateRange && (this.panelLibrary.currentFilters.dateRange.start || this.panelLibrary.currentFilters.dateRange.end)) {
            const startDate = this.panelLibrary.currentFilters.dateRange.start ? new Date(this.panelLibrary.currentFilters.dateRange.start) : null;
            const endDate = this.panelLibrary.currentFilters.dateRange.end ? new Date(this.panelLibrary.currentFilters.dateRange.end) : null;
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
        if (this.panelLibrary.currentFilters.source && this.panelLibrary.currentFilters.source !== 'all') {
            const desired = String(this.panelLibrary.currentFilters.source).toLowerCase();
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
                return gc >= this.panelLibrary.currentFilters.geneCountRange.min && gc <= this.panelLibrary.currentFilters.geneCountRange.max;
            });
        }

        // Visibility status filter
        if (this.panelLibrary.currentFilters.visibility && this.panelLibrary.currentFilters.visibility !== 'all') {
            const desiredVis = this.panelLibrary.currentFilters.visibility.toLowerCase();
            filtered = filtered.filter(panel => {
                const visRaw = panel.visibility.includes('.') ? panel.visibility.split('.').pop().toLowerCase() : panel.visibility.toLowerCase();
                if (!visRaw) return false; // if filter active and no visibility info, exclude
                const vis = visRaw.toLowerCase();
                if (['private','shared','public'].includes(desiredVis)) return vis === desiredVis;
                return true;
            });
        }

        // Status filter
        if (this.panelLibrary.currentFilters.status) {
            const desiredStatus = this.panelLibrary.currentFilters.status.toUpperCase();
            filtered = filtered.filter(panel => {
                const status = panel.status.includes('.') ? panel.status.split('.').pop().toUpperCase() : panel.status.toUpperCase();
                return !status || status === desiredStatus;
            });
        }

        this.panelLibrary.filteredPanels = filtered;
        this.sortAndRender();
        this.updateFilterInfo();
        this.updateActiveFiltersIndicator();
    }

    hasActiveFilters() {
        const filters = this.panelLibrary.currentFilters;
        
        // Check if any filters are active
        if (filters.search && filters.search.trim()) return true;
        if (filters.visibility && filters.visibility !== 'all') return true;
        if (filters.status && filters.status !== 'all') return true;
        
        // Check date range filter
        if (filters.dateRange && (filters.dateRange.start || filters.dateRange.end)) return true;
        
        // Check gene count range filter (only if it's not the default range)
        if (filters.geneCountRange && 
            (filters.geneCountRange.min > 0 || filters.geneCountRange.max < 10000)) return true;
        
        return false;
    }

    sortAndRender() {
        // If using server pagination, reload from server with new sort
        if (this.panelLibrary.useServerPagination) {
            this.panelLibrary.currentPage = 1; // Reset to first page when sort changes
            this.panelLibrary.loadPanels(1, true);
            return;
        }
        
        // Client-side sorting for demo data
        this.panelLibrary.filteredPanels.sort((a, b) => {
            let aVal = a[this.panelLibrary.currentSort.field];
            let bVal = b[this.panelLibrary.currentSort.field];
            
            // Handle different data types
            if (this.panelLibrary.currentSort.field === 'gene_count' || this.panelLibrary.currentSort.field === 'version_count') {
                // Numeric fields
                aVal = parseInt(aVal) || 0;
                bVal = parseInt(bVal) || 0;
            } else if (this.panelLibrary.currentSort.field === 'created_at' || this.panelLibrary.currentSort.field === 'updated_at' || this.panelLibrary.currentSort.field === 'accessed') {
                // Date fields
                aVal = new Date(aVal || 0);
                bVal = new Date(bVal || 0);
            } else if (typeof aVal === 'string' && typeof bVal === 'string') {
                // String fields (case insensitive)
                aVal = aVal.toLowerCase();
                bVal = bVal.toLowerCase();
            }
            
            let comparison = 0;
            if (aVal < bVal) comparison = -1;
            else if (aVal > bVal) comparison = 1;
            
            return this.panelLibrary.currentSort.direction === 'desc' ? -comparison : comparison;
        });

        this.panelLibrary.render();
    }

    updateFilterInfo() {
        console.log("updateFilterInfo");
        // Check for different possible filter info container IDs
        let filterInfo = document.getElementById('filter-info');
        if (!filterInfo) {
            filterInfo = document.getElementById('panels-filter-info');
        }
        if (!filterInfo) {
            filterInfo = document.getElementById('total-panels');
        }
        
        if (filterInfo) {
            if (this.panelLibrary.useServerPagination && this.panelLibrary.serverPagination) {
                // Use server pagination total count
                filterInfo.textContent = `${this.panelLibrary.serverPagination.total}`;
            } else {
                // Use client-side counts
                const totalCount = this.panelLibrary.panels.length;
                const filteredCount = this.panelLibrary.filteredPanels.length;
                filterInfo.textContent = `${filteredCount}`;
            }
        }

        // Also update total versions and total genes if present
        const versionsEl = document.getElementById('total-versions');
        const genesEl = document.getElementById('total-genes');
        if (versionsEl || genesEl) {
            if (this.panelLibrary.useServerPagination && this.panelLibrary.serverPagination) {
                // Use server-provided totals for filtered results
                if (versionsEl) versionsEl.textContent = `${this.panelLibrary.serverPagination.total_versions || 0}`;
                if (genesEl) genesEl.textContent = `${this.panelLibrary.serverPagination.total_genes || 0}`;
            } else {
                // Use client-side calculation for demo data
                const panelsForStats = this.panelLibrary.filteredPanels && this.panelLibrary.filteredPanels.length >= 0 ? this.panelLibrary.filteredPanels : this.panelLibrary.panels;
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
        if (Array.isArray(this.panelLibrary.currentFilters?.tags) && this.panelLibrary.currentFilters.tags.length) flags.add('tags');

        const count = flags.size;
        if (count > 0) {
            countEl.textContent = count + "\x20filter";
            countEl.textContent += (count === 1 ? '' : 's');
            indicatorWrapper.classList.remove('hidden');
        } else {
            indicatorWrapper.classList.add('hidden');
        }
    }

    clearFilters() {
        // Clear ALL filters including search
        this.panelLibrary.currentFilters = {
            search: '',
            dateRange: { start: null, end: null },
            source: 'all',
            geneCountRange: { min: 0, max: 10000 },
            sharingStatus: 'all',
            status: null,
            tags: []
        };
        
        // Clear the search input field
        const searchInput = document.getElementById('panel-search');
        if (searchInput) {
            searchInput.value = '';
        }
        
        // Hide the clear search button
        const clearSearchBtn = document.getElementById('clear-search-btn');
        if (clearSearchBtn) {
            clearSearchBtn.classList.add('hidden');
        }
        
        // Clear all select-based filters in template
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
        
        // When clearing filters, we must reload from server to get all panels back
        // This prevents getting stuck with an empty panels array from previous filtering
        this.panelLibrary.useServerPagination = true;
        this.panelLibrary.currentPage = 1;
        
        // Force a server reload with cleared filters instead of calling applyFilters()
        this.panelLibrary.loadPanels(1, true);
        
        // Update the filter indicators
        if (typeof this.updateActiveFiltersIndicator === 'function') {
            this.updateActiveFiltersIndicator();
        }
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

    handleFilterChange() {
        // Update filters based on UI elements
        // Source
        this.panelLibrary.currentFilters.source = document.getElementById('source-filter')?.value || 'all';
        // Sharing / visibility (support multiple possible IDs and take first non-empty value)
        const visEl = document.getElementById('visibility-filter');
        if (visEl && visEl.value) {
            this.panelLibrary.currentFilters.sharingStatus = visEl.value;
        }

        // Status
        const statusVal = document.getElementById('status-filter')?.value || '';
        this.panelLibrary.currentFilters.status = statusVal ? statusVal : null;
        // Date bucket
        const dateBucket = document.getElementById('date-filter')?.value || '';
        if (dateBucket) {
            this.panelLibrary.currentFilters.dateRange = this.parseDateRange(dateBucket);
        } else {
            this.panelLibrary.currentFilters.dateRange = { start: null, end: null };
        }
        // Gene count bucket -> range
        const geneBucket = document.getElementById('gene-count-filter')?.value || '';
        if (geneBucket) {
            this.panelLibrary.currentFilters.geneCountRange = this.parseGeneCountRange(geneBucket);
        } else {
            // Reset to full range unless user provided manual min/max inputs already
            if (this.panelLibrary.currentFilters.geneCountRange.min === undefined || this.panelLibrary.currentFilters.geneCountRange.max === undefined) {
                this.panelLibrary.currentFilters.geneCountRange = { min: 0, max: 10000 };
            }
        }
        this.applyFilters();
        if (typeof this.updateActiveFiltersIndicator === 'function') {
            this.updateActiveFiltersIndicator();
        }
    }
}
