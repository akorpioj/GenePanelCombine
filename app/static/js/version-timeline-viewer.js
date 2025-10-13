/**
 * Version Timeline Viewer
 * Displays a visual timeline of panel version history with branch visualization
 */

class VersionTimelineViewer {
    constructor() {
        this.currentPanelId = null;
        this.versions = [];
        this.branches = [];
        this.tags = [];
    }

    /**
     * Show timeline for a specific panel
     * @param {number} panelId - The panel ID
     * @param {string} panelName - The panel name for display
     */
    async show(panelId, panelName) {
        this.currentPanelId = panelId;
        
        // Load version data
        await this.loadVersionData(panelId);
        
        // Create and show modal
        this.createModal(panelName);
        this.renderTimeline();
    }

    /**
     * Load version data from API
     */
    async loadVersionData(panelId) {
        try {
            const response = await fetch(`/api/user/panels/${panelId}/versions`);
            if (!response.ok) throw new Error('Failed to load version data');
            
            const data = await response.json();
            this.versions = data.versions || [];
            
            // Process versions to determine branches
            this.processBranches();
            
        } catch (error) {
            console.error('Error loading version data:', error);
            throw error;
        }
    }

    /**
     * Process versions to detect branches and merges
     */
    processBranches() {
        // Extract tags from versions
        this.tags = [];
        this.versions.forEach(version => {
            if (version.tags && version.tags.length > 0) {
                version.tags.forEach(tag => {
                    this.tags.push({
                        version_number: version.version_number,
                        name: tag.tag_name,
                        color: tag.color || '#6366f1'
                    });
                });
            }
        });

        // Detect branches based on version metadata or changes summary
        this.branches = this.detectBranches();
    }

    /**
     * Detect branches from version history
     */
    detectBranches() {
        const branches = [{
            name: 'main',
            color: '#3b82f6',
            versions: this.versions.map(v => v.version_number)
        }];

        // Check for branch indicators in version metadata
        this.versions.forEach(version => {
            if (version.metadata && version.metadata.branch) {
                const branchName = version.metadata.branch;
                let branch = branches.find(b => b.name === branchName);
                
                if (!branch) {
                    branch = {
                        name: branchName,
                        color: this.getRandomColor(),
                        versions: []
                    };
                    branches.push(branch);
                }
                
                branch.versions.push(version.version_number);
            }
        });

        return branches;
    }

    /**
     * Get a random color for branch visualization
     */
    getRandomColor() {
        const colors = [
            '#ef4444', '#f59e0b', '#10b981', '#3b82f6', 
            '#6366f1', '#8b5cf6', '#ec4899', '#06b6d4'
        ];
        return colors[Math.floor(Math.random() * colors.length)];
    }

