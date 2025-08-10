/**
 * Panel Actions Manager
 * Handles all panel CRUD operations, bulk actions, and modal management
 */
class PanelActionsManager {
    constructor(panelLibrary) {
        this.panelLibrary = panelLibrary;
    }

    // Panel action methods
    async openPanel(panelId) {
        console.log('Opening panel:', panelId);
        this.showPanelDetails(panelId);
    }

    async editPanel(panelId) {
        console.log('Editing panel:', panelId);
        // Find the right panel data
        if (!this.panelLibrary.panels || this.panelLibrary.panels.length === 0) {
            this.panelLibrary.showError('No panels available to edit.');
            return;
        }
        const panel = this.panelLibrary.panels.find(p => p.id === panelId);
        if (!panel) {
            this.panelLibrary.showError('Panel not found.');
            return;
        }
        this.openPanelModal(panel);
    }

    async duplicatePanel(panelId) {
        console.log('Duplicating panel:', panelId);
        alert('Duplicate panel functionality coming soon!');
    }

    async sharePanel(panelId) {
        console.log('Sharing panel:', panelId);
        alert('Share panel functionality coming soon!');
    }

    async exportPanel(panelId) {
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
        console.log('Showing version timeline for panel:', panelId);
        if (typeof showVersionTimeline === 'function') {
            showVersionTimeline(panelId);
        }
    }

    async showPanelDetails(panelId) {
        console.log('Showing panel details for:', panelId);
        
        try {
            // Fetch panel data from API
            const response = await fetch(`/api/user/panels/${panelId}`);
            if (!response.ok) throw new Error('Failed to load panel details');
            
            const data = await response.json();
            
            // Extract panel data from the API response wrapper
            const panel = data.panel || data;
            
            // Show the modal with panel data
            this.displayPanelDetailsModal(panel);
            
        } catch (error) {
            console.error('Error loading panel details:', error);
            this.panelLibrary.showMessage('Error loading panel details', 'error');
        }
    }

    displayPanelDetailsModal(panel) {
        const modal = document.getElementById('panel-details-modal');
        const titleElement = document.getElementById('panel-details-title');
        const subtitleElement = document.getElementById('panel-details-subtitle');
        const contentElement = document.getElementById('panel-details-content');
        
        if (!modal || !titleElement || !contentElement) {
            console.error('Panel details modal elements not found');
            return;
        }

        // Update modal title
        titleElement.textContent = panel.name || 'Panel Details';
        subtitleElement.textContent = `Created ${this.formatDate(panel.created_at)} • ${panel.gene_count || 0} genes`;

        // Populate panel details content
        contentElement.innerHTML = this.renderPanelDetailsContent(panel);

        // Set up modal event handlers
        this.setupDetailsModalEventHandlers(panel);

        // Show modal
        modal.classList.remove('hidden');
        modal.style.display = 'block';
        
        // Focus management for accessibility
        setTimeout(() => {
            const closeButton = document.getElementById('close-details-modal');
            if (closeButton) closeButton.focus();
        }, 100);
    }

