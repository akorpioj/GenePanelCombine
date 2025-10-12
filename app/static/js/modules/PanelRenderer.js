/**
 * Panel Renderer Module
 * Handles all panel rendering logic (grid view, list view, cards, etc.)
 */
class PanelRenderer {
    constructor(panelLibrary) {
        this.panelLibrary = panelLibrary;
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
                    <div class="list-column list-sharing">Visibility</div>
                    <div class="list-column list-actions">Actions</div>
                </div>
                ${panels.map(panel => this.renderPanelRow(panel)).join('')}
            </div>
        `;
    }

    renderPanelCard(panel) {
        const isSelected = this.panelLibrary.selectedPanels.has(panel.id);
        const thumbnail = this.generatePanelThumbnail(panel);
        const status = this.panelLibrary.backendToFrontend(panel.status);
        const visibility = this.panelLibrary.backendToFrontend(panel.visibility);
        const statusColor = this.getStatusColor(status);
        const sharingIcon = this.getSharingIcon(visibility);
        console.log("tags: ", panel.tags);

        // Generate tags HTML
        const tagsHtml = (panel.tags || []).slice(0, 3).map(tag => 
            `<span class="tag">${tag}</span>`
        ).join('') + ((panel.tags || []).length > 3 ? `<span class="tag-more">+${(panel.tags || []).length - 3}</span>` : '');

        // Use external template if available, otherwise use inline template
        if (window.panelCardTemplate) {
            return window.panelCardTemplate
                .replace(/{{SELECTED_CLASS}}/g, isSelected ? 'selected' : '')
                .replace(/{{PANEL_ID}}/g, panel.id)
                .replace(/{{CHECKED}}/g, isSelected ? 'checked' : '')
                .replace(/{{STATUS_COLOR}}/g, statusColor)
                .replace(/{{SHARING_ICON}}/g, sharingIcon)
                .replace(/{{VISIBILITY}}/g, visibility)
                .replace(/{{THUMBNAIL}}/g, thumbnail)
                .replace(/{{PANEL_NAME_FULL}}/g, panel.name)
                .replace(/{{PANEL_NAME}}/g, this.panelLibrary.truncateText(panel.name, 30))
                .replace(/{{PANEL_DESCRIPTION}}/g, this.panelLibrary.truncateText(panel.description || 'No description available', 50))
                .replace(/{{GENE_COUNT}}/g, panel.gene_count || 0)
                .replace(/{{VERSION_COUNT}}/g, panel.version_count || 1)
                .replace(/{{UPDATED_DATE}}/g, this.panelLibrary.formatDate(panel.updated_at || panel.created_at))
                .replace(/{{OWNER_USERNAME}}/g, panel.owner ? panel.owner.username : 'Unknown')
                .replace(/{{TAGS}}/g, tagsHtml);
        }
    }

    renderPanelRow(panel) {
        const isSelected = this.panelLibrary.selectedPanels.has(panel.id);
        const status = this.panelLibrary.backendToFrontend(panel.status);
        const visibility = this.panelLibrary.backendToFrontend(panel.visibility);
        const statusColor = this.getStatusColor(status);
        const sharingIcon = this.getSharingIcon(visibility);

        // Use external template if available, otherwise use inline template
        if (window.panelRowTemplate) {
            return window.panelRowTemplate
                .replace(/{{SELECTED_CLASS}}/g, isSelected ? 'selected' : '')
                .replace(/{{PANEL_ID}}/g, panel.id)
                .replace(/{{CHECKED}}/g, isSelected ? 'checked' : '')
                .replace(/{{STATUS_COLOR}}/g, statusColor)
                .replace(/{{PANEL_NAME}}/g, panel.name)
                .replace(/{{PANEL_DESCRIPTION}}/g, this.panelLibrary.truncateText(panel.description || '', 40))
                .replace(/{{GENE_COUNT}}/g, panel.gene_count)
                .replace(/{{SOURCE_TYPE}}/g, panel.source_type)
                .replace(/{{UPDATED_DATE}}/g, this.panelLibrary.formatDate(panel.updated_at))
                .replace(/{{VERSION_COUNT}}/g, panel.version_count)
                .replace(/{{SHARING_ICON}}/g, sharingIcon)
                .replace(/{{VISIBILITY}}/g, panel.visibility);
        }
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
        const geneCount = Math.min(panel.gene_count, 1000);
        const cellCount = Math.min(geneCount, 1000);
        
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
}
