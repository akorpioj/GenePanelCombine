# Version Timeline Feature Documentation

## Overview

The **Version Timeline** feature provides a comprehensive visual representation of panel evolution over time, allowing users to:
- View the complete version history in a graphical timeline
- Track changes and understand panel evolution
- Identify important versions through tags and protection status
- Restore previous versions when needed
- Compare versions to see what changed
- Navigate branch structures visually

## Features

### Visual Timeline Display

1. **Horizontal Timeline Layout**
   - Versions displayed chronologically from left to right
   - Smooth connectors between versions showing progression
   - Responsive design adapts to different screen sizes
   - Zoom controls for detailed exploration

2. **Version Nodes**
   - **Regular Versions**: Blue gradient circles
   - **Current Version**: Purple gradient with star icon (larger)
   - **Protected Versions**: Green gradient with shield icon
   - Interactive hover states for additional information

3. **Version Information**
   - Version number prominently displayed
   - Creation date (relative format: "2d ago", "3w ago")
   - Tags shown with yellow tag icons
   - Creator information
   - Gene count
   - Protection status

### Interactive Features

#### 1. **Hover Information Cards**

When hovering over a version node, a detailed information card appears showing:
- Full version number
- Creator's username
- Exact creation date and time
- Gene count
- Version comment/description
- Protection status indicator
- Current version indicator
- Associated tags

#### 2. **Click Actions**

Clicking on a version node opens a detailed modal with:
- **Full Version Details**:
  - Creator name and username
  - Precise timestamp
  - Gene count
  - Comment/description
  - Tags
  - Access statistics
  - Protection status

- **Action Buttons**:
  - **Restore This Version**: Creates new version from selected one
  - **View Changes**: Opens diff viewer to compare versions

#### 3. **Zoom Controls**

- **Zoom In** (+20% scale): For detailed examination
- **Zoom Out** (-20% scale): For overview
- **Reset**: Return to default zoom level

### Version Metadata Display

#### Version Labels
Each version displays:
```
v{number}
{relative date}
{tags (if any)}
```

Examples:
- `v1 | 3d ago`
- `v5 | Today | Production, Stable`
- `v12 | 2w ago | 🛡️ Protected`

#### Visual Indicators

