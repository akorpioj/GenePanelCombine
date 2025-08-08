/**
 * Version Timeline Component
 * Visual timeline showing panel evolution with branch visualization
 */

class VersionTimeline {
    constructor(panelId) {
        this.panelId = panelId;
        this.versions = [];
        this.branches = [];
        this.tags = [];
        this.timeline = null;
        this.selectedVersions = [];
        
        this.init();
    }

    async init() {
        await this.loadVersionData();
        this.renderTimeline();
        this.setupEventListeners();
    }

    async loadVersionData() {
        try {
            // Load versions
            const versionsResponse = await fetch(`/api/user/panels/${this.panelId}/versions`);
            if (versionsResponse.ok) {
                this.versions = await versionsResponse.json();
            }

            // Load branches (if available) - disabled for now
            try {
                // const branchesResponse = await fetch(`/api/v1/version-control/panels/${this.panelId}/branches`);
                // if (branchesResponse.ok) {
                //     this.branches = await branchesResponse.json();
                // }
                this.branches = [];
            } catch (e) {
                console.log('Branches not available:', e);
            }

            // Load tags (if available) - disabled for now
            try {
                // const tagsResponse = await fetch(`/api/v1/version-control/panels/${this.panelId}/tags`);
                // if (tagsResponse.ok) {
                //     this.tags = await tagsResponse.json();
                // }
                this.tags = [];
            } catch (e) {
                console.log('Tags not available:', e);
            }

        } catch (error) {
            console.error('Error loading version data:', error);
            throw error;
        }
    }

    renderTimeline() {
        const container = document.getElementById('version-timeline-container');
        if (!container) return;

        const timelineHtml = `
            <div class="version-timeline">
                <div class="timeline-header">
                    <h4>Version History</h4>
                    <div class="timeline-controls">
                        <button class="btn btn-sm btn-outline-primary" onclick="versionTimeline.compareSelected()">
                            <i class="fas fa-code-compare"></i> Compare Selected
                        </button>
                        <button class="btn btn-sm btn-outline-secondary" onclick="versionTimeline.exportTimeline()">
                            <i class="fas fa-download"></i> Export Timeline
                        </button>
                    </div>
                </div>
                
                <div class="timeline-legend">
                    <div class="legend-item">
                        <span class="legend-dot main-branch"></span>
                        <span>Main Branch</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-dot feature-branch"></span>
                        <span>Feature Branch</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-dot merge-commit"></span>
                        <span>Merge Commit</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-tag"></span>
                        <span>Tagged Version</span>
                    </div>
                </div>
                
                <div class="timeline-content">
                    ${this.renderTimelineGraph()}
                </div>
                
                <div class="timeline-details">
                    ${this.renderVersionDetails()}
                </div>
            </div>
        `;

        container.innerHTML = timelineHtml;
    }

