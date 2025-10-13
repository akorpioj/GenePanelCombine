/**
 * Panel Actions Manager
 * Handles all panel CRUD operations, bulk actions, and modal management
 */
class PanelActionsManager {
    constructor(panelLibrary) {
        this.panelLibrary = panelLibrary;
        this.panelOverviewTemplate = null;
        this.panelTechnicalInfoTemplate = null;
        this.panelDetailsSectionsTemplate = null;
        this.loadTemplates();
    }

    async loadTemplates() {
        // Load panel overview template
        try {
            const response = await fetch('/static/partials/_panel_overview.html');
            if (response.ok) {
                this.panelOverviewTemplate = await response.text();
                console.log('Panel overview template loaded successfully');
            } else {
                console.warn('Failed to load panel overview template, will use inline fallback');
            }
        } catch (error) {
            console.warn('Error loading panel overview template:', error);
        }

        // Load panel technical info template
        try {
            const response = await fetch('/static/partials/_panel_technical_info.html');
            if (response.ok) {
                this.panelTechnicalInfoTemplate = await response.text();
                console.log('Panel technical info template loaded successfully');
            } else {
                console.warn('Failed to load panel technical info template, will use inline fallback');
            }
        } catch (error) {
            console.warn('Error loading panel technical info template:', error);
        }

        // Load panel details sections template
        try {
            const response = await fetch('/static/partials/_panel_details_sections.html');
            if (response.ok) {
                this.panelDetailsSectionsTemplate = await response.text();
                console.log('Panel details sections template loaded successfully');
            } else {
                console.warn('Failed to load panel details sections template, will use inline fallback');
            }
        } catch (error) {
            console.warn('Error loading panel details sections template:', error);
        }
    }

    // Panel action methods
    async openPanel(panelId) {
        console.log('Opening panel:', panelId);
        this.showPanelDetails(panelId);
    }

