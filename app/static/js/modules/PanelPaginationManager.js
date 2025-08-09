/**
 * Panel Pagination Manager
 * Handles pagination logic for both server and client-side pagination
 */
class PanelPaginationManager {
    constructor(panelLibrary) {
        this.panelLibrary = panelLibrary;
    }

    renderPagination() {
        // Check for different possible pagination container IDs
        let paginationContainer = document.getElementById('panel-pagination');
        if (!paginationContainer) {
            paginationContainer = document.getElementById('panels-pagination');
        }
        
        if (!paginationContainer) return;

        let totalPages, currentPage;
        
        if (this.panelLibrary.useServerPagination && this.panelLibrary.serverPagination) {
            // Use server pagination data
            totalPages = this.panelLibrary.serverPagination.pages;
            currentPage = this.panelLibrary.serverPagination.page;
        } else {
            // Use client-side pagination
            totalPages = Math.ceil(this.panelLibrary.filteredPanels.length / this.panelLibrary.pageSize);
            currentPage = this.panelLibrary.currentPage;
        }
        
        if (totalPages <= 1) {
            paginationContainer.innerHTML = '';
            return;
        }

        let pagination = '<nav><ul class="pagination">';
        
        // Previous button
        pagination += `
            <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="panelLibrary.goToPage(${currentPage - 1})">Previous</a>
            </li>
        `;
        
        // Page numbers
        for (let i = 1; i <= totalPages; i++) {
            if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
                pagination += `
                    <li class="page-item ${i === currentPage ? 'active' : ''}">
                        <a class="page-link" href="#" onclick="panelLibrary.goToPage(${i})">${i}</a>
                    </li>
                `;
            } else if (i === currentPage - 3 || i === currentPage + 3) {
                pagination += '<li class="page-item disabled"><span class="page-link">...</span></li>';
            }
        }
        
        // Next button
        pagination += `
            <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="panelLibrary.goToPage(${currentPage + 1})">Next</a>
            </li>
        `;
        
        pagination += '</ul></nav>';
        paginationContainer.innerHTML = pagination;
    }

    goToPage(page) {
        if (this.panelLibrary.useServerPagination && this.panelLibrary.serverPagination) {
            // Server-side pagination
            const totalPages = this.panelLibrary.serverPagination.pages;
            if (page < 1 || page > totalPages) return;
            
            this.panelLibrary.currentPage = page;
            this.panelLibrary.loadPanels(page, true);
        } else {
            // Client-side pagination
            const totalPages = Math.ceil(this.panelLibrary.filteredPanels.length / this.panelLibrary.pageSize);
            if (page < 1 || page > totalPages) return;
            
            this.panelLibrary.currentPage = page;
            this.panelLibrary.render();
        }
    }
}
