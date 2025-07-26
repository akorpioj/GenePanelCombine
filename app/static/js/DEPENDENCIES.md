# Module Dependency Graph

```
main.js
├── modules/api.js
│   ├── modules/state.js
│   └── modules/panelManager.js (dynamic import)
├── modules/panelManager.js
│   ├── modules/state.js
│   ├── modules/utils.js
│   └── modules/api.js
├── modules/autocomplete.js
│   ├── modules/state.js
│   ├── modules/utils.js
│   ├── modules/api.js
│   └── modules/panelManager.js
├── modules/fileUpload.js
│   ├── modules/state.js
│   └── modules/api.js
└── modules/panelComparison.js
    ├── modules/api.js
    └── modules/panelManager.js
```

## Module Relationships

### Core Dependencies
- **state.js**: Foundation module with no dependencies
- **utils.js**: Foundation module with minimal dependencies (state.js)

### API Layer
- **api.js**: Handles external communications, depends on state.js

### Feature Modules
- **panelManager.js**: Core panel logic, depends on state, utils, and api
- **autocomplete.js**: Search features, depends on multiple core modules
- **fileUpload.js**: Upload functionality, depends on state and api
- **panelComparison.js**: Comparison features, depends on api and panelManager

### Entry Point
- **main.js**: Orchestrates everything, imports from all feature modules

## Circular Dependency Resolution

The original circular dependency between `api.js` and `panelManager.js` is resolved using dynamic imports:

```javascript
// In api.js
import('./panelManager.js').then(module => {
    module.populateAll().catch(console.error);
});
```

This ensures that the module system can load properly while maintaining the required functionality.