    async editPanel(panelId) {
        console.log('Editing panel:', panelId);
        
        try {
            // Fetch fresh panel data from API to ensure we have complete information
            const response = await fetch(`/api/user/panels/${panelId}`);
            if (!response.ok) throw new Error('Failed to load panel data');
            
            const data = await response.json();
            
            // Extract panel data from the API response wrapper
            const panel = data.panel || data;
            
            // Open the edit modal with complete panel data
            await this.openPanelModal(panel);
            
        } catch (error) {
            console.error('Error loading panel data for editing:', error);
            this.panelLibrary.showError('Error loading panel data');
        }
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
        
        try {
            // Send DELETE request to API
            const response = await fetch(`/api/user/panels/${panelId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Failed to delete panel');
            }
            
            // Success - show message and refresh panel list
            this.panelLibrary.showSuccess('Panel deleted successfully!');
            
            // Remove from selected panels if it was selected
            this.panelLibrary.selectedPanels.delete(panelId);
            
            // Refresh the panel list to reflect the deletion
            await this.panelLibrary.loadPanels();
            
            // Close any open modals that might be showing this panel
            this.closePanelModal();
            this.closePanelDetailsModal();
            
        } catch (error) {
            console.error('Error deleting panel:', error);
            this.panelLibrary.showError(error.message || 'Failed to delete panel. Please try again.');
        }
    }

    async showVersionTimeline(panelId) {
        console.log('Showing version timeline for panel:', panelId);
        alert('Showing version timeline for panel functionality coming soon!');
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
            this.panelLibrary.showError('Error loading panel details');
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

    renderPanelOverview(panel) {
        // Use external template if available, otherwise fallback to inline
        if (this.panelOverviewTemplate) {
            return this.panelOverviewTemplate
                .replace(/\{\{PANEL_NAME\}\}/g, panel.name || 'N/A')
                .replace(/\{\{VERSION_COUNT\}\}/g, panel.version_count || '1')
                .replace(/\{\{GENE_COUNT\}\}/g, panel.gene_count || 0)
                .replace(/\{\{CREATED_DATE\}\}/g, this.formatDate(panel.created_at))
                .replace(/\{\{STATUS_BADGE_CLASS\}\}/g, this.getStatusBadgeClass(panel.status))
                .replace(/\{\{STATUS\}\}/g, this.panelLibrary.backendToFrontend(panel.status || 'ACTIVE'))
                .replace(/\{\{VISIBILITY_BADGE_CLASS\}\}/g, this.getVisibilityBadgeClass(panel.visibility))
                .replace(/\{\{VISIBILITY\}\}/g, this.panelLibrary.backendToFrontend(panel.visibility || 'PRIVATE'));
        }        
    }

    renderPanelTechnicalInfo(panel) {
        // Use external template if available, otherwise fallback to inline
        if (this.panelTechnicalInfoTemplate) {
            return this.panelTechnicalInfoTemplate
                .replace(/\{\{PANEL_ID\}\}/g, panel.id || 'N/A')
                .replace(/\{\{LAST_UPDATED\}\}/g, this.formatDate(panel.updated_at))
                .replace(/\{\{LAST_ACCESSED\}\}/g, this.formatDate(panel.last_accessed_at) || 'Never')
                .replace(/\{\{VERSION_COUNT\}\}/g, panel.version_count || 1);
        }
    }

    renderPanelDetailsSections(panel) {
        const formatTags = this.formatTags.bind(this);
        
        // Render individual sections
        const descriptionSection = panel.description ? `
            <div>
                <h4 class="text-lg font-medium text-gray-900 mb-3">Description</h4>
                <div class="bg-white border border-gray-200 rounded-lg p-4">
                    <p class="text-sm text-gray-700 whitespace-pre-wrap">${panel.description}</p>
                </div>
            </div>
        ` : '';

        const tagsSection = panel.tags && panel.tags.length > 0 ? `
            <div>
                <h4 class="text-lg font-medium text-gray-900 mb-3">Tags</h4>
                <div class="bg-white border border-gray-200 rounded-lg p-4">
                    ${formatTags(panel.tags)}
                </div>
            </div>
        ` : '';

        const sourceInfoSection = panel.source_type || panel.source_reference ? `
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
        ` : '';

        const geneListContent = this.renderGeneList(panel.genes || []);

        // Use external template if available
        if (this.panelDetailsSectionsTemplate) {
            return this.panelDetailsSectionsTemplate
                .replace(/\{\{DESCRIPTION_SECTION\}\}/g, descriptionSection)
                .replace(/\{\{TAGS_SECTION\}\}/g, tagsSection)
                .replace(/\{\{SOURCE_INFO_SECTION\}\}/g, sourceInfoSection)
                .replace(/\{\{GENE_COUNT\}\}/g, panel.gene_count || 0)
                .replace(/\{\{GENE_LIST_CONTENT\}\}/g, geneListContent);
        }
    }

    renderPanelDetailsContent(panel) {
        // Render sections from templates
        const panelOverviewHtml = this.renderPanelOverview(panel);
        const panelDetailsSectionsHtml = this.renderPanelDetailsSections(panel);
        const panelTechnicalInfoHtml = this.renderPanelTechnicalInfo(panel);
        
        return `
            <div class="space-y-6">
                ${panelOverviewHtml}
                ${panelDetailsSectionsHtml}
                ${panelTechnicalInfoHtml}
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
            document.getElementById('edit-panel-from-details').addEventListener('click', async () => {
                closeModal(); // Close details modal first
                setTimeout(async () => {
                    await this.openPanelModal(panel); // Open edit modal with panel data
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

    // Modal management
    async loadPanelGenes(panelId) {
        try {
            const response = await fetch(`/api/user/panels/${panelId}`);
            if (!response.ok) throw new Error('Failed to load panel genes');
            
            const data = await response.json();
            const panel = data.panel || data;
            
            console.log('Panel data for genes:', panel); // Debug log
            
            if (panel.genes && Array.isArray(panel.genes)) {
                const genesText = panel.genes.map(gene => gene.gene_symbol || gene.symbol || gene).join('\n');
                const panelGenes = document.getElementById('panel-genes');
                if (panelGenes) {
                    panelGenes.value = genesText;
                    console.log(`Loaded ${panel.genes.length} genes for panel ${panelId}`);
                }
            } else {
                console.log('No genes found in panel data:', panel);
                const panelGenes = document.getElementById('panel-genes');
                if (panelGenes) panelGenes.value = '';
            }
        } catch (error) {
            console.error('Error loading panel genes:', error);
            // Don't fail silently - show a message to the user
            const panelGenes = document.getElementById('panel-genes');
            if (panelGenes) panelGenes.value = '# Error loading genes\n# Please try again or contact support';
        }
    }

    async openPanelModal(panelData = null) {
        console.log("openPanelModal");
        const modalTitle = document.getElementById('modal-title');
        const panelId = document.getElementById('panel-id');
        
        if (panelData) {
            if (modalTitle) modalTitle.textContent = 'Edit Panel';
            if (panelId) panelId.value = panelData.id;
            await this.populateForm(panelData); // Wait for form population to complete
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
    
    async populateForm(panelData) {
        const panelName = document.getElementById('panel-name');
        const panelDescription = document.getElementById('panel-description');
        const panelTags = document.getElementById('panel-tags');
        const panelStatus = document.getElementById('panel-status');
        const panelVisibility = document.getElementById('panel-visibility');
        
        console.log('Populating form with panel data:', panelData); // Debug log
        
        if (panelName) panelName.value = panelData.name || '';
        if (panelDescription) panelDescription.value = panelData.description || '';
        if (panelTags) {
            if (Array.isArray(panelData.tags)) {
                panelTags.value = panelData.tags.map(tag => {
                    const cleanTag = String(tag).replace(/^[{\s]+|[}\s]+$/g, '').trim();
                    return `${cleanTag}`;
                }).join(', ');
            } else if (typeof panelData.tags === 'string') {
                panelTags.value = panelData.tags;
            } else {
                panelTags.value = '';
            }
        }
        if (panelStatus) {
            panelStatus.value = this.panelLibrary.backendToFrontend(panelData.status || 'ACTIVE');
            console.log('Set status to:', panelData.status || 'ACTIVE');
        }
        if (panelVisibility) {
            panelVisibility.value = this.panelLibrary.backendToFrontend(panelData.visibility || 'PRIVATE');
            console.log('Set visibility to:', panelData.visibility || 'PRIVATE');
        }
        
        // Load genes if editing - if genes are already in panelData, use them directly
        if (panelData.id) {
            if (panelData.genes && Array.isArray(panelData.genes)) {
                // Use genes from the already-fetched panel data
                const genesText = panelData.genes.map(gene => gene.gene_symbol || gene.symbol || gene).join('\n');
                const panelGenes = document.getElementById('panel-genes');
                if (panelGenes) {
                    panelGenes.value = genesText;
                    console.log(`Populated ${panelData.genes.length} genes for panel ${panelData.id} from existing data`);
                }
            } else {
                // Fallback to fetching genes separately if not included in panel data
                await this.loadPanelGenes(panelData.id);
            }
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
        // Prevent double submission
        if (this._saving) {
            console.log('Save already in progress, ignoring duplicate call');
            return;
        }
        
        this._saving = true;
        console.log('Starting savePanelData()');
        
        // Get button references
        const saveButton = document.getElementById('save-panel');
        const cancelButton = document.getElementById('cancel-panel');
        
        // Store original button content
        const originalSaveContent = saveButton?.innerHTML;
        
        // Disable buttons and update text
        if (saveButton) {
            saveButton.disabled = true;
            saveButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Saving...';
            saveButton.classList.add('opacity-75', 'cursor-not-allowed');
        }
        if (cancelButton) {
            cancelButton.disabled = true;
            cancelButton.classList.add('opacity-50', 'cursor-not-allowed');
        }
        
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
            console.log('Saving panel data:', data);
            
            // Use different endpoints for create vs update
            const url = isEdit ? `/api/user/panels/${panelId}` : '/api/user/panels';
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
                console.log(errorData);
                throw new Error(errorData.message || 'Failed to save panel');
            }
            
            this.panelLibrary.showSuccess(isEdit ? 'Panel updated successfully!' : 'Panel created successfully!');
            this.closePanelModal();
            this.panelLibrary.loadPanels();
        } catch (error) {
            console.error('Error saving panel:', error);
            this.panelLibrary.showError(error.message || 'Failed to save panel. Please try again.');
        } finally {
            // Re-enable buttons and restore text
            if (saveButton) {
                saveButton.disabled = false;
                saveButton.innerHTML = originalSaveContent;
                saveButton.classList.remove('opacity-75', 'cursor-not-allowed');
            }
            if (cancelButton) {
                cancelButton.disabled = false;
                cancelButton.classList.remove('opacity-50', 'cursor-not-allowed');
            }
            
            this._saving = false;
            console.log('Finished savePanelData()');
        }
    }

    // Bulk actions
    async bulkDeletePanels() {
        if (this.panelLibrary.selectedPanels.size === 0) return;
        
        const selectedIds = Array.from(this.panelLibrary.selectedPanels);
        console.log('Bulk deleting panels:', selectedIds);
        
        try {
            let deletePromises = selectedIds.map(async (panelId) => {
                const response = await fetch(`/api/user/panels/${panelId}`, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(`Failed to delete panel ${panelId}: ${errorData.message || 'Unknown error'}`);
                }
                
                return panelId;
            });
            
            // Wait for all deletions to complete
            const deletedIds = await Promise.all(deletePromises);
            
            // Clear selected panels
            this.panelLibrary.selectedPanels.clear();
            
            // Success - show message and refresh panel list
            this.panelLibrary.showSuccess(`Successfully deleted ${deletedIds.length} panels!`);
            
            // Refresh the panel list to reflect the deletions
            await this.panelLibrary.loadPanels();
            
        } catch (error) {
            console.error('Error bulk deleting panels:', error);
            this.panelLibrary.showError(error.message || 'Failed to delete some panels. Please try again.');
            
            // Refresh the panel list in case some deletions succeeded
            await this.panelLibrary.loadPanels();
        }
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
        
        // Delete panels one by one
        this.bulkDeletePanels();
    }

    compareSelected() {
        const selectedIds = Array.from(this.panelLibrary.selectedPanels);
        if (selectedIds.length !== 2) {
            alert('Please select exactly 2 panels to compare');
            return;
        }
        // Coming soon functionality
        alert('Panel comparison feature is coming soon!');
        console.log('Comparing panels:', selectedIds);
    }

    exportSelected() {
        const selectedIds = Array.from(this.panelLibrary.selectedPanels);
        if (selectedIds.length === 0) {
            alert('Please select panels to export');
            return;
        }
        // Coming soon functionality
        alert('Panel export feature is coming soon!');
        console.log('Exporting panels:', selectedIds);
    }

    // UI helpers
    toggleDropdown(button) {
        const dropdown = button.parentElement;
        const menu = dropdown.querySelector('.dropdown-menu');
        const panelCard = button.closest('.panel-card');
        
        // Close all other dropdowns first and remove dropdown-open class
        document.querySelectorAll('.dropdown-menu').forEach(otherMenu => {
            if (otherMenu !== menu) {
                otherMenu.classList.add('hidden');
                const otherPanelCard = otherMenu.closest('.panel-card');
                if (otherPanelCard) {
                    otherPanelCard.classList.remove('dropdown-open');
                }
            }
        });
        
        // Toggle this dropdown
        const isHidden = menu.classList.contains('hidden');
        menu.classList.toggle('hidden');
        
        // Manage panel card z-index for dropdown visibility
        if (panelCard) {
            if (isHidden) {
                // Dropdown is being opened
                panelCard.classList.add('dropdown-open');
            } else {
                // Dropdown is being closed
                panelCard.classList.remove('dropdown-open');
            }
        }
        
        // Close dropdown when clicking outside
        if (!menu.classList.contains('hidden')) {
            const closeDropdown = (e) => {
                if (!dropdown.contains(e.target)) {
                    menu.classList.add('hidden');
                    if (panelCard) {
                        panelCard.classList.remove('dropdown-open');
                    }
                    document.removeEventListener('click', closeDropdown);
                    document.removeEventListener('keydown', handleEscape);
                }
            };
            
            const handleEscape = (e) => {
                if (e.key === 'Escape') {
                    menu.classList.add('hidden');
                    if (panelCard) {
                        panelCard.classList.remove('dropdown-open');
                    }
                    document.removeEventListener('click', closeDropdown);
                    document.removeEventListener('keydown', handleEscape);
                }
            };
            
            setTimeout(() => {
                document.addEventListener('click', closeDropdown);
                document.addEventListener('keydown', handleEscape);
            }, 0);
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
            case 'DELETED':
                return 'bg-red-100 text-red-800';
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
        
        return tags.map(tag => {
            // Clean up tag by removing leading/trailing curly braces and whitespace
            const cleanTag = String(tag).replace(/^[{\s]+|[}\s]+$/g, '').trim();
            
            return `
                <span class="inline-flex items-center px-2.5 py-1.5 rounded-md text-xs font-medium bg-gray-100 text-gray-800 border border-gray-200 mr-2 mb-2">
                    <i class="fas fa-tag mr-1"></i>
                    ${cleanTag}
                </span>
            `;
        }).join('');
    }
}
