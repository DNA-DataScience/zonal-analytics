# Batch Processing Implementation Architecture

## File Structure

```
src/app/components/
├── BatchProcessingControl.tsx (NEW - 738 lines)
└── Map.tsx (MODIFIED - added import and initialization)
```

## Component Overview

### BatchProcessingControl.tsx

A MapLibre control that implements the `IControl` interface for seamless integration with the map.

#### Key Classes/Interfaces

```typescript
interface Coordinate {
  id: number;
  lat: number;
  lon: number;
}

export class BatchProcessingControl implements maplibregl.IControl {
  // Control properties
  private _container: HTMLDivElement;      // Main container
  private _panel: HTMLDivElement;          // Collapsible panel
  private _map: maplibregl.Map;            // Map reference
  private _styleEl: HTMLStyleElement;      // CSS styles
  
  // State management
  private _isOpen: boolean;                // Panel open/closed
  private _mode: "table" | "paste";        // Input mode
  private _coordinates: Coordinate[];      // Collected coordinates
  private _nextId: number;                 // Auto-increment counter
}
```

#### MapLibre IControl Interface Implementation

```typescript
onAdd(map: maplibregl.Map): HTMLElement {
  // Called when control is added to map
  // Creates DOM elements and attaches event listeners
}

onRemove(): void {
  // Called when control is removed from map
  // Cleans up DOM and event listeners
}
```

## State Management

### Data Flow

```
User Input (Table/Paste)
        ↓
Input Validation
        ↓
Store in _coordinates array
        ↓
Auto-increment IDs (1, 2, 3, ...)
        ↓
Generate Report
        ↓
Log to Console as JSON
```

### Mode-Specific Processing

#### Table Mode
```
DOM Form Inputs
  ↓
Parse each row (lat, lon)
  ↓
Extract ID from table cell
  ↓
Validate per input field
  ↓
Collect into Coordinate[]
```

#### Paste Mode
```
Text Input (lat,lon;lat,lon;)
  ↓
Split by semicolon
  ↓
Split each pair by comma
  ↓
Validate format & ranges
  ↓
Auto-assign IDs (1, 2, 3, ...)
  ↓
Collect into Coordinate[]
```

## Event Handling

### Tab Button
- **Event:** Click
- **Action:** Toggle panel open/closed

### Mode Toggle Buttons
- **Event:** Click
- **Action:** Switch between Table and Paste mode
- **Effect:** Hide/show respective input UI

### Table Inputs
- **Event:** Input (on lat/lon fields)
- **Action:** Real-time validation
- **Effect:** Add/remove "error" CSS class, update counter

### Remove Row Button
- **Event:** Click
- **Action:** Delete table row
- **Effect:** Update counter

### Add Row Button
- **Event:** Click
- **Action:** Add new row to table
- **Limit:** Max 100 rows

### Paste Textarea
- **Event:** Input
- **Action:** Real-time parsing and validation
- **Effect:** Update error messages and counter

### Clear Button
- **Event:** Click
- **Action:** Clear all inputs and reset state
- **Effect:** Reset counter, clear coordinates array

### Generate Button
- **Event:** Click
- **Action:** Collect coordinates, validate, log to console
- **Effect:** Console logs JSON in required format

## Validation Logic

### Latitude Validation
```typescript
isValid = value >= -90 && value <= 90 && isNumber(value)
```

### Longitude Validation
```typescript
isValid = value >= -180 && value <= 180 && isNumber(value)
```

### Required Fields
- Both latitude and longitude must be filled
- Empty fields marked as error

### Error Feedback

**Table Mode:**
- Invalid inputs highlighted with red border
- Error applies to specific input field
- User can fix individual coordinates

**Paste Mode:**
- Entire textarea highlighted with red border if any errors
- Error messages displayed below textarea
- Shows line number and specific error description
- Examples:
  - "Line 1: Latitude out of range (-90 to 90)"
  - "Line 2: Invalid numbers"
  - "Line 3: Expected format 'lat,lon'"

## ID Generation

