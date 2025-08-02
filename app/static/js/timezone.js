/**
 * Timezone Detection and Management
 * Automatically detects user's timezone and provides timezone selection functionality
 */

class TimezoneManager {
    constructor() {
        this.detectedTimezone = null;
        this.currentTimezone = null;
        this.init();
    }

    /**
     * Initialize timezone detection and management
     */
    init() {
        this.detectTimezone();
        this.setupEventListeners();
        this.updateTimestampsOnPage();
        
        // Auto-update timestamps every minute
        setInterval(() => {
            this.updateTimestampsOnPage();
        }, 60000);
    }

    /**
     * Detect user's timezone using JavaScript Intl API
     */
    detectTimezone() {
        try {
            // Modern browsers support Intl.DateTimeFormat().resolvedOptions().timeZone
            if (Intl && Intl.DateTimeFormat) {
                this.detectedTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
                console.log('Detected timezone:', this.detectedTimezone);
                
                // Send detected timezone to server
                this.sendTimezoneToServer(this.detectedTimezone, 'detect');
            } else {
                console.warn('Timezone detection not supported in this browser');
            }
        } catch (error) {
            console.error('Error detecting timezone:', error);
        }
    }

    /**
     * Send timezone information to server
     * @param {string} timezone - IANA timezone name
     * @param {string} endpoint - API endpoint ('detect' or 'set')
     */
    async sendTimezoneToServer(timezone, endpoint = 'set') {
        try {
            const response = await fetch(`/api/timezone/${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ timezone: timezone })
            });

            const result = await response.json();
            
            if (result.success) {
                this.currentTimezone = timezone;
                console.log(`Timezone ${endpoint}:`, timezone);
                
                // Update timestamps on page after timezone change
                if (endpoint === 'set') {
                    this.updateTimestampsOnPage();
                }
            } else {
                console.error('Failed to set timezone:', result.error);
            }
        } catch (error) {
            console.error('Error sending timezone to server:', error);
        }
    }

    /**
     * Get current timezone information from server
     */
    async getCurrentTimezone() {
        try {
            const response = await fetch('/api/timezone/current');
            const result = await response.json();
            
            if (result.success) {
                this.currentTimezone = result.timezone;
                return result;
            } else {
                console.error('Failed to get current timezone:', result.error);
                return null;
            }
        } catch (error) {
            console.error('Error getting current timezone:', error);
            return null;
        }
    }

    /**
     * Get available timezones from server
     */
    async getAvailableTimezones() {
        try {
            const response = await fetch('/api/timezone/available');
            const result = await response.json();
            
            if (result.success) {
                return result.timezones;
            } else {
                console.error('Failed to get available timezones:', result.error);
                return [];
            }
        } catch (error) {
            console.error('Error getting available timezones:', error);
            return [];
        }
    }

    /**
     * Update all timestamps on the current page
     */
    updateTimestampsOnPage() {
        // Update current time display
        this.updateCurrentTimeDisplay();
        
        // Find all elements with data-timestamp attribute
        const timestampElements = document.querySelectorAll('[data-timestamp]');
        
        timestampElements.forEach(element => {
            const isoTimestamp = element.getAttribute('data-timestamp');
            const format = element.getAttribute('data-format') || 'datetime';
            
            try {
                const date = new Date(isoTimestamp);
                const formattedTime = this.formatTimestamp(date, format);
                element.textContent = formattedTime;
            } catch (error) {
                console.error('Error formatting timestamp:', error);
            }
        });
    }

    /**
     * Update current time display elements
     */
    updateCurrentTimeDisplay() {
        const currentTimeElements = document.querySelectorAll('#current-user-time');
        const now = new Date();
        
        console.log('Updating current time display, found elements:', currentTimeElements.length);
        
        currentTimeElements.forEach(element => {
            try {
                const formattedTime = this.formatTimestamp(now, 'datetime');
                console.log('Setting current time to:', formattedTime);
                element.textContent = formattedTime;
            } catch (error) {
                console.error('Error updating current time display:', error);
                element.textContent = now.toLocaleString();
            }
        });
    }

    /**
     * Format timestamp according to user's locale and timezone
     * @param {Date} date - JavaScript Date object
     * @param {string} format - Format type ('datetime', 'date', 'time', 'relative')
     */
    formatTimestamp(date, format = 'datetime') {
        const options = {
            timeZone: this.currentTimezone || this.detectedTimezone || 'UTC'
        };

        switch (format) {
            case 'date':
                return date.toLocaleDateString(undefined, {
                    ...options,
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                });
            
            case 'time':
                return date.toLocaleTimeString(undefined, {
                    ...options,
                    hour: '2-digit',
                    minute: '2-digit'
                });
            
            case 'datetime':
                return date.toLocaleString(undefined, {
                    ...options,
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            
            case 'relative':
                return this.formatRelativeTime(date);
            
            default:
                return date.toLocaleString(undefined, options);
        }
    }

    /**
     * Format timestamp as relative time (e.g., "2 hours ago")
     * @param {Date} date - JavaScript Date object
     */
    formatRelativeTime(date) {
        const now = new Date();
        const diffMs = now - date;
        const diffSecs = Math.floor(diffMs / 1000);
        const diffMins = Math.floor(diffSecs / 60);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);

        if (diffSecs < 60) {
            return 'Just now';
        } else if (diffMins < 60) {
            return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
        } else if (diffHours < 24) {
            return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
        } else if (diffDays < 7) {
            return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
        } else {
            // For longer periods, show the actual date
            return this.formatTimestamp(date, 'date');
        }
    }

    /**
     * Create timezone selector dropdown
     * @param {HTMLElement} container - Container element for the selector
     */
    async createTimezoneSelector(container) {
        const timezones = await this.getAvailableTimezones();
        const currentTz = await this.getCurrentTimezone();
        
        const selectElement = document.createElement('select');
        selectElement.className = 'timezone-selector';
        selectElement.id = 'timezone-select';
        
        timezones.forEach(tz => {
            const option = document.createElement('option');
            option.value = tz.name;
            option.textContent = `${tz.display_name} (${tz.current_time})`;
            
            if (currentTz && tz.name === currentTz.timezone) {
                option.selected = true;
            }
            
            selectElement.appendChild(option);
        });
        
        // Add change event listener
        selectElement.addEventListener('change', (event) => {
            this.sendTimezoneToServer(event.target.value, 'set');
        });
        
        container.appendChild(selectElement);
    }

    /**
     * Setup event listeners for timezone-related functionality
     */
    setupEventListeners() {
        // Listen for timezone selector containers
        document.addEventListener('DOMContentLoaded', () => {
            const selectorContainers = document.querySelectorAll('.timezone-selector-container');
            selectorContainers.forEach(container => {
                this.createTimezoneSelector(container);
            });
        });

        // Listen for manual timezone updates
        document.addEventListener('timezoneChanged', (event) => {
            this.sendTimezoneToServer(event.detail.timezone, 'set');
        });
    }

    /**
     * Manually set timezone (can be called from other scripts)
     * @param {string} timezone - IANA timezone name
     */
    setTimezone(timezone) {
        this.sendTimezoneToServer(timezone, 'set');
    }

    /**
     * Get current detected timezone
     */
    getDetectedTimezone() {
        return this.detectedTimezone;
    }

    /**
     * Get current active timezone
     */
    getCurrentActiveTimezone() {
        return this.currentTimezone || this.detectedTimezone;
    }
}

// Global instance - Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.timezoneManager = new TimezoneManager();
});

// Helper function to convert server timestamps to user timezone
window.formatUserTimestamp = function(isoString, format = 'datetime') {
    try {
        const date = new Date(isoString);
        return window.timezoneManager ? window.timezoneManager.formatTimestamp(date, format) : new Date(isoString).toLocaleString();
    } catch (error) {
        console.error('Error formatting timestamp:', error);
        return isoString;
    }
};

// Helper function to get current time in user timezone
window.getCurrentUserTime = function() {
    const now = new Date();
    return window.timezoneManager ? window.timezoneManager.formatTimestamp(now, 'datetime') : now.toLocaleString();
};