| Indicator | Meaning | Color |
|-----------|---------|-------|
| Regular circle | Standard version | Blue (#3b82f6) |
| Large circle with ⭐ | Current version | Purple (#a855f7) |
| Circle with 🛡️ | Protected version | Green (#10b981) |
| 🏷️ Tag icon | Tagged version | Yellow (#f59e0b) |

### Timeline Statistics

The timeline header displays:
- Total number of versions
- Current panel name
- Panel ID (in development mode)

## User Workflows

### Viewing Timeline History

1. **Access Timeline**:
   - Navigate to "My Panels" in profile
   - Find desired panel in grid
   - Click "History" button on panel card
   
2. **Explore Timeline**:
   - Scroll horizontally to view all versions
   - Hover over nodes for quick information
   - Use zoom controls for detailed examination
   - Click nodes for full details

3. **Close Timeline**:
   - Click X button in header
   - Click outside modal (on backdrop)
   - Press Escape key

### Restoring Previous Versions

1. Click on the version you want to restore
2. In the details modal, click "Restore This Version"
3. Confirm the restoration
4. System creates new version with restored content
5. Timeline automatically refreshes

### Comparing Versions

1. Click on a version to view details
2. Click "View Changes" button
3. Diff viewer opens showing:
   - Genes added
   - Genes removed
   - Metadata changes
   - Version comments

## Technical Implementation

### Frontend Components

#### VersionTimelineViewer Class
**File**: `app/static/js/version-timeline-viewer.js`

**Key Methods**:
```javascript
// Show timeline for specific panel
show(panelId, panelName)

// Load version data from API
loadVersionData(panelId)

// Process versions to detect branches
processBranches()

// Render the timeline visualization
renderTimeline()

// Show detailed version information
showVersionDetails(versionNumber)

// Restore a specific version
restoreVersion(versionId, versionNumber)

// View differences between versions
viewVersionDiff(versionNumber)

// Zoom controls
adjustZoom(factor)
resetZoom()

// Close the viewer
close()
```

**Global Instance**:
```javascript
const versionTimelineViewer = new VersionTimelineViewer();
```

### Integration Points

#### 1. Profile Page Integration
**File**: `app/templates/auth/profile.html`

The script is loaded in the profile page:
```html
<script src="{{ url_for('static', filename='js/version-timeline-viewer.js') }}?v={{ cache_bust }}"></script>
```

#### 2. Panel Actions Manager
**File**: `app/static/js/modules/PanelActionsManager.js`

```javascript
async showVersionTimeline(panelId) {
    // Fetch panel name
    const response = await fetch(`/api/user/panels/${panelId}`);
    const data = await response.json();
    const panelName = data.panel?.name || 'Panel ' + panelId;
    
    // Show timeline
    await versionTimelineViewer.show(panelId, panelName);
}
```

#### 3. Panel Card Template
**File**: `app/static/partials/_panel_card.html`

History button:
```html
<button onclick="panelLibrary.showVersionTimeline({{PANEL_ID}})">
    <i class="fas fa-history"></i> History
</button>
```

### API Endpoints

#### Get Panel Versions
```
GET /api/user/panels/{panel_id}/versions
```

**Response**:
```json
{
    "versions": [
        {
            "version_number": 1,
            "created_at": "2024-01-15T10:30:00Z",
            "created_by": {
                "username": "jsmith",
                "full_name": "John Smith"
            },
            "gene_count": 150,
            "comment": "Initial panel creation",
            "is_protected": false,
            "tags": [
                {
                    "tag_name": "Production",
                    "color": "#10b981"
                }
            ],
            "metadata": {
                "branch": "main"
            },
            "access_count": 42,
            "last_accessed_at": "2024-01-20T14:22:00Z"
        }
    ]
}
```

#### Restore Version
```
POST /api/user/panels/{panel_id}/versions/{version_number}/restore
```

**Response**:
```json
{
    "message": "Version restored successfully",
    "new_version_number": 15
}
```

### CSS Styling

The timeline uses custom CSS with the following key features:

1. **Responsive Design**:
   - Adapts to screen size
   - Mobile-optimized node sizes
   - Flexible layout

2. **Smooth Animations**:
   - Hover effects with transitions
   - Zoom transitions
   - Fade in/out for info cards

3. **Visual Hierarchy**:
   - Current version stands out (larger, different color)
   - Protected versions clearly marked
   - Tags visually distinct

4. **Accessibility**:
   - High contrast colors
   - Clear hover states
   - Keyboard navigation support (via modal close with Escape)

### Data Flow

```
User clicks "History" button
    ↓
PanelActionsManager.showVersionTimeline(panelId)
    ↓
Fetch panel data for name
    ↓
versionTimelineViewer.show(panelId, panelName)
    ↓
loadVersionData(panelId) - API call
    ↓
processBranches() - Extract tags and branches
    ↓
createModal(panelName) - Build UI
    ↓
renderTimeline() - Draw timeline
    ↓
User interacts with timeline
    ↓
Click node → showVersionDetails()
    ↓
User chooses action:
    - Restore → restoreVersion() → API call → Refresh
    - View Changes → viewVersionDiff() → Open diff viewer
```

## UI/UX Design

### Modal Structure

```
┌─────────────────────────────────────────────┐
│ ◄ Version Timeline                       ✕ │
│   Panel Name                                │
├─────────────────────────────────────────────┤
│ [Zoom In] [Zoom Out] [Reset]    5 versions │
├─────────────────────────────────────────────┤
│                                             │
│   ●─────●─────●─────★─────●                │
│   v1    v2    v3    v4    v5               │
│  3mo   2mo   1mo  Today  (current)         │
│                                             │
├─────────────────────────────────────────────┤
│ ● Version  🏷️ Tagged  🛡️ Protected  ⭐ Current │
└─────────────────────────────────────────────┘
```

### Color Scheme

- **Primary (Blue)**: Regular versions, UI elements
  - `#3b82f6` - Main blue
  - `#2563eb` - Darker blue
  
- **Success (Green)**: Protected versions
  - `#10b981` - Main green
  - `#059669` - Darker green
  
- **Current (Purple)**: Active version
  - `#a855f7` - Main purple
  - `#7c3aed` - Darker purple
  
- **Tags (Yellow)**: Version tags
  - `#f59e0b` - Amber/yellow
  
- **Neutral (Gray)**: Text, borders, backgrounds
  - `#6b7280` - Medium gray
  - `#e5e7eb` - Light gray

### Responsive Breakpoints

```css
/* Desktop: Default styles */
.node-circle { width: 24px; height: 24px; }

/* Tablet: 768px and below */
@media (max-width: 768px) {
    .node-circle { width: 20px; height: 20px; }
    .version-label { font-size: 10px; }
}

/* Mobile: 640px and below */
@media (max-width: 640px) {
    .timeline-wrapper { padding: 20px 10px; }
}
```

## Branch Visualization

### Branch Detection

The system detects branches through:

1. **Metadata Inspection**:
   - Checks `version.metadata.branch` field
   - Automatically assigns to "main" if not specified

2. **Visual Representation**:
   - Different colors for different branches
   - Consistent color per branch throughout timeline

3. **Branch Information**:
   ```javascript
   {
       name: 'main',
       color: '#3b82f6',
       versions: [1, 2, 3, 4, 5]
   }
   ```

### Future Enhancements

- **Y-axis Branch Separation**: Display branches on separate horizontal tracks
- **Merge Points**: Visual indicators where branches merge
- **Branch Labels**: Named labels for each branch track
- **Branch Filtering**: Show/hide specific branches

## Performance Considerations

### Optimization Strategies

1. **Lazy Loading**:
   - Version data loaded only when timeline opened
   - Details fetched on-demand when node clicked

2. **DOM Efficiency**:
   - Timeline rendered once, not repeatedly
   - Minimal DOM manipulation
   - CSS transforms for smooth animations

3. **Data Caching**:
   - Version data cached in viewer instance
   - Reduces API calls on zoom/pan operations

4. **Responsive Rendering**:
   - Adaptive detail level based on zoom
   - Simplified view at far zoom out

### Scalability

**Current Implementation**:
- Optimized for 1-50 versions
- Smooth performance up to 100 versions
- May require pagination for 100+ versions

**Future Improvements**:
- Virtual scrolling for large timelines
- Progressive disclosure of details
- Server-side filtering options

## Error Handling

### User-Facing Errors

1. **Network Errors**:
   ```
   "Failed to load version data. Please check your connection and try again."
   ```

2. **Permission Errors**:
   ```
   "You don't have permission to view this panel's version history."
   ```

3. **Data Errors**:
   ```
   "Version data is incomplete. Please contact support."
   ```

### Developer Errors

Logged to console:
```javascript
console.error('Error loading version data:', error);
console.error('Error restoring version:', error);
console.error('Error showing version timeline:', error);
```

## Testing Checklist

### Functional Testing

- [ ] Timeline opens when clicking "History" button
- [ ] All versions displayed correctly
- [ ] Version nodes clickable
- [ ] Hover info cards appear/disappear
- [ ] Zoom controls work (in, out, reset)
- [ ] Modal closes (X button, backdrop, Escape key)
- [ ] Version details modal shows correct information
- [ ] Restore version creates new version
- [ ] Diff viewer integration works
- [ ] Tags displayed correctly
- [ ] Protection status shown correctly
- [ ] Current version highlighted

### Visual Testing

- [ ] Timeline responsive on desktop
- [ ] Timeline responsive on tablet
- [ ] Timeline responsive on mobile
- [ ] Colors consistent with design system
- [ ] Icons display correctly
- [ ] Hover effects smooth
- [ ] Zoom transitions smooth
- [ ] Text readable at all zoom levels

### Edge Cases

- [ ] Panel with single version
- [ ] Panel with 50+ versions
- [ ] Panel with no tags
- [ ] Panel with multiple tags per version
- [ ] Panel with all protected versions
- [ ] Panel with long version comments
- [ ] Panel with special characters in name

### Performance Testing

- [ ] Timeline loads in < 2 seconds
- [ ] Smooth scrolling with 20+ versions
- [ ] Zoom operations < 200ms
- [ ] Modal open/close animations smooth
- [ ] No memory leaks on repeated open/close

## Accessibility

### Keyboard Navigation

- **Escape**: Close timeline modal
- **Tab**: Navigate through interactive elements
- **Enter**: Activate buttons

### Screen Reader Support

- Modal properly announced
- Version information readable
- Button purposes clear
- Status indicators announced

### Color Contrast

All text meets WCAG AA standards:
- Normal text: 4.5:1 minimum
- Large text: 3:1 minimum
- Interactive elements: Clear focus indicators

## Future Enhancements

### Phase 2 Features

1. **Advanced Branch Visualization**:
   - Vertical separation of branches
   - Merge point indicators
   - Branch creation/deletion tracking

2. **Timeline Filtering**:
   - Filter by date range
   - Filter by creator
   - Filter by tags
   - Show only protected versions

3. **Timeline Export**:
   - Export timeline as image (PNG/SVG)
   - Export version history as PDF
   - Export change log as CSV

4. **Collaboration Features**:
   - Version annotations
   - Discussion threads per version
   - @mention notifications

5. **Analytics**:
   - Version access heatmap
   - Contribution statistics
   - Change frequency graph
   - Popular version indicators

6. **Batch Operations**:
   - Compare multiple versions
   - Bulk protect/unprotect
   - Batch tag management

### Phase 3 Features

1. **AI-Powered Insights**:
   - Suggest optimal versions to protect
   - Detect unusual change patterns
   - Recommend cleanup of old versions

2. **Real-Time Updates**:
   - Live timeline updates via WebSocket
   - Real-time collaboration indicators
   - Instant version creation notifications

3. **Advanced Visualization**:
   - 3D timeline view
   - Network graph of version relationships
   - Interactive change heatmap

## Support and Troubleshooting

### Common Issues

**Q: Timeline doesn't open**
- Check console for errors
- Verify `version-timeline-viewer.js` loaded
- Ensure panel has versions

**Q: Versions not displaying**
- Check API response format
- Verify user permissions
- Check browser compatibility

**Q: Restore fails**
- Verify user has edit permissions
- Check panel not locked
- Ensure storage quota not exceeded

### Browser Compatibility

**Tested and Supported**:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

**Features Requiring Modern Browser**:
- CSS Grid
- Flexbox
- CSS Transforms
- Fetch API
- ES6 JavaScript

## Documentation Links

- [Version Control System](./VERSION_CONTROL_SYSTEM.md)
- [Panel Library](./MY_PANELS_PROFILE_TAB.md)
- [API Documentation](./PANEL_API_USAGE.md)
- [Audit Trail](./AUDIT_TRAIL_SYSTEM.md)

## Changelog

### Version 1.0.0 (2024-01-22)
- Initial implementation
- Horizontal timeline layout
- Version details modal
- Restore version functionality
- Zoom controls
- Tag display
- Protection status indicators
- Current version highlighting
- Responsive design
- Keyboard navigation support

---

**Last Updated**: January 22, 2024  
**Status**: ✅ Implemented  
**Maintainer**: Development Team
