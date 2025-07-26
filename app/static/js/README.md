# PanelMerge - Modular JavaScript Architecture

This directory contains the modularized JavaScript codebase for the PanelMerge application, split from the original monolithic `panels.js` file into logical, maintainable modules.

## Module Structure

### `main.js` - Application Entry Point
- **Purpose**: Main entry point that imports and initializes all modules
- **Responsibilities**: 
  - Coordinate module initialization
  - Expose global functions for HTML onclick handlers
  - Initialize data fetching on app start

### `modules/state.js` - Global State Management
- **Purpose**: Centralized state management and configuration
- **Exports**:
  - `allPanels`: Global panels data store
  - `currentAPI`: Current API source (uk/aus/upload)
  - `maxPanels`: Maximum number of panels allowed
  - `listTypeOptions`: Available list type options
  - `fieldsToSearch`: Search configuration
- **Functions**:
  - `setCurrentAPI()`: Update current API source
  - `updatePanels()`: Update panels data
  - `getCurrentPanels()`: Get current panels
  - `getAllPanels()`: Get all panels

### `modules/utils.js` - Utility Functions
- **Purpose**: Common utility functions used across modules
- **Functions**:
  - `debounce()`: Debounce function calls
  - `matches()`: Check if panel matches search term

### `modules/api.js` - API Management
- **Purpose**: Handle all API communications and data fetching
- **Functions**:
  - `fetchPanels()`: Fetch panels from API
  - `switchAPI()`: Switch between API sources
  - `fetchGeneSuggestions()`: Get gene autocomplete suggestions
  - `fetchPanelsByGene()`: Get panels containing a gene
  - `fetchPanelDetails()`: Get detailed panel information
  - `fetchUploadedFiles()`: Get uploaded user files
  - `uploadPanelFiles()`: Upload files to server
  - `removeUserPanel()`: Remove uploaded file

### `modules/panelManager.js` - Panel Management
- **Purpose**: Handle panel selection, filtering, and UI updates
- **Functions**:
  - `setLoadingState()`: Set loading state for panel dropdowns
  - `populateAll()`: Populate panel dropdowns with filtered results
  - `updateSelectOptions()`: Update select element options
  - `clearPanel()`: Clear specific panel selection
  - `clearAll()`: Clear all selections
  - `getSelectedPanels()`: Get currently selected panels

### `modules/autocomplete.js` - Autocomplete Functionality
- **Purpose**: Gene search autocomplete and suggestions
- **Functions**:
  - `initializeAutocomplete()`: Setup autocomplete functionality

### `modules/fileUpload.js` - File Upload
- **Purpose**: Handle drag-and-drop uploads and file management
- **Functions**:
  - `initializeDragAndDrop()`: Setup drag-and-drop interface
  - `initializeFileUpload()`: Setup file upload functionality

### `modules/panelComparison.js` - Panel Comparison
- **Purpose**: Side-by-side panel comparison and modal interface
- **Functions**:
  - `openPanelComparison()`: Open comparison modal
  - `closePanelComparison()`: Close comparison modal
  - `proceedWithSelection()`: Continue with current selection

## Key Benefits

### 1. **Separation of Concerns**
Each module has a single, well-defined responsibility, making the codebase easier to understand and maintain.

### 2. **Dependency Management**
Clear import/export statements make dependencies explicit and prevent circular dependencies.

### 3. **Reusability**
Individual modules can be easily reused or replaced without affecting other parts of the application.

### 4. **Testing**
Modular structure enables unit testing of individual components.

### 5. **Code Organization**
Related functionality is grouped together, making it easier to locate and modify specific features.

### 6. **Maintainability**
Changes to one module don't require understanding the entire codebase, reducing maintenance overhead.

### 7. **User Experience**
Loading states provide visual feedback to users while data is being fetched from APIs.

## Usage

The application uses ES6 modules, so the HTML template includes:
```html
<script type="module" src="{{ url_for('static', filename='js/main.js') }}"></script>
```

Global variables from the template (maxPanels, listTypeOptions) are automatically picked up by the state module.

## Loading States

The application now includes user-friendly loading states for panel dropdowns:

### Implementation
- Panel dropdowns show "Loading panels..." when data is being fetched
- Loading option is disabled and visually distinct (grayed out, italic text)
- Loading state automatically clears when real data is populated
- Smart detection prevents showing loading state when data is already available

### Technical Details
- HTML templates include initial `<option value="Loading" disabled selected>Loading panels...</option>`
- `setLoadingState()` function manages loading state display
- CSS styles provide visual distinction for loading states
- Loading state is shown during API source switches and initial page load

## Migration Notes

- Original `panels.js` has been backed up as `panels.js.backup`
- All functionality remains identical to the original implementation
- Global functions required by HTML onclick handlers are exposed via `window` object in `main.js`
- Circular dependencies are resolved using dynamic imports where necessary

## Development

When adding new features:
1. Determine which module is most appropriate for the new functionality
2. Add exports to the relevant module
3. Import the function in modules that need to use it
4. Update this README if adding new modules or major functionality