    /**
     * Create the modal container
     */
    createModal(panelName) {
        const modalHTML = `
            <div id="version-timeline-modal" class="fixed inset-0 bg-gray-600 bg-opacity-50 z-50 flex items-center justify-center p-4">
                <div class="bg-white rounded-lg shadow-xl w-full max-w-6xl max-h-[90vh] flex flex-col">
                    <!-- Header -->
                    <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                        <div>
                            <h2 class="text-2xl font-bold text-gray-900">
                                <i class="fas fa-code-branch mr-2 text-blue-600"></i>
                                Version Timeline
                            </h2>
                            <p class="text-sm text-gray-500 mt-1">${panelName}</p>
                        </div>
                        <button id="close-timeline" class="text-gray-400 hover:text-gray-600">
                            <i class="fas fa-times text-2xl"></i>
                        </button>
                    </div>
                    
                    <!-- Toolbar -->
                    <div class="px-6 py-3 border-b border-gray-200 bg-gray-50">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center space-x-4">
                                <button id="zoom-in" class="px-3 py-1 text-sm bg-white border border-gray-300 rounded hover:bg-gray-50">
                                    <i class="fas fa-search-plus mr-1"></i>Zoom In
                                </button>
                                <button id="zoom-out" class="px-3 py-1 text-sm bg-white border border-gray-300 rounded hover:bg-gray-50">
                                    <i class="fas fa-search-minus mr-1"></i>Zoom Out
                                </button>
                                <button id="reset-zoom" class="px-3 py-1 text-sm bg-white border border-gray-300 rounded hover:bg-gray-50">
                                    <i class="fas fa-redo mr-1"></i>Reset
                                </button>
                            </div>
                            <div class="text-sm text-gray-600">
                                <i class="fas fa-info-circle mr-1"></i>
                                ${this.versions.length} versions
                            </div>
                        </div>
                    </div>
                    
                    <!-- Timeline Content -->
                    <div class="flex-1 overflow-auto p-6">
                        <div id="timeline-container" class="relative">
                            <!-- Timeline will be rendered here -->
                        </div>
                    </div>
                    
                    <!-- Legend -->
                    <div class="px-6 py-3 border-t border-gray-200 bg-gray-50">
                        <div class="flex items-center justify-between text-xs text-gray-600">
                            <div class="flex items-center space-x-4">
                                <div class="flex items-center">
                                    <div class="w-3 h-3 rounded-full bg-blue-500 mr-1"></div>
                                    <span>Version</span>
                                </div>
                                <div class="flex items-center">
                                    <i class="fas fa-tag text-yellow-500 mr-1"></i>
                                    <span>Tagged Version</span>
                                </div>
                                <div class="flex items-center">
                                    <i class="fas fa-shield-alt text-green-500 mr-1"></i>
                                    <span>Protected</span>
                                </div>
                                <div class="flex items-center">
                                    <i class="fas fa-star text-purple-500 mr-1"></i>
                                    <span>Current Version</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);

        // Event listeners
        document.getElementById('close-timeline').addEventListener('click', () => {
            this.close();
        });

        document.getElementById('zoom-in').addEventListener('click', () => {
            this.adjustZoom(1.2);
        });

        document.getElementById('zoom-out').addEventListener('click', () => {
            this.adjustZoom(0.8);
        });

        document.getElementById('reset-zoom').addEventListener('click', () => {
            this.resetZoom();
        });

        // Close on backdrop click
        document.getElementById('version-timeline-modal').addEventListener('click', (e) => {
            if (e.target.id === 'version-timeline-modal') {
                this.close();
            }
        });

        // Close on Escape key
        this.escapeHandler = (e) => {
            if (e.key === 'Escape') {
                this.close();
            }
        };
        document.addEventListener('keydown', this.escapeHandler);
    }

    /**
     * Render the timeline visualization
     */
    renderTimeline() {
        const container = document.getElementById('timeline-container');
        if (!container) return;

        const sortedVersions = [...this.versions].sort((a, b) => a.version_number - b.version_number);
        const currentVersion = Math.max(...sortedVersions.map(v => v.version_number));

        let timelineHTML = '<div class="timeline-wrapper">';
        
        // Timeline axis
        timelineHTML += '<div class="timeline-axis">';
        
        sortedVersions.forEach((version, index) => {
            const isFirst = index === 0;
            const isLast = index === sortedVersions.length - 1;
            const isCurrent = version.version_number === currentVersion;
            const isProtected = version.is_protected;
            const hasTags = this.tags.filter(t => t.version_number === version.version_number).length > 0;
            
            // Calculate position
            const position = (index / Math.max(sortedVersions.length - 1, 1)) * 100;
            
            timelineHTML += `
                <div class="timeline-node" style="left: ${position}%" data-version="${version.version_number}">
                    <!-- Connector line (except for first) -->
                    ${!isFirst ? '<div class="timeline-connector"></div>' : ''}
                    
                    <!-- Version node -->
                    <div class="version-node ${isCurrent ? 'current-version' : ''} ${isProtected ? 'protected-version' : ''}" 
                         onclick="versionTimelineViewer.showVersionDetails(${version.version_number})">
                        <div class="node-circle">
                            ${isCurrent ? '<i class="fas fa-star text-xs"></i>' : ''}
                            ${isProtected && !isCurrent ? '<i class="fas fa-shield-alt text-xs"></i>' : ''}
                        </div>
                        
                        <!-- Version label -->
                        <div class="version-label">
                            <div class="font-semibold">v${version.version_number}</div>
                            <div class="text-xs text-gray-500">${this.formatDate(version.created_at)}</div>
                            ${hasTags ? `<div class="text-xs text-yellow-600 mt-1"><i class="fas fa-tag mr-1"></i>${this.getTags(version.version_number).join(', ')}</div>` : ''}
                        </div>
                        
                        <!-- Version info card (shown on hover) -->
                        <div class="version-info-card">
                            <div class="font-semibold text-sm mb-2">Version ${version.version_number}</div>
                            <div class="text-xs space-y-1">
                                <div><i class="fas fa-user mr-1"></i>${version.created_by?.username || 'Unknown'}</div>
                                <div><i class="fas fa-calendar mr-1"></i>${this.formatDateTime(version.created_at)}</div>
                                <div><i class="fas fa-dna mr-1"></i>${version.gene_count} genes</div>
                                ${version.comment ? `<div class="mt-2 text-gray-600">${version.comment}</div>` : ''}
                                ${isProtected ? '<div class="mt-2 text-green-600"><i class="fas fa-shield-alt mr-1"></i>Protected</div>' : ''}
                                ${isCurrent ? '<div class="mt-2 text-purple-600"><i class="fas fa-star mr-1"></i>Current Version</div>' : ''}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        timelineHTML += '</div>'; // Close timeline-axis
        timelineHTML += '</div>'; // Close timeline-wrapper

        container.innerHTML = timelineHTML;
        
        // Add CSS for timeline
        this.injectTimelineCSS();
    }