    renderPanelDetailsContent(panel) {
        const formatDate = this.formatDate.bind(this);
        const formatTags = this.formatTags.bind(this);
        
        return `
            <div class="space-y-6">
                <!-- Panel Overview -->
                <div class="bg-gray-50 rounded-lg p-4">
                    <h4 class="text-lg font-medium text-gray-900 mb-3">Panel Overview</h4>
                    <dl class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                            <dt class="text-sm font-medium text-gray-500">Panel Name</dt>
                            <dd class="mt-1 text-sm text-gray-900">${panel.name || 'N/A'}</dd>
                        </div>
                        <div>
                            <dt class="text-sm font-medium text-gray-500">Version</dt>
                            <dd class="mt-1 text-sm text-gray-900">${panel.version_count || '1'}</dd>
                        </div>
                        <div>
                            <dt class="text-sm font-medium text-gray-500">Total Genes</dt>
                            <dd class="mt-1 text-sm text-gray-900">${panel.gene_count || 0}</dd>
                        </div>
                        <div>
                            <dt class="text-sm font-medium text-gray-500">Created Date</dt>
                            <dd class="mt-1 text-sm text-gray-900">${formatDate(panel.created_at)}</dd>
                        </div>
                        <div>
                            <dt class="text-sm font-medium text-gray-500">Status</dt>
                            <dd class="mt-1">
                                <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full ${this.getStatusBadgeClass(panel.status)}">
                                    ${panel.status || 'ACTIVE'}
                                </span>
                            </dd>
                        </div>
                        <div>
                            <dt class="text-sm font-medium text-gray-500">Visibility</dt>
                            <dd class="mt-1">
                                <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full ${this.getVisibilityBadgeClass(panel.visibility)}">
                                    ${panel.visibility || 'PRIVATE'}
                                </span>
                            </dd>
                        </div>
                    </dl>
                </div>

                <!-- Description -->
                ${panel.description ? `
                <div>
                    <h4 class="text-lg font-medium text-gray-900 mb-3">Description</h4>
                    <div class="bg-white border border-gray-200 rounded-lg p-4">
                        <p class="text-sm text-gray-700 whitespace-pre-wrap">${panel.description}</p>
                    </div>
                </div>
                ` : ''}

                <!-- Tags -->
                ${panel.tags && panel.tags.length > 0 ? `
                <div>
                    <h4 class="text-lg font-medium text-gray-900 mb-3">Tags</h4>
                    <div class="bg-white border border-gray-200 rounded-lg p-4">
                        ${formatTags(panel.tags)}
                    </div>
                </div>
                ` : ''}

                <!-- Source Information -->
                ${panel.source_type || panel.source_reference ? `
                <div class="bg-gray-50 rounded-lg p-4">
                    <h4 class="text-lg font-medium text-gray-900 mb-3">Source Information</h4>
                    <dl class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        ${panel.source_type ? `
                        <div>
                            <dt class="text-sm font-medium text-gray-500">Source Type</dt>
                            <dd class="mt-1 text-sm text-gray-900">${panel.source_type}</dd>
                        </div>
                        ` : ''}
                        ${panel.source_reference ? `
                        <div>
                            <dt class="text-sm font-medium text-gray-500">Source Reference</dt>
                            <dd class="mt-1 text-sm text-gray-900">${panel.source_reference}</dd>
                        </div>
                        ` : ''}
                    </dl>
                </div>
                ` : ''}

                <!-- Gene List -->
                <div>
                    <h4 class="text-lg font-medium text-gray-900 mb-3">
                        Gene List 
                        <span class="text-sm font-normal text-gray-500">(${panel.gene_count || 0} genes)</span>
                    </h4>
                    <div class="bg-white border border-gray-200 rounded-lg">
                        ${this.renderGeneList(panel.genes || [])}
                    </div>
                </div>

                <!-- Technical Information -->
                <div class="bg-gray-50 rounded-lg p-4">
                    <h4 class="text-lg font-medium text-gray-900 mb-3">Technical Information</h4>
                    <dl class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                            <dt class="text-sm font-medium text-gray-500">Panel ID</dt>
                            <dd class="mt-1 text-sm text-gray-900 font-mono">${panel.id || 'N/A'}</dd>
                        </div>
                        <div>
                            <dt class="text-sm font-medium text-gray-500">Last Updated</dt>
                            <dd class="mt-1 text-sm text-gray-900">${formatDate(panel.updated_at)}</dd>
                        </div>
                        <div>
                            <dt class="text-sm font-medium text-gray-500">Last Accessed</dt>
                            <dd class="mt-1 text-sm text-gray-900">${formatDate(panel.last_accessed_at) || 'Never'}</dd>
                        </div>
                        <div>
                            <dt class="text-sm font-medium text-gray-500">Version Count</dt>
                            <dd class="mt-1 text-sm text-gray-900">${panel.version_count || 1}</dd>
                        </div>
                    </dl>
                </div>
            </div>
        `;
    }