### Table Mode
- IDs displayed in first column
- Auto-incrementing: 1, 2, 3, ...
- Assigned at creation time
- Preserved even if rows reordered

### Paste Mode
- IDs assigned sequentially: `results.valid.length + 1`
- Applied only to valid coordinates
- Restarts from 1 for each parsing operation

### ID Counter
```typescript
private _nextId: number = 1;

// Incremented when adding table row
const id = this._nextId++;
```

## UI/UX Components

### Tab Button
```
Position: Middle-right of map
Icon: 📦 
Label: "Batch"
Behavior: Toggle panel on click
```

### Panel Layout
```
┌─ Header ─────────────────────┐
│ "Batch Processing"    [Close] │
├─ Mode Toggle ────────────────┤
│ [Table]   [Paste]             │
├─ Content Area ───────────────┤
│ (Table Mode)                  │
│ Counter: 0/100                │
│ ID | Lat | Lon | Actions     │
│ [+ Add Row]                   │
│                               │
│ (Paste Mode - hidden)         │
│ Format hint                   │
│ [Textarea]                    │
│ Counter: 0 coordinates        │
├─ Footer ─────────────────────┤
│ [Clear]        [Generate]     │
└───────────────────────────────┘
```

### CSS Classes
- `.batch-processing-tab` - Main container
- `.batch-processing-tab-button` - Tab button
- `.batch-processing-panel` - Expandable panel
- `.batch-processing-table` - Data table
- `.batch-processing-paste-area` - Textarea input
- `.error` - Applied to invalid inputs
- `.active` - Applied to active mode button

## Integration Points

### Map.tsx
```typescript
import { BatchProcessingControl } from "@/app/components/BatchProcessingControl";

map.on("load", () => {
  // ... other controls ...
  map.addControl(new BatchProcessingControl(), "top-right");
});
```

### Position on Map
- **Position:** "top-right" 
- **Actual Placement:** Middle-right (via CSS absolute positioning)
- **Z-index:** 101 (panel) / 100 (container)
- **Stacking:** Above standard MapLibre controls

## Data Output Format

### Console Log
```javascript
console.log(
  "Batch Processing Coordinates:",
  JSON.stringify(coords, null, 2)
)
```

### Example Output
```json
[
  {
    "id": 1,
    "lat": 20.43,
    "lon": 76.12
  },
  {
    "id": 2,
    "lat": 19.07,
    "lon": 72.87
  }
]
```

## Future Enhancement Points

### TODO Comments in Code
1. Backend API integration at `_generateReport()`
2. CSV download implementation
3. Loading state management
4. Error handling for API calls
5. Success notification display

### Planned Functions
```typescript
// To be added
private async _sendToBatchAPI(coords: Coordinate[]): Promise<void>
private _downloadCSV(response: Blob, filename: string): void
private _showLoadingState(isLoading: boolean): void
private _showNotification(message: string, type: 'success' | 'error'): void
```

## Performance Considerations

### Memory
- Only stores valid coordinates (invalid ones discarded)
- Max 100 coordinates per request
- Lightweight DOM structure

### Rendering
- Only visible when panel is open
- CSS transforms for positioning (better performance)
- Event delegation not used (direct listeners on elements)

### Validation
- Real-time validation on input
- Debounce not needed (input is synchronous)
- Error state cached in DOM (red border)

## Browser Compatibility

- Uses standard Web APIs (no polyfills needed)
- MapLibre GL JS 5.7.3+
- Modern CSS (flex, grid)
- ES6 TypeScript
- Works in all modern browsers (Chrome, Firefox, Safari, Edge)

## Accessibility

- Semantic HTML structure
- ARIA labels on buttons
- Keyboard navigable
- Color not sole indicator (uses borders + text)
- Clear error messages

## Code Quality

- **Type Safety:** Full TypeScript strict mode
- **Error Handling:** User-facing validation + console logs
- **Memory Leaks:** Proper cleanup in onRemove()
- **Naming:** Camelcase private members with underscore prefix
- **Documentation:** Inline comments for complex logic

