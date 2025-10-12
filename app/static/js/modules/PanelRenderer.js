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
                        <i class="fas ${sharingIcon}" title="${visibility}"></i>
                    </div>
                </div>
                
                <div class="panel-thumbnail" onclick="panelLibrary.openPanel(${panel.id})">
                    ${thumbnail}
                </div>
                
                <div class="panel-info">
                    <h3 class="panel-title" title="${panel.name}">${this.panelLibrary.truncateText(panel.name, 30)}</h3>
                    <p class="panel-description">${this.panelLibrary.truncateText(panel.description || 'No description available', 50)}</p>
                    
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
                            <span>${this.panelLibrary.formatDate(panel.updated_at || panel.created_at)}</span>
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
                    <button class="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500" onclick="panelLibrary.showPanelDetails(${panel.id})">
                        <i class="fas fa-info-circle"></i> Details
                    </button>
                    <button class="px-3 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-md bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500" onclick="panelLibrary.showVersionTimeline(${panel.id})">
                        <i class="fas fa-history"></i> History
                    </button>
                    <div class="dropdown" z-1000>
                        <button class="px-2 py-1 border border-gray-300 text-gray-700 text-xs font-medium rounded bg-white hover:bg-gray-50 focus:outline-none focus:ring-1 focus:ring-blue-500" onclick="panelLibrary.toggleDropdown(this)">
                            <i class="fas fa-ellipsis-v"></i>
                        </button>
                        <ul class="dropdown-menu hidden" z-1000>
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
        const isSelected = this.panelLibrary.selectedPanels.has(panel.id);
        const status = this.panelLibrary.backendToFrontend(panel.status);
        const visibility = this.panelLibrary.backendToFrontend(panel.visibility);
        const statusColor = this.getStatusColor(status);
        const sharingIcon = this.getSharingIcon(visibility);

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
                            <p class="panel-description-short">${this.panelLibrary.truncateText(panel.description || '', 40)}</p>
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
                    <span class="updated-date">${this.panelLibrary.formatDate(panel.updated_at)}</span>
                    <small class="version-info">v${panel.version_count}</small>
                </div>
                <div class="list-column list-sharing">
                    <i class="fas ${sharingIcon}" title="${panel.visibility}"></i>
                </div>
                <div class="list-column list-actions">
                    <button class="px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium rounded focus:outline-none focus:ring-1 focus:ring-blue-500" onclick="panelLibrary.showPanelDetails(${panel.id})">
                        Details
                    </button>
                    <button class="px-2 py-1 border border-gray-300 text-gray-700 text-xs font-medium rounded bg-white hover:bg-gray-50 focus:outline-none focus:ring-1 focus:ring-blue-500 ml-1" onclick="panelLibrary.showVersionTimeline(${panel.id})">
                        History
                    </button>
                    <div class="dropdown relative z-1000">
                        <button class="px-2 py-1 border border-gray-300 text-gray-700 text-xs font-medium rounded bg-white hover:bg-gray-50 focus:outline-none focus:ring-1 focus:ring-blue-500" onclick="panelLibrary.toggleDropdown(this)">
                            <i class="fas fa-ellipsis-v"></i>
                        </button>
                        <ul class="dropdown-menu absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200 hidden z-1000">
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
}