    renderGeneList(genes) {
        if (!genes || genes.length === 0) {
            return `
                <div class="p-6 text-center text-gray-500">
                    <i class="fas fa-dna text-2xl mb-2"></i>
                    <p>No genes found in this panel</p>
                </div>
            `;
        }

        // Show first 10 genes by default, with expand option for more
        const displayGenes = genes.slice(0, 10);
        const hasMore = genes.length > 10;

        const renderGeneCard = (gene) => {
            const confidenceBadge = gene.confidence_level ? 
                `<span class="inline-flex px-1.5 py-0.5 text-xs font-medium rounded ${this.getConfidenceBadgeClass(gene.confidence_level)}">${gene.confidence_level}</span>` : '';
            
            const geneName = gene.name ? `<p class="text-xs text-gray-600 mt-1">${gene.name}</p>` : '';
            
            const ensemblInfo = gene.ensembl_id ? 
                `<div class="text-right text-xs text-gray-500"><div class="font-mono">${gene.ensembl_id}</div></div>` : '';

            return `
                <div class="flex items-center justify-between p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <div class="flex-1">
                        <div class="flex items-center">
                            <i class="fas fa-dna mr-2 text-blue-600"></i>
                            <span class="font-medium text-blue-800">${gene.symbol || 'Unknown'}</span>
                        </div>
                        ${geneName}
                        ${confidenceBadge ? `<div class="mt-1">${confidenceBadge}</div>` : ''}
                    </div>
                    ${ensemblInfo}
                </div>
            `;
        };

        const moreGenesSection = hasMore ? `
            <div class="border-t border-gray-200 pt-3">
                <button type="button" 
                        onclick="this.parentElement.parentElement.querySelector('.hidden-genes').classList.toggle('hidden'); this.style.display='none';"
                        class="text-sm text-blue-600 hover:text-blue-800 font-medium">
                    <i class="fas fa-chevron-down mr-1"></i>
                    Show ${genes.length - 10} more genes
                </button>
                
                <div class="hidden-genes hidden mt-3">
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        ${genes.slice(10).map(renderGeneCard).join('')}
                    </div>
                </div>
            </div>
        ` : '';

        return `
            <div class="p-4">
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
                    ${displayGenes.map(renderGeneCard).join('')}
                </div>
                ${moreGenesSection}
            </div>
        `;
    }

    setupDetailsModalEventHandlers(panel) {
        // Close modal handlers
        const closeButton = document.getElementById('close-details-modal');
        const cancelButton = document.getElementById('cancel-details');
        const modal = document.getElementById('panel-details-modal');
        
        const closeModal = () => {
            modal.classList.add('hidden');
            modal.style.display = 'none';
        };

        // Remove existing event listeners to prevent duplicates
        if (closeButton) {
            closeButton.replaceWith(closeButton.cloneNode(true));
            document.getElementById('close-details-modal').addEventListener('click', closeModal);
        }
        
        if (cancelButton) {
            cancelButton.replaceWith(cancelButton.cloneNode(true));
            document.getElementById('cancel-details').addEventListener('click', closeModal);
        }

        // Edit button handler
        const editButton = document.getElementById('edit-panel-from-details');
        if (editButton) {
            editButton.replaceWith(editButton.cloneNode(true));
            document.getElementById('edit-panel-from-details').addEventListener('click', () => {
                closeModal(); // Close details modal first
                setTimeout(() => {
                    this.openPanelModal(panel); // Open edit modal with panel data
                }, 150); // Small delay for smooth transition
            });
        }

        // Click outside to close
        modal.onclick = (e) => {
            if (e.target === modal) {
                closeModal();
            }
        };

        // Escape key to close
        const escapeHandler = (e) => {
            if (e.key === 'Escape') {
                closeModal();
                document.removeEventListener('keydown', escapeHandler);
            }
        };
        document.addEventListener('keydown', escapeHandler);
    }

