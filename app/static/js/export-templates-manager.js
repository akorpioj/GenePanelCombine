/**
 * Export Templates Management for Profile Page
 * Handles loading, displaying, editing, and deleting export templates
 */

class ExportTemplatesManager {
    constructor() {
        this.templates = [];
        this.currentTab = 'profile';
        this.init();
    }

    init() {
        // Tab navigation
        this.setupTabNavigation();
        
        // Check for hash fragment on load
        if (window.location.hash === '#templates') {
            setTimeout(() => {
                document.getElementById('templates-nav')?.click();
            }, 100);
        }
        
        // Load templates when templates tab is clicked
        document.getElementById('templates-nav')?.addEventListener('click', () => {
            this.loadTemplates();
        });
        
        // Create template buttons
        document.getElementById('create-template-btn')?.addEventListener('click', () => {
            this.showCreateTemplateDialog();
        });
        
        document.querySelectorAll('.create-template-trigger').forEach(btn => {
            btn.addEventListener('click', () => {
                this.showCreateTemplateDialog();
            });
        });
    }

    setupTabNavigation() {
        const tabs = {
            'profile-nav': 'profile-content',
            'panels-nav': 'panels-content',
            'templates-nav': 'templates-content'
        };

        Object.keys(tabs).forEach(navId => {
            const navElement = document.getElementById(navId);
            if (navElement) {
                navElement.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.switchTab(navId, tabs);
                });
            }
        });
    }

    switchTab(activeNavId, tabs) {
        // Update nav styling
        Object.keys(tabs).forEach(navId => {
            const navElement = document.getElementById(navId);
            if (navId === activeNavId) {
                navElement.classList.remove('text-gray-500', 'hover:text-gray-700');
                navElement.classList.add('bg-sky-100', 'text-sky-700');
            } else {
                navElement.classList.remove('bg-sky-100', 'text-sky-700');
                navElement.classList.add('text-gray-500', 'hover:text-gray-700');
            }
        });

        // Show/hide content
        Object.values(tabs).forEach(contentId => {
            const contentElement = document.getElementById(contentId);
            if (tabs[activeNavId] === contentId) {
                contentElement.classList.remove('hidden');
            } else {
                contentElement.classList.add('hidden');
            }
        });

        this.currentTab = activeNavId.replace('-nav', '');
    }

    async loadTemplates() {
        const loadingEl = document.getElementById('templates-loading');
        const listEl = document.getElementById('templates-list');
        const emptyEl = document.getElementById('templates-empty');

        // Show loading state
        loadingEl.classList.remove('hidden');
        listEl.classList.add('hidden');
        emptyEl.classList.add('hidden');

        try {
            const response = await fetch('/api/user/export-templates');
            if (!response.ok) throw new Error('Failed to load templates');

            const data = await response.json();
            this.templates = data.templates || [];

            // Hide loading
            loadingEl.classList.add('hidden');

            if (this.templates.length === 0) {
                emptyEl.classList.remove('hidden');
            } else {
                this.renderTemplates();
                listEl.classList.remove('hidden');
            }
        } catch (error) {
            console.error('Error loading templates:', error);
            loadingEl.innerHTML = `
                <div class="text-center text-red-500">
                    <i class="fas fa-exclamation-triangle text-2xl mb-2"></i>
                    <p>Failed to load templates. Please try again.</p>
                </div>
            `;
        }
    }

    renderTemplates() {
        const listEl = document.getElementById('templates-list');
        
        const templatesHTML = this.templates.map((template, index) => `
            <div class="template-item ${index % 2 === 0 ? 'bg-white' : 'bg-gray-50'} px-4 py-5 sm:px-6 border-b border-gray-200 hover:bg-blue-50 transition-colors">
                <div class="flex items-center justify-between">
                    <div class="flex-1">
                        <div class="flex items-center">
                            <h4 class="text-base font-medium text-gray-900">
                                ${template.name}
                                ${template.is_default ? '<span class="ml-2 text-yellow-500" title="Default template">⭐</span>' : ''}
                            </h4>
                            <span class="ml-3 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                                ${this.getFormatBadgeClass(template.format)}">
                                ${template.format.toUpperCase()}
                            </span>
                        </div>
                        ${template.description ? `<p class="mt-1 text-sm text-gray-500">${template.description}</p>` : ''}
                        
                        <div class="mt-2 flex items-center text-xs text-gray-500 space-x-4">
                            <span>
                                <i class="fas fa-clock mr-1"></i>
                                Created ${this.formatDate(template.created_at)}
                            </span>
                            ${template.last_used_at ? `
                                <span>
                                    <i class="fas fa-history mr-1"></i>
                                    Last used ${this.formatDate(template.last_used_at)}
                                </span>
                            ` : ''}
                            <span>
                                <i class="fas fa-chart-line mr-1"></i>
                                Used ${template.usage_count} time${template.usage_count !== 1 ? 's' : ''}
                            </span>
                        </div>
                        
                        <div class="mt-2 flex items-center text-xs text-gray-600 space-x-3">
                            <span class="${template.include_metadata ? 'text-green-600' : 'text-gray-400'}">
                                <i class="fas ${template.include_metadata ? 'fa-check' : 'fa-times'} mr-1"></i>
                                Metadata
                            </span>
                            <span class="${template.include_versions ? 'text-green-600' : 'text-gray-400'}">
                                <i class="fas ${template.include_versions ? 'fa-check' : 'fa-times'} mr-1"></i>
                                Versions
                            </span>
                            <span class="${template.include_genes ? 'text-green-600' : 'text-gray-400'}">
                                <i class="fas ${template.include_genes ? 'fa-check' : 'fa-times'} mr-1"></i>
                                Genes
                            </span>
                        </div>
                    </div>
                    
                    <div class="ml-4 flex items-center space-x-2">
                        ${!template.is_default ? `
                            <button onclick="templatesManager.setAsDefault(${template.id})" 
                                    class="text-gray-600 hover:text-yellow-600 p-2 rounded hover:bg-yellow-50" 
                                    title="Set as default">
                                <i class="fas fa-star"></i>
                            </button>
                        ` : ''}
                        <button onclick="templatesManager.editTemplate(${template.id})" 
                                class="text-blue-600 hover:text-blue-800 p-2 rounded hover:bg-blue-50" 
                                title="Edit template">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button onclick="templatesManager.deleteTemplate(${template.id}, '${template.name.replace(/'/g, "\\'")}')" 
                                class="text-red-600 hover:text-red-800 p-2 rounded hover:bg-red-50" 
                                title="Delete template">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');

        listEl.innerHTML = templatesHTML;
    }

    getFormatBadgeClass(format) {
        switch (format.toLowerCase()) {
            case 'excel': return 'bg-green-100 text-green-800';
            case 'csv': return 'bg-blue-100 text-blue-800';
            case 'tsv': return 'bg-purple-100 text-purple-800';
            case 'json': return 'bg-orange-100 text-orange-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    }

    formatDate(dateString) {
        if (!dateString) return 'Never';
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffDays === 0) return 'Today';
        if (diffDays === 1) return 'Yesterday';
        if (diffDays < 7) return `${diffDays} days ago`;
        if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
        if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
        return `${Math.floor(diffDays / 365)} years ago`;
    }

    showCreateTemplateDialog() {
        const dialogHTML = `
            <div id="template-dialog" class="fixed inset-0 bg-gray-600 bg-opacity-50 z-50 flex items-center justify-center">
                <div class="bg-white p-6 rounded-md shadow-lg w-full max-w-md max-h-[90vh] overflow-y-auto">
                    <h3 class="text-lg font-medium mb-4">Create Export Template</h3>
                    <form id="template-form">
                        <div class="space-y-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">Template Name*</label>
                                <input type="text" id="template-name" required
                                       class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                                       placeholder="e.g., My Excel Export">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
                                <input type="text" id="template-description"
                                       class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                                       placeholder="Optional description">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">Export Format*</label>
                                <div class="space-y-2">
                                    <label class="flex items-center p-2 border rounded cursor-pointer hover:bg-gray-50">
                                        <input type="radio" name="format" value="excel" checked class="mr-2">
                                        <span class="text-sm">Excel (.xlsx)</span>
                                    </label>
                                    <label class="flex items-center p-2 border rounded cursor-pointer hover:bg-gray-50">
                                        <input type="radio" name="format" value="csv" class="mr-2">
                                        <span class="text-sm">CSV (.csv)</span>
                                    </label>
                                    <label class="flex items-center p-2 border rounded cursor-pointer hover:bg-gray-50">
                                        <input type="radio" name="format" value="tsv" class="mr-2">
                                        <span class="text-sm">TSV (.tsv)</span>
                                    </label>
                                    <label class="flex items-center p-2 border rounded cursor-pointer hover:bg-gray-50">
                                        <input type="radio" name="format" value="json" class="mr-2">
                                        <span class="text-sm">JSON (.json)</span>
                                    </label>
                                </div>
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">Include Options</label>
                                <div class="space-y-2">
                                    <label class="flex items-center text-sm">
                                        <input type="checkbox" id="include-metadata" checked class="mr-2">
                                        Include panel metadata
                                    </label>
                                    <label class="flex items-center text-sm">
                                        <input type="checkbox" id="include-versions" checked class="mr-2">
                                        Include version history
                                    </label>
                                    <label class="flex items-center text-sm">
                                        <input type="checkbox" id="include-genes" checked class="mr-2">
                                        Include gene data
                                    </label>
                                </div>
                            </div>
                            <div>
                                <label class="flex items-center text-sm">
                                    <input type="checkbox" id="is-default" class="mr-2">
                                    Set as default template
                                </label>
                            </div>
                        </div>
                        <div class="flex justify-end space-x-3 mt-6">
                            <button type="button" id="cancel-template" class="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400">
                                Cancel
                            </button>
                            <button type="submit" id="save-template" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
                                <i class="fas fa-save mr-2"></i>Create Template
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', dialogHTML);

        document.getElementById('cancel-template').addEventListener('click', () => {
            document.getElementById('template-dialog').remove();
        });

        document.getElementById('template-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.createTemplate();
        });
    }

    async createTemplate() {
        const name = document.getElementById('template-name').value.trim();
        const description = document.getElementById('template-description').value.trim();
        const format = document.querySelector('input[name="format"]:checked').value;
        const includeMetadata = document.getElementById('include-metadata').checked;
        const includeVersions = document.getElementById('include-versions').checked;
        const includeGenes = document.getElementById('include-genes').checked;
        const isDefault = document.getElementById('is-default').checked;

        const saveBtn = document.getElementById('save-template');
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Creating...';

        try {
            const response = await fetch('/api/user/export-templates', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name,
                    description,
                    format,
                    include_metadata: includeMetadata,
                    include_versions: includeVersions,
                    include_genes: includeGenes,
                    is_default: isDefault
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to create template');
            }

            document.getElementById('template-dialog').remove();
            this.showSuccess('Template created successfully!');
            await this.loadTemplates();
        } catch (error) {
            console.error('Error creating template:', error);
            alert(error.message);
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<i class="fas fa-save mr-2"></i>Create Template';
        }
    }

    async editTemplate(templateId) {
        const template = this.templates.find(t => t.id === templateId);
        if (!template) return;

        // Similar to create but pre-populate with existing values
        const dialogHTML = `
            <div id="template-dialog" class="fixed inset-0 bg-gray-600 bg-opacity-50 z-50 flex items-center justify-center">
                <div class="bg-white p-6 rounded-md shadow-lg w-full max-w-md max-h-[90vh] overflow-y-auto">
                    <h3 class="text-lg font-medium mb-4">Edit Export Template</h3>
                    <form id="template-form">
                        <div class="space-y-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">Template Name*</label>
                                <input type="text" id="template-name" required value="${template.name}"
                                       class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
                                <input type="text" id="template-description" value="${template.description || ''}"
                                       class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">Export Format*</label>
                                <div class="space-y-2">
                                    ${['excel', 'csv', 'tsv', 'json'].map(fmt => `
                                        <label class="flex items-center p-2 border rounded cursor-pointer hover:bg-gray-50">
                                            <input type="radio" name="format" value="${fmt}" ${template.format === fmt ? 'checked' : ''} class="mr-2">
                                            <span class="text-sm">${fmt.toUpperCase()}</span>
                                        </label>
                                    `).join('')}
                                </div>
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">Include Options</label>
                                <div class="space-y-2">
                                    <label class="flex items-center text-sm">
                                        <input type="checkbox" id="include-metadata" ${template.include_metadata ? 'checked' : ''} class="mr-2">
                                        Include panel metadata
                                    </label>
                                    <label class="flex items-center text-sm">
                                        <input type="checkbox" id="include-versions" ${template.include_versions ? 'checked' : ''} class="mr-2">
                                        Include version history
                                    </label>
                                    <label class="flex items-center text-sm">
                                        <input type="checkbox" id="include-genes" ${template.include_genes ? 'checked' : ''} class="mr-2">
                                        Include gene data
                                    </label>
                                </div>
                            </div>
                            <div>
                                <label class="flex items-center text-sm">
                                    <input type="checkbox" id="is-default" ${template.is_default ? 'checked' : ''} class="mr-2">
                                    Set as default template
                                </label>
                            </div>
                        </div>
                        <div class="flex justify-end space-x-3 mt-6">
                            <button type="button" id="cancel-template" class="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400">
                                Cancel
                            </button>
                            <button type="submit" id="save-template" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
                                <i class="fas fa-save mr-2"></i>Save Changes
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', dialogHTML);

        document.getElementById('cancel-template').addEventListener('click', () => {
            document.getElementById('template-dialog').remove();
        });

        document.getElementById('template-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.updateTemplate(templateId);
        });
    }

    async updateTemplate(templateId) {
        const name = document.getElementById('template-name').value.trim();
        const description = document.getElementById('template-description').value.trim();
        const format = document.querySelector('input[name="format"]:checked').value;
        const includeMetadata = document.getElementById('include-metadata').checked;
        const includeVersions = document.getElementById('include-versions').checked;
        const includeGenes = document.getElementById('include-genes').checked;
        const isDefault = document.getElementById('is-default').checked;

        const saveBtn = document.getElementById('save-template');
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Saving...';

        try {
            const response = await fetch(`/api/user/export-templates/${templateId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name,
                    description,
                    format,
                    include_metadata: includeMetadata,
                    include_versions: includeVersions,
                    include_genes: includeGenes,
                    is_default: isDefault
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to update template');
            }

            document.getElementById('template-dialog').remove();
            this.showSuccess('Template updated successfully!');
            await this.loadTemplates();
        } catch (error) {
            console.error('Error updating template:', error);
            alert(error.message);
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<i class="fas fa-save mr-2"></i>Save Changes';
        }
    }

    async deleteTemplate(templateId, templateName) {
        if (!confirm(`Are you sure you want to delete the template "${templateName}"? This action cannot be undone.`)) {
            return;
        }

        try {
            const response = await fetch(`/api/user/export-templates/${templateId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to delete template');
            }

            this.showSuccess('Template deleted successfully!');
            await this.loadTemplates();
        } catch (error) {
            console.error('Error deleting template:', error);
            alert(error.message);
        }
    }

    async setAsDefault(templateId) {
        try {
            const response = await fetch(`/api/user/export-templates/${templateId}/set-default`, {
                method: 'POST'
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to set default template');
            }

            this.showSuccess('Default template updated!');
            await this.loadTemplates();
        } catch (error) {
            console.error('Error setting default template:', error);
            alert(error.message);
        }
    }

    showSuccess(message) {
        // Simple success notification
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-md shadow-lg z-50';
        notification.innerHTML = `<i class="fas fa-check-circle mr-2"></i>${message}`;
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

// Initialize when DOM is ready
let templatesManager;
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        templatesManager = new ExportTemplatesManager();
    });
} else {
    templatesManager = new ExportTemplatesManager();
}