    renderTimelineGraph() {
        if (this.versions.length === 0) {
            return '<div class="timeline-empty">No versions found</div>';
        }

        // Sort versions by creation date
        const sortedVersions = [...this.versions].sort((a, b) => 
            new Date(b.created_at) - new Date(a.created_at)
        );

        // Create timeline nodes
        let timelineHtml = '<div class="timeline-graph">';
        
        // Create branch visualization
        const branchPaths = this.calculateBranchPaths(sortedVersions);
        
        timelineHtml += '<svg class="timeline-svg" width="100%" height="' + (sortedVersions.length * 80 + 100) + '">';
        
        // Draw branch lines
        timelineHtml += this.renderBranchLines(branchPaths);
        
        timelineHtml += '</svg>';
        
        // Timeline nodes
        timelineHtml += '<div class="timeline-nodes">';
        
        sortedVersions.forEach((version, index) => {
            const isSelected = this.selectedVersions.includes(version.id);
            const versionTags = this.getVersionTags(version.id);
            const branchInfo = this.getVersionBranch(version.id);
            
            timelineHtml += `
                <div class="timeline-node ${isSelected ? 'selected' : ''}" 
                     data-version-id="${version.id}"
                     style="top: ${index * 80 + 40}px;">
                     
                    <div class="node-selector">
                        <input type="checkbox" 
                               onchange="versionTimeline.toggleVersionSelection(${version.id})"
                               ${isSelected ? 'checked' : ''} />
                    </div>
                    
                    <div class="node-circle ${this.getNodeType(version, branchInfo)}"
                         onclick="versionTimeline.selectVersion(${version.id})">
                        <span class="node-version">v${version.version_number}</span>
                    </div>
                    
                    <div class="node-content">
                        <div class="node-header">
                            <h5 class="node-title">${version.comment || 'Version ' + version.version_number}</h5>
                            <div class="node-meta">
                                <span class="node-author">${version.created_by?.username || 'Unknown'}</span>
                                <span class="node-date">${this.formatDate(version.created_at)}</span>
                            </div>
                        </div>
                        
                        <div class="node-details">
                            <div class="detail-item">
                                <i class="fas fa-dna"></i>
                                <span>${version.gene_count} genes</span>
                            </div>
                            ${version.size_bytes ? `
                                <div class="detail-item">
                                    <i class="fas fa-weight"></i>
                                    <span>${this.formatFileSize(version.size_bytes)}</span>
                                </div>
                            ` : ''}
                            ${branchInfo ? `
                                <div class="detail-item">
                                    <i class="fas fa-code-branch"></i>
                                    <span>${branchInfo.name}</span>
                                </div>
                            ` : ''}
                        </div>
                        
                        ${versionTags.length > 0 ? `
                            <div class="node-tags">
                                ${versionTags.map(tag => `
                                    <span class="version-tag tag-${tag.tag_type.toLowerCase()}">
                                        <i class="fas fa-tag"></i>
                                        ${tag.tag_name}
                                    </span>
                                `).join('')}
                            </div>
                        ` : ''}
                        
                        <div class="node-actions">
                            <button class="btn btn-sm btn-outline-primary" 
                                    onclick="versionTimeline.viewVersion(${version.id})">
                                <i class="fas fa-eye"></i> View
                            </button>
                            <button class="btn btn-sm btn-outline-secondary" 
                                    onclick="versionTimeline.restoreVersion(${version.id})">
                                <i class="fas fa-undo"></i> Restore
                            </button>
                            <button class="btn btn-sm btn-outline-info" 
                                    onclick="versionTimeline.downloadVersion(${version.id})">
                                <i class="fas fa-download"></i> Download
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });
        
        timelineHtml += '</div></div>';
        
        return timelineHtml;
    }

    calculateBranchPaths(versions) {
        // Simplified branch path calculation
        const paths = [];
        const mainBranch = { x: 50, versions: [] };
        
        versions.forEach((version, index) => {
            const branchInfo = this.getVersionBranch(version.id);
            if (!branchInfo || branchInfo.name === 'main') {
                mainBranch.versions.push({ version, y: index * 80 + 40 });
            }
        });
        
        paths.push(mainBranch);
        return paths;
    }

    renderBranchLines(branchPaths) {
        let linesHtml = '';
        
        branchPaths.forEach(branch => {
            if (branch.versions.length > 1) {
                for (let i = 0; i < branch.versions.length - 1; i++) {
                    const current = branch.versions[i];
                    const next = branch.versions[i + 1];
                    
                    linesHtml += `
                        <line x1="${branch.x}" y1="${current.y}" 
                              x2="${branch.x}" y2="${next.y}" 
                              stroke="#007bff" stroke-width="3" />
                    `;
                }
            }
        });
        
        return linesHtml;
    }

    renderVersionDetails() {
        return `
            <div class="version-details-panel">
                <div class="details-header">
                    <h5>Version Details</h5>
                    <p class="text-muted">Select a version to see detailed information</p>
                </div>
                <div id="version-details-content">
                    <!-- Details will be populated when a version is selected -->
                </div>
            </div>
        `;
    }

    getNodeType(version, branchInfo) {
        if (branchInfo && branchInfo.name !== 'main') {
            return 'feature-branch';
        }
        if (version.is_merge) {
            return 'merge-commit';
        }
        return 'main-branch';
    }

    getVersionTags(versionId) {
        return this.tags.filter(tag => tag.version_id === versionId);
    }

    getVersionBranch(versionId) {
        // Find which branch this version belongs to
        return this.branches.find(branch => 
            branch.head_version_id === versionId || 
            branch.parent_version_id === versionId
        );
    }

    setupEventListeners() {
        // Timeline node click handlers are set up in the HTML
    }

    toggleVersionSelection(versionId) {
        const index = this.selectedVersions.indexOf(versionId);
        if (index > -1) {
            this.selectedVersions.splice(index, 1);
        } else {
            this.selectedVersions.push(versionId);
        }
        
        // Update UI
        this.updateCompareButton();
    }

    selectVersion(versionId) {
        this.showVersionDetails(versionId);
        
        // Update visual selection
        document.querySelectorAll('.timeline-node').forEach(node => {
            node.classList.remove('active');
        });
        
        const selectedNode = document.querySelector(`[data-version-id="${versionId}"]`);
        if (selectedNode) {
            selectedNode.classList.add('active');
        }
    }

    async showVersionDetails(versionId) {
        const version = this.versions.find(v => v.id === versionId);
        if (!version) return;

        const detailsContainer = document.getElementById('version-details-content');
        if (!detailsContainer) return;

        try {
            // Load detailed version data
            const response = await fetch(`/api/user/panels/${this.panelId}/versions/${version.version_number}`);
            const versionDetails = response.ok ? await response.json() : version;

            const versionTags = this.getVersionTags(versionId);
            const branchInfo = this.getVersionBranch(versionId);

            detailsContainer.innerHTML = `
                <div class="version-detail-card">
                    <div class="detail-header">
                        <h6>Version ${version.version_number}</h6>
                        <span class="version-date">${this.formatDate(version.created_at)}</span>
                    </div>
                    
                    <div class="detail-body">
                        <div class="detail-section">
                            <label>Description:</label>
                            <p>${version.comment || 'No description provided'}</p>
                        </div>
                        
                        <div class="detail-section">
                            <label>Created by:</label>
                            <p>${version.created_by?.username || 'Unknown'}</p>
                        </div>
                        
                        <div class="detail-section">
                            <label>Statistics:</label>
                            <div class="stats-grid">
                                <div class="stat-item">
                                    <span class="stat-value">${version.gene_count}</span>
                                    <span class="stat-label">Genes</span>
                                </div>
                                ${version.access_count ? `
                                    <div class="stat-item">
                                        <span class="stat-value">${version.access_count}</span>
                                        <span class="stat-label">Downloads</span>
                                    </div>
                                ` : ''}
                                ${version.size_bytes ? `
                                    <div class="stat-item">
                                        <span class="stat-value">${this.formatFileSize(version.size_bytes)}</span>
                                        <span class="stat-label">Size</span>
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                        
                        ${versionTags.length > 0 ? `
                            <div class="detail-section">
                                <label>Tags:</label>
                                <div class="tag-list">
                                    ${versionTags.map(tag => `
                                        <span class="version-tag tag-${tag.tag_type.toLowerCase()}">
                                            <i class="fas fa-tag"></i>
                                            ${tag.tag_name}
                                            ${tag.description ? `<small>${tag.description}</small>` : ''}
                                        </span>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                        
                        ${branchInfo ? `
                            <div class="detail-section">
                                <label>Branch:</label>
                                <p>${branchInfo.name}</p>
                                ${branchInfo.description ? `<small>${branchInfo.description}</small>` : ''}
                            </div>
                        ` : ''}
                        
                        ${version.changes_summary ? `
                            <div class="detail-section">
                                <label>Changes:</label>
                                <div class="changes-summary">
                                    ${this.renderChangesSummary(version.changes_summary)}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                    
                    <div class="detail-actions">
                        <button class="btn btn-primary" onclick="versionTimeline.viewVersion(${versionId})">
                            <i class="fas fa-eye"></i> View Details
                        </button>
                        <button class="btn btn-outline-secondary" onclick="versionTimeline.restoreVersion(${versionId})">
                            <i class="fas fa-undo"></i> Restore
                        </button>
                        <button class="btn btn-outline-info" onclick="versionTimeline.downloadVersion(${versionId})">
                            <i class="fas fa-download"></i> Download
                        </button>
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('Error loading version details:', error);
            detailsContainer.innerHTML = '<div class="alert alert-danger">Error loading version details</div>';
        }
    }

    renderChangesSummary(changesSummary) {
        try {
            const changes = typeof changesSummary === 'string' ? JSON.parse(changesSummary) : changesSummary;
            
            let html = '<div class="changes-list">';
            
            if (changes.genes_added && changes.genes_added.length > 0) {
                html += `
                    <div class="change-item">
                        <span class="change-type added">+${changes.genes_added.length}</span>
                        <span class="change-label">genes added</span>
                    </div>
                `;
            }
            
            if (changes.genes_removed && changes.genes_removed.length > 0) {
                html += `
                    <div class="change-item">
                        <span class="change-type removed">-${changes.genes_removed.length}</span>
                        <span class="change-label">genes removed</span>
                    </div>
                `;
            }
            
            if (changes.genes_modified && changes.genes_modified.length > 0) {
                html += `
                    <div class="change-item">
                        <span class="change-type modified">~${changes.genes_modified.length}</span>
                        <span class="change-label">genes modified</span>
                    </div>
                `;
            }
            
            html += '</div>';
            return html;
        } catch (error) {
            return '<p>Changes information not available</p>';
        }
    }

    updateCompareButton() {
        const compareBtn = document.querySelector('.timeline-controls button[onclick*="compareSelected"]');
        if (compareBtn) {
            const selectedCount = this.selectedVersions.length;
            if (selectedCount === 2) {
                compareBtn.disabled = false;
                compareBtn.innerHTML = '<i class="fas fa-code-compare"></i> Compare Selected (2)';
            } else {
                compareBtn.disabled = selectedCount < 2;
                compareBtn.innerHTML = `<i class="fas fa-code-compare"></i> Compare Selected (${selectedCount})`;
            }
        }
    }

    compareSelected() {
        if (this.selectedVersions.length !== 2) {
            alert('Please select exactly 2 versions to compare');
            return;
        }
        
        const [version1, version2] = this.selectedVersions;
        // Open diff viewer
        window.diffViewer = new DiffViewer(this.panelId, version1, version2);
        window.diffViewer.show();
    }

    async viewVersion(versionId) {
        // Open version details in modal or new view
        console.log('Viewing version:', versionId);
    }

    async restoreVersion(versionId) {
        if (!confirm('Are you sure you want to restore to this version? This will create a new version based on the selected one.')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/user/panels/${this.panelId}/versions/${versionId}/restore`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (response.ok) {
                alert('Version restored successfully');
                this.loadVersionData().then(() => this.renderTimeline());
            } else {
                throw new Error('Failed to restore version');
            }
        } catch (error) {
            console.error('Error restoring version:', error);
            alert('Error restoring version');
        }
    }

    async downloadVersion(versionId) {
        try {
            const version = this.versions.find(v => v.id === versionId);
            const response = await fetch(`/api/user/panels/${this.panelId}/versions/${version.version_number}/export/excel`);
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `panel_v${version.version_number}.xlsx`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } else {
                throw new Error('Failed to download version');
            }
        } catch (error) {
            console.error('Error downloading version:', error);
            alert('Error downloading version');
        }
    }

    exportTimeline() {
        // Export timeline as image or PDF
        console.log('Exporting timeline');
    }

    // Utility methods
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// Global instance for timeline operations
let versionTimeline;