    formatDate(dateString) {
        if (!dateString) return 'N/A';
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        } catch (e) {
            return 'Invalid Date';
        }
    }

    formatTags(tags) {
        if (!tags || tags.length === 0) return '<span class="text-gray-500">No tags</span>';
        
        return tags.map(tag => `
            <span class="inline-flex items-center px-2.5 py-1.5 rounded-md text-xs font-medium bg-gray-100 text-gray-800 border border-gray-200 mr-2 mb-2">
                <i class="fas fa-tag mr-1"></i>
                ${tag}
            </span>
        `).join('');
    }

    // Modal management
    async loadPanelGenes(panelId) {
        try {
            const response = await fetch(`/api/user/panels/${panelId}`);
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

    openPanelModal(panelData = null) {
        console.log("openPanelModal");
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
        
        this.panelLibrary.panelModal?.classList.remove('hidden');
    }
    
    closePanelModal() {
        this.panelLibrary.panelModal?.classList.add('hidden');
        this.clearForm();
    }

    closePanelDetailsModal() {
        this.panelLibrary.panelDetailsModal?.classList.add('hidden');
        this.panelLibrary.panelId = null; // Reset panel ID
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
        console.log("clearForm");
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
            id: panelId || null,
            name: document.getElementById('panel-name')?.value || '',
            description: document.getElementById('panel-description')?.value || '',
            tags: this.panelLibrary.parseTags(document.getElementById('panel-tags')?.value || ''),
            status: document.getElementById('panel-status')?.value || 'ACTIVE',
            visibility: document.getElementById('panel-visibility')?.value || 'PRIVATE',
            genes: this.panelLibrary.parseGenes(document.getElementById('panel-genes')?.value || '')
        };
        
        try {           
            const response = await fetch('/api/user/panels', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Failed to save panel');
            }
            
            this.panelLibrary.showSuccess(isEdit ? 'Panel updated successfully!' : 'Panel created successfully!');
            this.closePanelModal();
            this.panelLibrary.loadPanels();
        } catch (error) {
            console.error('Error saving panel:', error);
            this.panelLibrary.showError(error.message || 'Failed to save panel. Please try again.');
        }
    }

    // Bulk actions
    async bulkDeletePanels() {
        if (this.panelLibrary.selectedPanels.size === 0) return;
        console.log('Bulk deleting panels:', Array.from(this.panelLibrary.selectedPanels));
    }

    async bulkExportPanels() {
        if (this.panelLibrary.selectedPanels.size === 0) return;
        console.log('Bulk exporting panels:', Array.from(this.panelLibrary.selectedPanels));
    }

    async bulkSharePanels() {
        if (this.panelLibrary.selectedPanels.size === 0) return;
        console.log('Bulk sharing panels:', Array.from(this.panelLibrary.selectedPanels));
    }

    deleteSelected() {
        const selectedIds = Array.from(this.panelLibrary.selectedPanels);
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

    compareSelected() {
        const selectedIds = Array.from(this.panelLibrary.selectedPanels);
        if (selectedIds.length !== 2) {
            alert('Please select exactly 2 panels to compare');
            return;
        }
        // Implementation for comparison
        console.log('Comparing panels:', selectedIds);
    }

    exportSelected() {
        const selectedIds = Array.from(this.panelLibrary.selectedPanels);
        if (selectedIds.length === 0) {
            alert('Please select panels to export');
            return;
        }
        // Implementation for export
        console.log('Exporting panels:', selectedIds);
    }

    // UI helpers
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

    toggleActionsMenu() {
        const menu = document.getElementById('actions-menu');
        if (menu) {
            menu.classList.toggle('hidden');
        }
    }

    // Utility methods for styling badges
    getStatusBadgeClass(status) {
        switch (status?.toUpperCase()) {
            case 'ACTIVE':
                return 'bg-green-100 text-green-800';
            case 'DRAFT':
                return 'bg-yellow-100 text-yellow-800';
            case 'ARCHIVED':
                return 'bg-gray-100 text-gray-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    }

    getVisibilityBadgeClass(visibility) {
        switch (visibility?.toUpperCase()) {
            case 'PUBLIC':
                return 'bg-blue-100 text-blue-800';
            case 'SHARED':
                return 'bg-purple-100 text-purple-800';
            case 'PRIVATE':
                return 'bg-gray-100 text-gray-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    }

    getConfidenceBadgeClass(confidence) {
        switch (confidence?.toLowerCase()) {
            case 'high':
                return 'bg-green-100 text-green-800';
            case 'medium':
                return 'bg-yellow-100 text-yellow-800';
            case 'low':
                return 'bg-red-100 text-red-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    }

    formatTags(tags) {
        if (!tags || !Array.isArray(tags) || tags.length === 0) {
            return '<span class="text-gray-500 text-sm">No tags</span>';
        }
        
        return tags.map(tag => `
            <span class="inline-flex items-center px-2.5 py-1.5 rounded-md text-xs font-medium bg-gray-100 text-gray-800 border border-gray-200 mr-2 mb-2">
                <i class="fas fa-tag mr-1"></i>
                ${tag}
            </span>
        `).join('');
    }
}
