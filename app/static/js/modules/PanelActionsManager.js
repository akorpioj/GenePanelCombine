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
        if (typeof showPanelDetails === 'function') {
            showPanelDetails(panelId);
        }
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
}
