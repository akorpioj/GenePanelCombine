/**
 * Profile Management Module
 * Handles user profile tabs
 */

export class ProfileManager {
    constructor() {
        this.currentPage = 1;
        this.totalPages = 1;
        this.isLoading = false;
        this.searchTimeout = null;
        
        this.initializeElements();
        this.bindEvents();
        this.initializeTimezone();
    }
    
    initializeElements() {
        // Navigation elements
        this.profileNav = document.getElementById('profile-nav');
        this.panelsNav = document.getElementById('panels-nav');
        this.profileContent = document.getElementById('profile-content');
        this.panelsContent = document.getElementById('panels-content');        
    }
    
    bindEvents() {
        // Navigation switching
        if (this.profileNav) {
            this.profileNav.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchTab('profile');
            });
        }
        
        if (this.panelsNav) {
            this.panelsNav.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchTab('panels');                
            });
        }                
    }
    
    switchTab(tab) {
        if (tab === 'profile') {
            // Update profile nav to active state
            this.profileNav?.classList.remove('text-gray-500', 'hover:text-gray-700');
            this.profileNav?.classList.add('bg-sky-100', 'text-sky-700');
            
            // Update panels nav to inactive state
            this.panelsNav?.classList.remove('bg-sky-100', 'text-sky-700');
            this.panelsNav?.classList.add('text-gray-500', 'hover:text-gray-700');
            
            // Show/hide content
            this.profileContent?.classList.remove('hidden');
            this.panelsContent?.classList.add('hidden');
        } else {
            // Update panels nav to active state
            this.panelsNav?.classList.remove('text-gray-500', 'hover:text-gray-700');
            this.panelsNav?.classList.add('bg-sky-100', 'text-sky-700');
            
            // Update profile nav to inactive state
            this.profileNav?.classList.remove('bg-sky-100', 'text-sky-700');
            this.profileNav?.classList.add('text-gray-500', 'hover:text-gray-700');
            
            // Show/hide content
            this.panelsContent?.classList.remove('hidden');
            this.profileContent?.classList.add('hidden');
        }
    }
    
    // Utility methods
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, function(m) { return map[m]; });
    }
    
    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        
        if (days === 0) return 'today';
        if (days === 1) return 'yesterday';
        if (days < 7) return `${days} days ago`;
        if (days < 30) return `${Math.floor(days / 7)} weeks ago`;
        if (days < 365) return `${Math.floor(days / 30)} months ago`;
        return `${Math.floor(days / 365)} years ago`;
    }
    
    showSuccess(message) {
        // Simple alert for now - could be replaced with a proper toast notification
        alert(message);
    }
    
    showError(message) {
        // Simple alert for now - could be replaced with a proper toast notification
        alert('Error: ' + message);
    }
    
    initializeTimezone() {
        // Initialize timezone display for profile tab
        const userTimeElement = document.getElementById('current-user-time');
        if (userTimeElement) {
            const updateUserTime = () => {
                const now = new Date();
                const timeString = now.toLocaleTimeString();
                userTimeElement.textContent = timeString;
            };
            updateUserTime();
            setInterval(updateUserTime, 1000);
        }
    }
}

// Initialize profile manager when DOM is loaded
export function initializeProfileManager() {
    return new ProfileManager();
}
