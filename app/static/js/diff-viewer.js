/**
 * Diff Viewer Component
 * Side-by-side comparison with highlighted changes
 */

class DiffViewer {
    constructor(panelId, version1Id, version2Id) {
        this.panelId = panelId;
        this.version1Id = version1Id;
        this.version2Id = version2Id;
        this.version1Data = null;
        this.version2Data = null;
        this.diffResults = null;
        this.viewMode = 'side-by-side'; // 'side-by-side' or 'unified'
        this.showOnlyChanges = false;
        
        this.modal = null;
    }

    async show() {
        await this.loadVersionData();
        this.calculateDiff();
        this.renderModal();
        this.displayModal();
    }

    async loadVersionData() {
        try {
            // Load version 1 data
            const v1Response = await fetch(`/api/user/panels/${this.panelId}/versions/${this.getVersionNumber(this.version1Id)}`);
            if (v1Response.ok) {
                this.version1Data = await v1Response.json();
            }

            // Load version 2 data
            const v2Response = await fetch(`/api/user/panels/${this.panelId}/versions/${this.getVersionNumber(this.version2Id)}`);
            if (v2Response.ok) {
                this.version2Data = await v2Response.json();
            }

            if (!this.version1Data || !this.version2Data) {
                throw new Error('Failed to load version data');
            }
        } catch (error) {
            console.error('Error loading version data:', error);
            throw error;
        }
    }

    getVersionNumber(versionId) {
        // This would typically come from the timeline data
        // For now, assume we can find it in the timeline
        if (window.versionTimeline && window.versionTimeline.versions) {
            const version = window.versionTimeline.versions.find(v => v.id === versionId);
            return version ? version.version_number : versionId;
        }
        return versionId;
    }

    calculateDiff() {
        this.diffResults = {
            metadata: this.compareMetadata(),
            genes: this.compareGenes(),
            statistics: this.calculateStatistics()
        };
    }

    compareMetadata() {
        const v1 = this.version1Data;
        const v2 = this.version2Data;
        
        const changes = {};
        
        // Compare basic fields
        const fieldsToCompare = ['panel_name', 'panel_symbol', 'description', 'source_organisation', 'version_number'];
        
        fieldsToCompare.forEach(field => {
            if (v1[field] !== v2[field]) {
                changes[field] = {
                    old: v1[field],
                    new: v2[field],
                    type: 'modified'
                };
            }
        });
        
        return changes;
    }

    compareGenes() {
        const v1Genes = this.extractGenes(this.version1Data);
        const v2Genes = this.extractGenes(this.version2Data);
        
        const result = {
            added: [],
            removed: [],
            modified: [],
            unchanged: []
        };
        
        // Create maps for easier comparison
        const v1GeneMap = new Map(v1Genes.map(gene => [gene.hgnc_symbol, gene]));
        const v2GeneMap = new Map(v2Genes.map(gene => [gene.hgnc_symbol, gene]));
        
        // Find added genes (in v2 but not in v1)
        for (const [symbol, gene] of v2GeneMap) {
            if (!v1GeneMap.has(symbol)) {
                result.added.push(gene);
            }
        }
        
        // Find removed genes (in v1 but not in v2)
        for (const [symbol, gene] of v1GeneMap) {
            if (!v2GeneMap.has(symbol)) {
                result.removed.push(gene);
            }
        }
        
        // Find modified and unchanged genes
        for (const [symbol, v2Gene] of v2GeneMap) {
            if (v1GeneMap.has(symbol)) {
                const v1Gene = v1GeneMap.get(symbol);
                const differences = this.compareGeneDetails(v1Gene, v2Gene);
                
                if (differences.length > 0) {
                    result.modified.push({
                        gene: v2Gene,
                        oldGene: v1Gene,
                        differences: differences
                    });
                } else {
                    result.unchanged.push(v2Gene);
                }
            }
        }
        
        return result;
    }

    extractGenes(versionData) {
        // Extract genes from version data - adapt based on your data structure
        if (versionData.genes) {
            return versionData.genes;
        }
        
        // If genes are in panel_genes relationship
        if (versionData.panel_genes) {
            return versionData.panel_genes.map(pg => ({
                hgnc_symbol: pg.hgnc_symbol,
                confidence_level: pg.confidence_level,
                phenotype: pg.phenotype,
                mode_of_inheritance: pg.mode_of_inheritance,
                mode_of_pathogenicity: pg.mode_of_pathogenicity,
                publications: pg.publications,
                evidence: pg.evidence,
                tags: pg.tags
            }));
        }
        
        return [];
    }

