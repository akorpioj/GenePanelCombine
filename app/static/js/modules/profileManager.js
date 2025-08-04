/**
 * Profile Management Module
 * Handles user profile tabs and panel management functionality
 */

export class ProfileManager {
    constructor() {
        this.currentPage = 1;
        this.totalPages = 1;
        this.isLoading = false;
        this.searchTimeout = null;
        
        this.initializeElements();
        this.bindEvents();
        this.initializeTimezone();
    }
    
    initializeElements() {
        // Tab elements
        this.profileTab = document.getElementById('profile-tab');
        this.panelsTab = document.getElementById('panels-tab');
        this.profileContent = document.getElementById('profile-content');
        this.panelsContent = document.getElementById('panels-content');
        
        // Panel management elements
        this.createPanelBtn = document.getElementById('create-panel-btn');
        this.panelModal = document.getElementById('panel-modal');
        this.closeModal = document.getElementById('close-modal');
        this.cancelPanel = document.getElementById('cancel-panel');
        this.panelForm = document.getElementById('panel-form');
        
        // Search and filter elements
        this.searchInput = document.getElementById('panel-search');
        this.statusFilter = document.getElementById('status-filter');
        this.visibilityFilter = document.getElementById('visibility-filter');
        this.sortSelect = document.getElementById('sort-select');
        
        // Grid and pagination elements
        this.panelsGrid = document.getElementById('panels-grid');
        this.panelsLoading = document.getElementById('panels-loading');
        this.panelsEmpty = document.getElementById('panels-empty');
        this.paginationContainer = document.getElementById('pagination-container');
    }
    