    /**
     * Get tags for a specific version
     */
    getTags(versionNumber) {
        return this.tags
            .filter(t => t.version_number === versionNumber)
            .map(t => t.name);
    }

    /**
     * Format date for display
     */
    formatDate(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffDays === 0) return 'Today';
        if (diffDays === 1) return 'Yesterday';
        if (diffDays < 7) return `${diffDays}d ago`;
        if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`;
        return date.toLocaleDateString();
    }

    /**
     * Format date and time for detailed view
     */
    formatDateTime(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toLocaleString();
    }

    /**
     * Show detailed information about a version
     */
    async showVersionDetails(versionNumber) {
        const version = this.versions.find(v => v.version_number === versionNumber);
        if (!version) return;

        const detailsHTML = `
            <div id="version-details-overlay" class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
                <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full p-6">
                    <div class="flex justify-between items-start mb-4">
                        <h3 class="text-xl font-bold">Version ${version.version_number} Details</h3>
                        <button onclick="document.getElementById('version-details-overlay').remove()" 
                                class="text-gray-400 hover:text-gray-600">
                            <i class="fas fa-times text-xl"></i>
                        </button>
                    </div>
                    
                    <div class="space-y-3 text-sm">
                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <span class="font-medium text-gray-700">Created By:</span>
                                <div class="text-gray-900">${version.created_by?.full_name || version.created_by?.username || 'Unknown'}</div>
                            </div>
                            <div>
                                <span class="font-medium text-gray-700">Created:</span>
                                <div class="text-gray-900">${this.formatDateTime(version.created_at)}</div>
                            </div>
                        </div>
                        
                        <div>
                            <span class="font-medium text-gray-700">Gene Count:</span>
                            <span class="text-gray-900">${version.gene_count}</span>
                        </div>
                        
                        ${version.comment ? `
                            <div>
                                <span class="font-medium text-gray-700">Comment:</span>
                                <div class="text-gray-900 mt-1 p-2 bg-gray-50 rounded">${version.comment}</div>
                            </div>
                        ` : ''}
                        
                        <div class="flex items-center space-x-4 pt-2">
                            ${version.is_protected ? '<span class="text-green-600"><i class="fas fa-shield-alt mr-1"></i>Protected</span>' : ''}
                            ${version.tags?.length > 0 ? `<span class="text-yellow-600"><i class="fas fa-tag mr-1"></i>${version.tags.map(t => t.tag_name).join(', ')}</span>` : ''}
                        </div>
                        