    compareGeneDetails(gene1, gene2) {
        const differences = [];
        const fieldsToCompare = [
            'confidence_level', 'phenotype', 'mode_of_inheritance', 
            'mode_of_pathogenicity', 'publications', 'evidence'
        ];
        
        fieldsToCompare.forEach(field => {
            if (gene1[field] !== gene2[field]) {
                differences.push({
                    field: field,
                    old: gene1[field],
                    new: gene2[field]
                });
            }
        });
        
        return differences;
    }

    calculateStatistics() {
        const genes = this.diffResults.genes;
        
        return {
            totalV1: this.extractGenes(this.version1Data).length,
            totalV2: this.extractGenes(this.version2Data).length,
            added: genes.added.length,
            removed: genes.removed.length,
            modified: genes.modified.length,
            unchanged: genes.unchanged.length,
            changePercentage: this.calculateChangePercentage()
        };
    }

    calculateChangePercentage() {
        const genes = this.diffResults.genes;
        const totalChanges = genes.added.length + genes.removed.length + genes.modified.length;
        const totalV1 = this.extractGenes(this.version1Data).length;
        
        if (totalV1 === 0) return 0;
        return Math.round((totalChanges / totalV1) * 100);
    }

    renderModal() {
        const modalHtml = `
            <div class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center diff-viewer-modal" id="diffViewerModal" style="display: none;">
                <div class="bg-white rounded-lg max-w-7xl max-h-screen w-full mx-4 overflow-hidden">
                    <div class="bg-white rounded-lg shadow-xl">
                        <div class="flex items-center justify-between p-6 border-b border-gray-200">
                            <div class="modal-title-container">
                                <h5 class="text-xl font-semibold text-gray-900">Version Comparison</h5>
                                <div class="version-labels flex items-center mt-2">
                                    <span class="version-label version-old bg-red-100 text-red-800 px-3 py-1 rounded-md">
                                        v${this.version1Data.version_number}
                                        <small class="block text-xs text-red-600">${this.formatDate(this.version1Data.created_at)}</small>
                                    </span>
                                    <i class="fas fa-arrow-right mx-3 text-gray-400"></i>
                                    <span class="version-label version-new bg-green-100 text-green-800 px-3 py-1 rounded-md">
                                        v${this.version2Data.version_number}
                                        <small class="block text-xs text-green-600">${this.formatDate(this.version2Data.created_at)}</small>
                                    </span>
                                </div>
                            </div>
                            <button type="button" class="text-gray-400 hover:text-gray-600 transition-colors" onclick="diffViewer.closeModal()">
                                <i class="fas fa-times text-xl"></i>
                            </button>
                        </div>
                        
                        <div class="p-6 overflow-y-auto max-h-[calc(100vh-200px)]">
                            ${this.renderDiffHeader()}
                            ${this.renderDiffContent()}
                        </div>
                        
                        <div class="border-t border-gray-200 p-6">
                            <div class="flex items-center justify-end space-x-3">
                                <button class="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors" onclick="diffViewer.exportDiff()">
                                    <i class="fas fa-download mr-2"></i> Export Diff
                                </button>
                                <button class="px-4 py-2 text-blue-700 bg-blue-100 hover:bg-blue-200 rounded-md transition-colors" onclick="diffViewer.generateReport()">
                                    <i class="fas fa-file-alt mr-2"></i> Generate Report
                                </button>
                                <button class="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors" onclick="diffViewer.closeModal()">Close</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if any
        const existingModal = document.getElementById('diffViewerModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Add modal to DOM
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        this.modal = document.getElementById('diffViewerModal');
    }

    renderDiffHeader() {
        const stats = this.diffResults.statistics;
        
        return `
            <div class="diff-header space-y-6">
                <div class="diff-controls">
                    <div class="view-controls flex items-center justify-between">
                        <div class="flex items-center space-x-4">
                            <div class="flex bg-gray-100 rounded-lg p-1">
                                <button type="button" class="px-4 py-2 rounded-md transition-colors ${this.viewMode === 'side-by-side' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-600 hover:text-gray-900'}"
                                        onclick="diffViewer.setViewMode('side-by-side')">
                                    <i class="fas fa-columns mr-2"></i> Side by Side
                                </button>
                                <button type="button" class="px-4 py-2 rounded-md transition-colors ${this.viewMode === 'unified' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-600 hover:text-gray-900'}"
                                        onclick="diffViewer.setViewMode('unified')">
                                    <i class="fas fa-align-left mr-2"></i> Unified
                                </button>
                            </div>
                        </div>
                        
                        <div class="filter-controls">
                            <label class="flex items-center space-x-2 cursor-pointer">
                                <input type="checkbox" class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                       onchange="diffViewer.toggleShowOnlyChanges(this.checked)"
                                       ${this.showOnlyChanges ? 'checked' : ''}>
                                <span class="text-sm text-gray-700">Show only changes</span>
                            </label>
                        </div>
                    </div>
                </div>
                
                <div class="diff-statistics">
                    <div class="grid grid-cols-5 gap-4">
                        <div class="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
                            <div class="text-2xl font-bold text-green-600">+${stats.added}</div>
                            <div class="text-sm text-green-800">Added</div>
                        </div>
                        <div class="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
                            <div class="text-2xl font-bold text-red-600">-${stats.removed}</div>
                            <div class="text-sm text-red-800">Removed</div>
                        </div>
                        <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-center">
                            <div class="text-2xl font-bold text-yellow-600">~${stats.modified}</div>
                            <div class="text-sm text-yellow-800">Modified</div>
                        </div>
                        <div class="bg-gray-50 border border-gray-200 rounded-lg p-4 text-center">
                            <div class="text-2xl font-bold text-gray-600">${stats.unchanged}</div>
                            <div class="text-sm text-gray-700">Unchanged</div>
                        </div>
                        <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
                            <div class="text-2xl font-bold text-blue-600">${stats.changePercentage}%</div>
                            <div class="text-sm text-blue-800">Changed</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderDiffContent() {
        return `
            <div class="diff-content">
                <nav class="diff-nav mb-6">
                    <div class="flex border-b border-gray-200" id="diffTabs" role="tablist">
                        <button class="px-6 py-3 text-sm font-medium text-blue-600 border-b-2 border-blue-600 tab-button active" 
                                id="metadata-tab" onclick="diffViewer.switchTab('metadata')" type="button" role="tab">
                            <i class="fas fa-info-circle mr-2"></i> Metadata
                        </button>
                        <button class="px-6 py-3 text-sm font-medium text-gray-500 hover:text-gray-700 tab-button" 
                                id="genes-tab" onclick="diffViewer.switchTab('genes')" type="button" role="tab">
                            <i class="fas fa-dna mr-2"></i> Genes
                        </button>
                        <button class="px-6 py-3 text-sm font-medium text-gray-500 hover:text-gray-700 tab-button" 
                                id="summary-tab" onclick="diffViewer.switchTab('summary')" type="button" role="tab">
                            <i class="fas fa-chart-bar mr-2"></i> Summary
                        </button>
                    </div>
                </nav>
                
                <div class="tab-content" id="diffTabContent">
                    <div class="tab-pane active" id="metadata-content" role="tabpanel">
                        ${this.renderMetadataDiff()}
                    </div>
                    <div class="tab-pane hidden" id="genes-content" role="tabpanel">
                        ${this.renderGenesDiff()}
                    </div>
                    <div class="tab-pane hidden" id="summary-content" role="tabpanel">
                        ${this.renderSummaryDiff()}
                    </div>
                </div>
            </div>
        `;
    }

    renderMetadataDiff() {
        const metadataChanges = this.diffResults.metadata;
        
        if (Object.keys(metadataChanges).length === 0) {
            return '<div class="no-changes">No metadata changes detected</div>';
        }
        
        let html = '<div class="metadata-diff">';
        
        if (this.viewMode === 'side-by-side') {
            html += `
                <div class="diff-side-by-side">
                    <div class="diff-side">
                        <h6>Version ${this.version1Data.version_number}</h6>
                        <div class="metadata-list">
                            ${Object.entries(metadataChanges).map(([field, change]) => `
                                <div class="metadata-item">
                                    <label>${this.formatFieldName(field)}:</label>
                                    <div class="metadata-value old-value">${change.old || 'Not set'}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    <div class="diff-side">
                        <h6>Version ${this.version2Data.version_number}</h6>
                        <div class="metadata-list">
                            ${Object.entries(metadataChanges).map(([field, change]) => `
                                <div class="metadata-item">
                                    <label>${this.formatFieldName(field)}:</label>
                                    <div class="metadata-value new-value">${change.new || 'Not set'}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `;
        } else {
            html += `
                <div class="diff-unified">
                    ${Object.entries(metadataChanges).map(([field, change]) => `
                        <div class="unified-change">
                            <h6>${this.formatFieldName(field)}</h6>
                            <div class="change-line old-line">- ${change.old || 'Not set'}</div>
                            <div class="change-line new-line">+ ${change.new || 'Not set'}</div>
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        html += '</div>';
        return html;
    }

    renderGenesDiff() {
        const genes = this.diffResults.genes;
        let html = '<div class="genes-diff">';
        
        // Added genes section
        if (genes.added.length > 0) {
            html += `
                <div class="gene-section added-section">
                    <h6 class="section-title">
                        <i class="fas fa-plus-circle text-success"></i>
                        Added Genes (${genes.added.length})
                    </h6>
                    <div class="gene-list">
                        ${genes.added.map(gene => this.renderGeneItem(gene, 'added')).join('')}
                    </div>
                </div>
            `;
        }
        
        // Removed genes section
        if (genes.removed.length > 0) {
            html += `
                <div class="gene-section removed-section">
                    <h6 class="section-title">
                        <i class="fas fa-minus-circle text-danger"></i>
                        Removed Genes (${genes.removed.length})
                    </h6>
                    <div class="gene-list">
                        ${genes.removed.map(gene => this.renderGeneItem(gene, 'removed')).join('')}
                    </div>
                </div>
            `;
        }
        
        // Modified genes section
        if (genes.modified.length > 0) {
            html += `
                <div class="gene-section modified-section">
                    <h6 class="section-title">
                        <i class="fas fa-edit text-warning"></i>
                        Modified Genes (${genes.modified.length})
                    </h6>
                    <div class="gene-list">
                        ${genes.modified.map(modifiedGene => this.renderModifiedGene(modifiedGene)).join('')}
                    </div>
                </div>
            `;
        }
        
        // Unchanged genes section (only if not filtering)
        if (!this.showOnlyChanges && genes.unchanged.length > 0) {
            html += `
                <div class="gene-section unchanged-section">
                    <h6 class="section-title">
                        <i class="fas fa-equals text-muted"></i>
                        Unchanged Genes (${genes.unchanged.length})
                    </h6>
                    <div class="gene-list collapsed" id="unchangedGenes">
                        ${genes.unchanged.slice(0, 10).map(gene => this.renderGeneItem(gene, 'unchanged')).join('')}
                        ${genes.unchanged.length > 10 ? `
                            <div class="show-more-genes" onclick="diffViewer.showAllUnchangedGenes()">
                                <i class="fas fa-chevron-down"></i>
                                Show ${genes.unchanged.length - 10} more genes
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }
        
        html += '</div>';
        return html;
    }

    renderGeneItem(gene, changeType) {
        return `
            <div class="gene-item ${changeType}">
                <div class="gene-header">
                    <span class="gene-symbol">${gene.hgnc_symbol}</span>
                    <span class="gene-confidence confidence-${gene.confidence_level}">
                        ${gene.confidence_level}
                    </span>
                </div>
                <div class="gene-details">
                    ${gene.phenotype ? `<div class="gene-detail">Phenotype: ${gene.phenotype}</div>` : ''}
                    ${gene.mode_of_inheritance ? `<div class="gene-detail">Inheritance: ${gene.mode_of_inheritance}</div>` : ''}
                    ${gene.mode_of_pathogenicity ? `<div class="gene-detail">Pathogenicity: ${gene.mode_of_pathogenicity}</div>` : ''}
                </div>
            </div>
        `;
    }

    renderModifiedGene(modifiedGene) {
        const gene = modifiedGene.gene;
        const oldGene = modifiedGene.oldGene;
        const differences = modifiedGene.differences;
        
        return `
            <div class="gene-item modified">
                <div class="gene-header">
                    <span class="gene-symbol">${gene.hgnc_symbol}</span>
                    <span class="modification-count">${differences.length} change${differences.length > 1 ? 's' : ''}</span>
                </div>
                <div class="gene-modifications">
                    ${differences.map(diff => `
                        <div class="modification-item">
                            <label>${this.formatFieldName(diff.field)}:</label>
                            <div class="value-comparison">
                                <span class="old-value">${diff.old || 'Not set'}</span>
                                <i class="fas fa-arrow-right"></i>
                                <span class="new-value">${diff.new || 'Not set'}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    renderSummaryDiff() {
        const stats = this.diffResults.statistics;
        const metadataChanges = Object.keys(this.diffResults.metadata).length;
        
        return `
            <div class="summary-diff">
                <div class="summary-overview">
                    <h6>Change Summary</h6>
                    <div class="summary-stats">
                        <div class="summary-row">
                            <span class="summary-label">Total genes in v${this.version1Data.version_number}:</span>
                            <span class="summary-value">${stats.totalV1}</span>
                        </div>
                        <div class="summary-row">
                            <span class="summary-label">Total genes in v${this.version2Data.version_number}:</span>
                            <span class="summary-value">${stats.totalV2}</span>
                        </div>
                        <div class="summary-row">
                            <span class="summary-label">Net change:</span>
                            <span class="summary-value ${stats.totalV2 > stats.totalV1 ? 'text-success' : stats.totalV2 < stats.totalV1 ? 'text-danger' : ''}">
                                ${stats.totalV2 > stats.totalV1 ? '+' : ''}${stats.totalV2 - stats.totalV1}
                            </span>
                        </div>
                        <div class="summary-row">
                            <span class="summary-label">Overall change percentage:</span>
                            <span class="summary-value">${stats.changePercentage}%</span>
                        </div>
                        <div class="summary-row">
                            <span class="summary-label">Metadata changes:</span>
                            <span class="summary-value">${metadataChanges}</span>
                        </div>
                    </div>
                </div>
                
                <div class="change-breakdown">
                    <h6>Change Breakdown</h6>
                    <div class="breakdown-chart">
                        ${this.renderChangeChart(stats)}
                    </div>
                </div>
                
                <div class="version-info">
                    <div class="version-comparison">
                        <div class="version-card">
                            <h6>Version ${this.version1Data.version_number}</h6>
                            <div class="version-meta">
                                <div>Created: ${this.formatDate(this.version1Data.created_at)}</div>
                                <div>By: ${this.version1Data.created_by?.username || 'Unknown'}</div>
                                ${this.version1Data.comment ? `<div>Comment: ${this.version1Data.comment}</div>` : ''}
                            </div>
                        </div>
                        <div class="version-card">
                            <h6>Version ${this.version2Data.version_number}</h6>
                            <div class="version-meta">
                                <div>Created: ${this.formatDate(this.version2Data.created_at)}</div>
                                <div>By: ${this.version2Data.created_by?.username || 'Unknown'}</div>
                                ${this.version2Data.comment ? `<div>Comment: ${this.version2Data.comment}</div>` : ''}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderChangeChart(stats) {
        const total = stats.added + stats.removed + stats.modified + stats.unchanged;
        if (total === 0) return '<div>No data to display</div>';
        
        const addedPercent = (stats.added / total) * 100;
        const removedPercent = (stats.removed / total) * 100;
        const modifiedPercent = (stats.modified / total) * 100;
        const unchangedPercent = (stats.unchanged / total) * 100;
        
        return `
            <div class="chart-container">
                <div class="chart-bar">
                    <div class="chart-segment added" style="width: ${addedPercent}%" title="Added: ${stats.added}"></div>
                    <div class="chart-segment removed" style="width: ${removedPercent}%" title="Removed: ${stats.removed}"></div>
                    <div class="chart-segment modified" style="width: ${modifiedPercent}%" title="Modified: ${stats.modified}"></div>
                    <div class="chart-segment unchanged" style="width: ${unchangedPercent}%" title="Unchanged: ${stats.unchanged}"></div>
                </div>
                <div class="chart-legend">
                    <div class="legend-item">
                        <span class="legend-color added"></span>
                        <span>Added (${stats.added})</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-color removed"></span>
                        <span>Removed (${stats.removed})</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-color modified"></span>
                        <span>Modified (${stats.modified})</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-color unchanged"></span>
                        <span>Unchanged (${stats.unchanged})</span>
                    </div>
                </div>
            </div>
        `;
    }

    displayModal() {
        if (this.modal) {
            this.modal.style.display = 'flex';
            // Add fade-in effect
            setTimeout(() => {
                this.modal.classList.add('opacity-100');
            }, 10);
        }
    }

    closeModal() {
        if (this.modal) {
            this.modal.style.display = 'none';
            this.modal.classList.remove('opacity-100');
        }
    }

    setViewMode(mode) {
        this.viewMode = mode;
        // Update just the content instead of re-rendering entire modal
        const contentContainer = document.getElementById('diffTabContent');
        if (contentContainer) {
            // Update the active tab content
            const activePane = contentContainer.querySelector('.tab-pane.active');
            if (activePane) {
                const tabId = activePane.id;
                if (tabId === 'metadata-content') {
                    activePane.innerHTML = this.renderMetadataDiff();
                } else if (tabId === 'genes-content') {
                    activePane.innerHTML = this.renderGenesDiff();
                } else if (tabId === 'summary-content') {
                    activePane.innerHTML = this.renderSummaryDiff();
                }
            }
        }
        
        // Update the header controls
        const headerContainer = document.querySelector('.diff-header');
        if (headerContainer) {
            headerContainer.innerHTML = this.renderDiffHeader().replace('<div class="diff-header space-y-6">', '').replace('</div>', '');
        }
    }

    switchTab(tabName) {
        // Remove active classes from all tabs and panes
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('text-blue-600', 'border-blue-600', 'active', 'border-b-2');
            btn.classList.add('text-gray-500');
        });
        document.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.add('hidden');
            pane.classList.remove('active');
        });

        // Add active classes to selected tab and pane
        const activeTab = document.getElementById(`${tabName}-tab`);
        const activePane = document.getElementById(`${tabName}-content`);
        
        if (activeTab && activePane) {
            activeTab.classList.add('text-blue-600', 'border-blue-600', 'border-b-2', 'active');
            activeTab.classList.remove('text-gray-500');
            activePane.classList.remove('hidden');
            activePane.classList.add('active');
        }
    }

    toggleShowOnlyChanges(showOnly) {
        this.showOnlyChanges = showOnly;
        // Update just the genes content
        const genesContent = document.getElementById('genes-content');
        if (genesContent) {
            genesContent.innerHTML = this.renderGenesDiff();
        }
    }

    showAllUnchangedGenes() {
        const unchangedContainer = document.getElementById('unchangedGenes');
        if (unchangedContainer) {
            const genes = this.diffResults.genes.unchanged;
            unchangedContainer.innerHTML = genes.map(gene => this.renderGeneItem(gene, 'unchanged')).join('');
        }
    }

    async exportDiff() {
        const diffData = {
            version1: this.version1Data,
            version2: this.version2Data,
            diff: this.diffResults,
            timestamp: new Date().toISOString()
        };
        
        const blob = new Blob([JSON.stringify(diffData, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `panel_diff_v${this.version1Data.version_number}_v${this.version2Data.version_number}.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }

    async generateReport() {
        // Generate a detailed HTML report
        const reportHtml = this.generateReportHtml();
        const blob = new Blob([reportHtml], { type: 'text/html' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `panel_comparison_report_v${this.version1Data.version_number}_v${this.version2Data.version_number}.html`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }

    generateReportHtml() {
        const stats = this.diffResults.statistics;
        
        return `
            <!DOCTYPE html>
            <html>
            <head>
                <title>Panel Comparison Report</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .header { border-bottom: 2px solid #007bff; padding-bottom: 10px; margin-bottom: 20px; }
                    .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }
                    .stat-card { border: 1px solid #ddd; padding: 15px; border-radius: 5px; }
                    .section { margin-bottom: 30px; }
                    .gene-list { margin-left: 20px; }
                    .added { color: #28a745; }
                    .removed { color: #dc3545; }
                    .modified { color: #ffc107; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Panel Comparison Report</h1>
                    <p>Version ${this.version1Data.version_number} vs Version ${this.version2Data.version_number}</p>
                    <p>Generated on: ${new Date().toLocaleString()}</p>
                </div>
                
                <div class="stats">
                    <div class="stat-card">
                        <h3>Added Genes</h3>
                        <p class="added">${stats.added}</p>
                    </div>
                    <div class="stat-card">
                        <h3>Removed Genes</h3>
                        <p class="removed">${stats.removed}</p>
                    </div>
                    <div class="stat-card">
                        <h3>Modified Genes</h3>
                        <p class="modified">${stats.modified}</p>
                    </div>
                    <div class="stat-card">
                        <h3>Change Percentage</h3>
                        <p>${stats.changePercentage}%</p>
                    </div>
                </div>
                
                <!-- Add detailed sections here -->
                
            </body>
            </html>
        `;
    }

    // Utility methods
    formatFieldName(fieldName) {
        return fieldName.split('_').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
}

// Global reference for diff viewer operations
let diffViewer;