    bindEvents() {
        // Tab switching
        if (this.profileTab) {
            this.profileTab.addEventListener('click', () => this.switchTab('profile'));
        }
        
        if (this.panelsTab) {
            this.panelsTab.addEventListener('click', () => {
                this.switchTab('panels');
                if (!this.isLoading) {
                    this.loadPanels();
                }
            });
        }
        
        // Modal events
        if (this.createPanelBtn) {
            this.createPanelBtn.addEventListener('click', () => this.openPanelModal());
        }
        
        if (this.closeModal) {
            this.closeModal.addEventListener('click', () => this.closePanelModal());
        }
        
        if (this.cancelPanel) {
            this.cancelPanel.addEventListener('click', () => this.closePanelModal());
        }
        
        if (this.panelForm) {
            this.panelForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.savePanelData();
            });
        }
        
        // Search and filter events
        if (this.searchInput) {
            this.searchInput.addEventListener('input', () => {
                clearTimeout(this.searchTimeout);
                this.searchTimeout = setTimeout(() => {
                    this.currentPage = 1;
                    this.loadPanels();
                }, 300);
            });
        }
        
        if (this.statusFilter) {
            this.statusFilter.addEventListener('change', () => {
                this.currentPage = 1;
                this.loadPanels();
            });
        }
        
        if (this.visibilityFilter) {
            this.visibilityFilter.addEventListener('change', () => {
                this.currentPage = 1;
                this.loadPanels();
            });
        }
        
        if (this.sortSelect) {
            this.sortSelect.addEventListener('change', () => {
                this.currentPage = 1;
                this.loadPanels();
            });
        }
        
        // Global panel action functions
        window.editPanel = (panelId) => this.editPanel(panelId);
        window.exportPanel = (panelId) => this.exportPanel(panelId);
        window.duplicatePanel = (panelId) => this.duplicatePanel(panelId);
        window.deletePanel = (panelId) => this.deletePanel(panelId);
    }
    
    switchTab(tab) {
        if (tab === 'profile') {
            this.profileTab?.classList.add('active', 'text-blue-600', 'border-blue-500');
            this.profileTab?.classList.remove('text-gray-500', 'border-transparent');
            this.panelsTab?.classList.remove('active', 'text-blue-600', 'border-blue-500');
            this.panelsTab?.classList.add('text-gray-500', 'border-transparent');
            
            this.profileContent?.classList.remove('hidden');
            this.panelsContent?.classList.add('hidden');
        } else {
            this.panelsTab?.classList.add('active', 'text-blue-600', 'border-blue-500');
            this.panelsTab?.classList.remove('text-gray-500', 'border-transparent');
            this.profileTab?.classList.remove('active', 'text-blue-600', 'border-blue-500');
            this.profileTab?.classList.add('text-gray-500', 'border-transparent');
            
            this.panelsContent?.classList.remove('hidden');
            this.profileContent?.classList.add('hidden');
        }
    }
    
    async loadPanels() {
        if (!this.searchInput) return;
        
        this.isLoading = true;
        
        this.panelsLoading?.classList.remove('hidden');
        this.panelsEmpty?.classList.add('hidden');
        this.paginationContainer?.classList.add('hidden');
        
        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                per_page: 9,
                search: this.searchInput.value || '',
                status: this.statusFilter?.value || '',
                visibility: this.visibilityFilter?.value || '',
                sort_by: this.sortSelect?.value || 'updated_at',
                sort_order: 'desc'
            });
            
            const response = await fetch(`/api/v1/saved-panels?${params}`, {
                headers: {
                    'Accept': 'application/json',
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            this.panelsLoading?.classList.add('hidden');
            
            if (data.panels && data.panels.length > 0) {
                this.renderPanels(data.panels);
                this.updatePagination(data.pagination);
                this.paginationContainer?.classList.remove('hidden');
            } else {
                this.panelsEmpty?.classList.remove('hidden');
            }
        } catch (error) {
            console.error('Error loading panels:', error);
            this.panelsLoading?.classList.add('hidden');
            this.showError('Failed to load panels. Please try again.');
        } finally {
            this.isLoading = false;
        }
    }
    
    renderPanels(panels) {
        if (!this.panelsGrid) return;
        
        // Clear existing panels but keep loading/empty state elements
        const existingCards = this.panelsGrid.querySelectorAll('.panel-card');
        existingCards.forEach(card => card.remove());
        
        panels.forEach(panel => {
            const card = this.createPanelCard(panel);
            this.panelsGrid.appendChild(card);
        });
    }
    
    createPanelCard(panel) {
        const card = document.createElement('div');
        card.className = 'panel-card bg-white rounded-lg shadow-md border border-gray-200 hover:shadow-lg transition-all duration-200';
        
        const statusClass = `status-${panel.status.toLowerCase()}`;
        const visibilityClass = `visibility-${panel.visibility.toLowerCase()}`;
        
        card.innerHTML = `
            <div class="p-6">
                <div class="flex justify-between items-start mb-3">
                    <h3 class="text-lg font-semibold text-gray-900 truncate">${this.escapeHtml(panel.name)}</h3>
                    <div class="flex space-x-1">
                        <span class="status-badge ${statusClass}">${panel.status}</span>
                        <span class="status-badge ${visibilityClass}">${panel.visibility}</span>
                    </div>
                </div>
                
                ${panel.description ? `<p class="text-gray-600 text-sm mb-3 line-clamp-2">${this.escapeHtml(panel.description)}</p>` : ''}
                
                <div class="flex justify-between items-center text-sm text-gray-500 mb-4">
                    <span>${panel.gene_count} genes</span>
                    <span>v${panel.version_count}</span>
                </div>
                
                ${panel.tags && Array.isArray(panel.tags) && panel.tags.length > 0 ? `
                    <div class="flex flex-wrap gap-1 mb-4">
                        ${panel.tags.slice(0, 3).map(tag => `<span class="bg-gray-100 text-gray-700 px-2 py-1 rounded-full text-xs">${this.escapeHtml(tag)}</span>`).join('')}
                        ${panel.tags.length > 3 ? `<span class="bg-gray-100 text-gray-700 px-2 py-1 rounded-full text-xs">+${panel.tags.length - 3}</span>` : ''}
                    </div>
                ` : ''}
                
                <div class="text-xs text-gray-400 mb-4">
                    Updated ${this.formatDate(panel.updated_at)}
                </div>
                
                <div class="flex justify-between items-center pt-3 border-t border-gray-200">
                    <div class="flex space-x-2">
                        <button onclick="editPanel(${panel.id})" class="text-blue-600 hover:text-blue-800 text-sm font-medium">Edit</button>
                        <button onclick="exportPanel(${panel.id})" class="text-green-600 hover:text-green-800 text-sm font-medium">Export</button>
                        <button onclick="duplicatePanel(${panel.id})" class="text-purple-600 hover:text-purple-800 text-sm font-medium">Duplicate</button>
                    </div>
                    <button onclick="deletePanel(${panel.id})" class="text-red-600 hover:text-red-800 text-sm font-medium">Delete</button>
                </div>
            </div>
        `;
        
        return card;
    }
    
    updatePagination(pagination) {
        this.totalPages = pagination.pages;
        this.currentPage = pagination.page;
        
        const pageStart = document.getElementById('page-start');
        const pageEnd = document.getElementById('page-end');
        const totalPanels = document.getElementById('total-panels');
        
        if (pageStart) {
            pageStart.textContent = ((this.currentPage - 1) * pagination.per_page) + 1;
        }
        if (pageEnd) {
            pageEnd.textContent = Math.min(this.currentPage * pagination.per_page, pagination.total);
        }
        if (totalPanels) {
            totalPanels.textContent = pagination.total;
        }
        
        // Update pagination buttons
        const prevBtn = document.getElementById('prev-page');
        const nextBtn = document.getElementById('next-page');
        
        if (prevBtn) {
            prevBtn.disabled = this.currentPage <= 1;
            prevBtn.onclick = () => {
                if (this.currentPage > 1) {
                    this.currentPage--;
                    this.loadPanels();
                }
            };
        }
        
        if (nextBtn) {
            nextBtn.disabled = this.currentPage >= this.totalPages;
            nextBtn.onclick = () => {
                if (this.currentPage < this.totalPages) {
                    this.currentPage++;
                    this.loadPanels();
                }
            };
        }
    }
    
    openPanelModal(panelData = null) {
        const modalTitle = document.getElementById('modal-title');
        const panelId = document.getElementById('panel-id');
        
        if (panelData) {
            if (modalTitle) modalTitle.textContent = 'Edit Panel';
            if (panelId) panelId.value = panelData.id;
            this.populateForm(panelData);
        } else {
            if (modalTitle) modalTitle.textContent = 'Create New Panel';
            if (panelId) panelId.value = '';
            this.clearForm();
        }
        
        this.panelModal?.classList.remove('hidden');
    }
    
    closePanelModal() {
        this.panelModal?.classList.add('hidden');
        this.clearForm();
    }
    
    populateForm(panelData) {
        const panelName = document.getElementById('panel-name');
        const panelDescription = document.getElementById('panel-description');
        const panelTags = document.getElementById('panel-tags');
        const panelStatus = document.getElementById('panel-status');
        const panelVisibility = document.getElementById('panel-visibility');
        
        if (panelName) panelName.value = panelData.name || '';
        if (panelDescription) panelDescription.value = panelData.description || '';
        if (panelTags) {
            if (Array.isArray(panelData.tags)) {
                panelTags.value = panelData.tags.join(', ');
            } else if (typeof panelData.tags === 'string') {
                panelTags.value = panelData.tags;
            } else {
                panelTags.value = '';
            }
        }
        if (panelStatus) panelStatus.value = panelData.status || 'ACTIVE';
        if (panelVisibility) panelVisibility.value = panelData.visibility || 'PRIVATE';
        
        // Load genes if editing
        if (panelData.id) {
            this.loadPanelGenes(panelData.id);
        }
    }
    
    clearForm() {
        const fields = ['panel-name', 'panel-description', 'panel-tags', 'panel-genes'];
        fields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) field.value = '';
        });
        
        const panelStatus = document.getElementById('panel-status');
        const panelVisibility = document.getElementById('panel-visibility');
        
        if (panelStatus) panelStatus.value = 'ACTIVE';
        if (panelVisibility) panelVisibility.value = 'PRIVATE';
    }
    
    async savePanelData() {
        const panelId = document.getElementById('panel-id')?.value;
        const isEdit = panelId !== '';
        
        const data = {
            name: document.getElementById('panel-name')?.value || '',
            description: document.getElementById('panel-description')?.value || '',
            tags: this.parseTags(document.getElementById('panel-tags')?.value || ''),
            status: document.getElementById('panel-status')?.value || 'ACTIVE',
            visibility: document.getElementById('panel-visibility')?.value || 'PRIVATE',
            genes: this.parseGenes(document.getElementById('panel-genes')?.value || '')
        };
        
        try {
            const url = isEdit ? `/api/v1/saved-panels/${panelId}` : '/api/v1/saved-panels';
            const method = isEdit ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Failed to save panel');
            }
            
            this.showSuccess(isEdit ? 'Panel updated successfully!' : 'Panel created successfully!');
            this.closePanelModal();
            this.loadPanels();
        } catch (error) {
            console.error('Error saving panel:', error);
            this.showError(error.message || 'Failed to save panel. Please try again.');
        }
    }
    
    parseTags(tagsText) {
        if (!tagsText.trim()) return [];
        
        // Split by comma and clean up
        return tagsText
            .split(',')
            .map(tag => tag.trim())
            .filter(tag => tag.length > 0);
    }
    
    parseGenes(genesText) {
        if (!genesText.trim()) return [];
        
        // Split by comma or newline and clean up
        return genesText
            .split(/[,\n]+/)
            .map(gene => gene.trim().toUpperCase())
            .filter(gene => gene.length > 0)
            .map(gene => ({
                gene_symbol: gene,
                confidence_level: '3',  // Default to high confidence
                phenotype: '',
                mode_of_inheritance: '',
                user_notes: ''
            }));
    }
    
    async loadPanelGenes(panelId) {
        try {
            const response = await fetch(`/api/v1/saved-panels/${panelId}`);
            if (!response.ok) throw new Error('Failed to load panel genes');
            
            const panel = await response.json();
            if (panel.genes) {
                const genesText = panel.genes.map(gene => gene.gene_symbol).join('\n');
                const panelGenes = document.getElementById('panel-genes');
                if (panelGenes) panelGenes.value = genesText;
            }
        } catch (error) {
            console.error('Error loading panel genes:', error);
        }
    }
    
    // Panel action methods
    async editPanel(panelId) {
        try {
            const response = await fetch(`/api/v1/saved-panels/${panelId}`);
            if (!response.ok) throw new Error('Failed to load panel');
            
            const panel = await response.json();
            this.openPanelModal(panel);
        } catch (error) {
            console.error('Error loading panel for edit:', error);
            this.showError('Failed to load panel for editing.');
        }
    }
    
    async exportPanel(panelId) {
        try {
            const response = await fetch(`/api/v1/saved-panels/${panelId}/export/csv`);
            if (!response.ok) throw new Error('Export failed');
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `panel_${panelId}.csv`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            this.showSuccess('Panel exported successfully!');
        } catch (error) {
            console.error('Error exporting panel:', error);
            this.showError('Failed to export panel.');
        }
    }
    
    async duplicatePanel(panelId) {
        try {
            const response = await fetch(`/api/v1/saved-panels/${panelId}/duplicate`, {
                method: 'POST'
            });
            
            if (!response.ok) throw new Error('Duplication failed');
            
            this.showSuccess('Panel duplicated successfully!');
            this.loadPanels();
        } catch (error) {
            console.error('Error duplicating panel:', error);
            this.showError('Failed to duplicate panel.');
        }
    }
    
    async deletePanel(panelId) {
        if (!confirm('Are you sure you want to delete this panel? This action cannot be undone.')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/v1/saved-panels/${panelId}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) throw new Error('Deletion failed');
            
            this.showSuccess('Panel deleted successfully!');
            this.loadPanels();
        } catch (error) {
            console.error('Error deleting panel:', error);
            this.showError('Failed to delete panel.');
        }
    }
    
    // Utility methods
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, function(m) { return map[m]; });
    }
    
    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        
        if (days === 0) return 'today';
        if (days === 1) return 'yesterday';
        if (days < 7) return `${days} days ago`;
        if (days < 30) return `${Math.floor(days / 7)} weeks ago`;
        if (days < 365) return `${Math.floor(days / 30)} months ago`;
        return `${Math.floor(days / 365)} years ago`;
    }
    
    showSuccess(message) {
        // Simple alert for now - could be replaced with a proper toast notification
        alert(message);
    }
    
    showError(message) {
        // Simple alert for now - could be replaced with a proper toast notification
        alert('Error: ' + message);
    }
    
    initializeTimezone() {
        // Initialize timezone display for profile tab
        const userTimeElement = document.getElementById('current-user-time');
        if (userTimeElement) {
            const updateUserTime = () => {
                const now = new Date();
                const timeString = now.toLocaleTimeString();
                userTimeElement.textContent = timeString;
            };
            updateUserTime();
            setInterval(updateUserTime, 1000);
        }
    }
}

// Initialize profile manager when DOM is loaded
export function initializeProfileManager() {
    return new ProfileManager();
}
