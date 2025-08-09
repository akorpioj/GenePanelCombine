// Profile page bootstrapper: initializes the profile manager and page helpers
import { initializeProfileManager } from '../modules/profileManager.js';

function bootstrap() {
  try {
    initializeProfileManager();
  } catch (err) {
    console.error('Failed to initialize profile manager:', err);
  }

  // Simple notification helper used by the page
  if (!window.showNotification) {
    window.showNotification = function (message, type = 'info') {
      const containerId = 'notification-container';
      let container = document.getElementById(containerId);
      if (!container) {
        container = document.createElement('div');
        container.id = containerId;
        container.style.position = 'fixed';
        container.style.top = '1rem';
        container.style.right = '1rem';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
      }

      const note = document.createElement('div');
      note.className = `mb-2 px-3 py-2 rounded shadow text-sm ${
        type === 'error'
          ? 'bg-red-100 text-red-800 border border-red-200'
          : type === 'success'
          ? 'bg-green-100 text-green-800 border border-green-200'
          : 'bg-blue-100 text-blue-800 border border-blue-200'
      }`;
      note.textContent = message;
      container.appendChild(note);
      setTimeout(() => note.remove(), 4000);
    };
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', bootstrap);
} else {
  bootstrap();
}