                        <div class="border-t border-gray-200 pt-3 mt-3">
                            <span class="font-medium text-gray-700">Statistics:</span>
                            <div class="grid grid-cols-2 gap-2 mt-2 text-xs">
                                <div>Access Count: ${version.access_count || 0}</div>
                                <div>Last Accessed: ${version.last_accessed_at ? this.formatDateTime(version.last_accessed_at) : 'Never'}</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="mt-6 flex justify-end space-x-3">
                        <button onclick="versionTimelineViewer.restoreVersion(${version.id}, ${version.version_number})" 
                                class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                            <i class="fas fa-undo mr-2"></i>Restore This Version
                        </button>
                        <button onclick="versionTimelineViewer.viewVersionDiff(${version.version_number})" 
                                class="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700">
                            <i class="fas fa-code-branch mr-2"></i>View Changes
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', detailsHTML);
    }

    /**
     * Restore a specific version
     */
    async restoreVersion(versionId, versionNumber) {
        if (!confirm(`Are you sure you want to restore to version ${versionNumber}? This will create a new version.`)) {
            return;
        }

        try {
            const response = await fetch(`/api/user/panels/${this.currentPanelId}/versions/${versionId}/restore`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    create_backup: true
                })
            });

            if (!response.ok) throw new Error('Failed to restore version');

            alert('Version restored successfully!');
            
            // Remove details overlay
            document.getElementById('version-details-overlay')?.remove();
            
            // Reload timeline
            await this.loadVersionData(this.currentPanelId);
            this.renderTimeline();
            
        } catch (error) {
            console.error('Error restoring version:', error);
            alert('Failed to restore version. Please try again.');
        }
    }

    /**
     * View diff between versions
     */
    async viewVersionDiff(versionNumber) {
        const currentVersion = Math.max(...this.versions.map(v => v.version_number));
        
        // Close details overlay
        document.getElementById('version-details-overlay')?.remove();
        
        // Close timeline modal
        this.close();
        
        // Open diff viewer (assuming it exists)
        if (typeof showVersionDiff === 'function') {
            showVersionDiff(this.currentPanelId, versionNumber, currentVersion);
        } else {
            alert('Diff viewer not available. Please implement showVersionDiff function.');
        }
    }

    /**
     * Adjust zoom level
     */
    adjustZoom(factor) {
        const container = document.getElementById('timeline-container');
        if (!container) return;
        
        const currentScale = parseFloat(container.dataset.scale || 1);
        const newScale = currentScale * factor;
        
        container.style.transform = `scale(${newScale})`;
        container.style.transformOrigin = 'top left';
        container.dataset.scale = newScale;
    }

    /**
     * Reset zoom to default
     */
    resetZoom() {
        const container = document.getElementById('timeline-container');
        if (!container) return;
        
        container.style.transform = 'scale(1)';
        container.dataset.scale = 1;
    }

    /**
     * Inject CSS for timeline visualization
     */
    injectTimelineCSS() {
        if (document.getElementById('timeline-css')) return;
        
        const style = document.createElement('style');
        style.id = 'timeline-css';
        style.textContent = `
            .timeline-wrapper {
                min-height: 300px;
                padding: 40px 20px;
                transition: transform 0.3s ease;
            }
            
            .timeline-axis {
                position: relative;
                height: 200px;
                margin: 0 auto;
                max-width: 100%;
            }
            
            .timeline-node {
                position: absolute;
                top: 50%;
                transform: translate(-50%, -50%);
            }
            
            .timeline-connector {
                position: absolute;
                right: 100%;
                top: 50%;
                height: 2px;
                background: linear-gradient(to left, #3b82f6, #93c5fd);
                width: calc(100vw / ${Math.max(this.versions.length - 1, 1)});
                transform: translateY(-50%);
            }
            
            .version-node {
                position: relative;
                cursor: pointer;
                transition: transform 0.2s ease;
            }
            
            .version-node:hover {
                transform: scale(1.1);
                z-index: 10;
            }
            
            .node-circle {
                width: 24px;
                height: 24px;
                border-radius: 50%;
                background: linear-gradient(135deg, #3b82f6, #2563eb);
                border: 3px solid white;
                box-shadow: 0 2px 8px rgba(59, 130, 246, 0.4);
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                transition: all 0.2s ease;
            }
            
            .version-node.current-version .node-circle {
                background: linear-gradient(135deg, #a855f7, #7c3aed);
                box-shadow: 0 2px 12px rgba(168, 85, 247, 0.5);
                width: 32px;
                height: 32px;
                border-width: 4px;
            }
            
            .version-node.protected-version .node-circle {
                background: linear-gradient(135deg, #10b981, #059669);
                box-shadow: 0 2px 8px rgba(16, 185, 129, 0.4);
            }
            
            .version-node:hover .node-circle {
                box-shadow: 0 4px 16px rgba(59, 130, 246, 0.6);
                transform: scale(1.2);
            }
            
            .version-label {
                position: absolute;
                top: 40px;
                left: 50%;
                transform: translateX(-50%);
                text-align: center;
                min-width: 100px;
                font-size: 12px;
            }
            
            .version-info-card {
                position: absolute;
                bottom: 50px;
                left: 50%;
                transform: translateX(-50%);
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 12px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                min-width: 200px;
                max-width: 300px;
                opacity: 0;
                pointer-events: none;
                transition: opacity 0.2s ease;
                z-index: 20;
            }
            
            .version-node:hover .version-info-card {
                opacity: 1;
                pointer-events: auto;
            }
            
            @media (max-width: 768px) {
                .timeline-wrapper {
                    padding: 20px 10px;
                }
                
                .version-label {
                    font-size: 10px;
                    min-width: 80px;
                }
                
                .node-circle {
                    width: 20px;
                    height: 20px;
                }
                
                .version-node.current-version .node-circle {
                    width: 26px;
                    height: 26px;
                }
            }
        `;
        
        document.head.appendChild(style);
    }

    /**
     * Close the timeline viewer
     */
    close() {
        document.getElementById('version-timeline-modal')?.remove();
        if (this.escapeHandler) {
            document.removeEventListener('keydown', this.escapeHandler);
        }
    }
}

// Initialize global instance
const versionTimelineViewer = new VersionTimelineViewer();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VersionTimelineViewer;
}
