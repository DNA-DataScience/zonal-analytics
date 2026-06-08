# Batch Processing UI Walkthrough

## Visual Layout

### Map View with Batch Tab

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│                                                  ┌─────────────┐
│                                                  │ 📦 Batch    │
│                    MAP CONTENT                   │             │
│                                                  │ (Click to   │
│                                                  │  open)      │
│                                                  └─────────────┘
│                                                  
│                                                     
│                                                     
└─────────────────────────────────────────────────────┘
```

---

## Panel States

### Panel Closed (Default)
```
Only "📦 Batch" button visible on right side
```

### Panel Opened - Table Mode
```
┌─────────────────────────────────────┐
│ Batch Processing            [Close] │
├─ [Table]  [Paste] ──────────────────┤
│                                      │
│ 2/100 coordinates                   │
│                                      │
│ ┌──┬──────────┬───────────┬────────┐ │
│ │ID│Latitude  │ Longitude │Actions │ │
│ ├──┼──────────┼───────────┼────────┤ │
│ │1 │20.43     │ 76.12     │  [−]   │ │
│ ├──┼──────────┼───────────┼────────┤ │
│ │2 │19.07     │ 72.87     │  [−]   │ │
│ └──┴──────────┴───────────┴────────┘ │
│                                      │
│ [+ Add Row]                          │
│                                      │
├──────────────────────────────────────┤
│ [Clear]             [Generate]       │
└──────────────────────────────────────┘
```

### Panel Opened - Paste Mode
```
┌─────────────────────────────────────┐
│ Batch Processing            [Close] │
├─ [Table]  [Paste] ──────────────────┤
│                                      │
│ Format: lat,lon;lat,lon;lat,lon     │
│ Example: 20.43,76.12;19.07,72.87    │
│                                      │
│ ┌──────────────────────────────────┐ │
│ │ 20.43,76.12;19.07,72.87;         │ │
│ │ 18.52,73.86                      │ │
│ │                                  │ │
│ └──────────────────────────────────┘ │
│                                      │
│ Detected: 3 coordinates             │
│                                      │
├──────────────────────────────────────┤
│ [Clear]             [Generate]       │
└──────────────────────────────────────┘
```

### Panel with Validation Errors - Table Mode
```
┌─────────────────────────────────────┐
│ Batch Processing            [Close] │
├─ [Table]  [Paste] ──────────────────┤
│                                      │
│ 2/100 coordinates                   │
│                                      │
│ ┌──┬──────────┬───────────┬────────┐ │
│ │ID│Latitude  │ Longitude │Actions │ │
│ ├──┼──���───────┼───────────┼────────┤ │
│ │1 │█95███    │ 76.12     │  [−]   │ │ ← Red error border
│ ├──┼──────────┼───────────┼────────┤ │
│ │2 │19.07     │ 72.87     │  [−]   │ │
│ └──┴──────────┴───────────┴────────┘ │
│                                      │
│ [+ Add Row]                          │
│                                      │
├──────────────────────────────────────┤
│ [Clear]             [Generate]       │
└──────────────────────────────────────┘
```

### Panel with Validation Errors - Paste Mode
```
┌─────────────────────────────────────┐
│ Batch Processing            [Close] │
├─ [Table]  [Paste] ──────────────────┤
│                                      │
│ Format: lat,lon;lat,lon;lat,lon     │
│ Example: 20.43,76.12;19.07,72.87    │
│                                      │
│ ┌──────────────────────────────────┐ │
│ │ 91,180;20,abc;30,200             │ │
│ │                                  │ │ ← Red error border
│ └──────────────────────────────────┘ │
│                                      │
│ ✗ Line 1: Latitude out of range     │
│ ✗ Line 2: Invalid numbers           │
│ ✗ Line 3: Longitude out of range    │
│                                      │
│ Detected: 0 coordinates             │
│                                      │
├──────────────────────────────────────┤
│ [Clear]             [Generate]       │
└──────────────────────────────────────┘
```

---

## Step-by-Step User Flow

### Scenario 1: Add Coordinates in Table Mode

**Step 1: Open Panel**
```
User clicks "📦 Batch" button on map
→ Panel opens with Table mode active
```

**Step 2: Add First Coordinate**
```
User clicks "+ Add Row"
→ New table row appears with ID=1
User enters: Lat=20.43, Lon=76.12
→ Counter shows: 1/100
```

**Step 3: Add Second Coordinate**
```
User clicks "+ Add Row" again
→ New table row appears with ID=2
User enters: Lat=19.07, Lon=72.87
→ Counter shows: 2/100
```

**Step 4: Generate Report**
```
User clicks "Generate"
→ Coordinates validated (no red borders)
→ Data logged to browser console:
   [
     {"id": 1, "lat": 20.43, "lon": 76.12},
     {"id": 2, "lat": 19.07, "lon": 72.87}
   ]
```

---

### Scenario 2: Bulk Paste Coordinates

**Step 1: Open Panel and Switch to Paste Mode**
```
User clicks "📦 Batch" button
→ Panel opens with Table mode
User clicks "Paste" tab
→ Panel switches to Paste mode
```

**Step 2: Paste Coordinates**
```
User copies text: 20.43,76.12;19.07,72.87;18.52,73.86
User pastes in textarea
→ Real-time validation occurs
→ Counter updates: "Detected: 3 coordinates"
→ No error messages shown (all valid)
```

**Step 3: Generate Report**
```
User clicks "Generate"
→ Data logged to browser console:
   [
     {"id": 1, "lat": 20.43, "lon": 76.12},
     {"id": 2, "lat": 19.07, "lon": 72.87},
     {"id": 3, "lat": 18.52, "lon": 73.86}
   ]
```

---

### Scenario 3: Handle Validation Error

**Step 1: Enter Invalid Data**
```
User adds row and enters: Lat=95 (invalid)
→ Input field turns red
→ Error class applied to DOM
```

**Step 2: Attempt Generate**
```
User clicks "Generate"
→ Code detects error state
→ Alert shown: "Please fix all coordinate errors before generating"
→ No console output
```

**Step 3: Fix and Retry**
```
User corrects Lat to 20.43
→ Red border removed
→ Input field returns to normal
User clicks "Generate"
→ Success: data logged to console
```

---

### Scenario 4: Clear and Start Over

**Step 1: Enter Multiple Coordinates**
```
User adds 5 rows with coordinates
Counter shows: 5/100
```

**Step 2: Clear All**
```
User clicks "Clear" button
→ All rows removed
→ Textarea emptied (if in Paste mode)
→ Counter resets to 0
→ Error messages cleared
```

**Step 3: Start Fresh**
```
Panel ready for new data input
User can add new coordinates
```

---

## Input Field States

### Valid Input
```
┌─────────────┐
│ 20.43       │  ← Normal border (gray)
└─────────────┘  ← White background
```

### Invalid Input
```
┌─────────────┐
│ 95          │  ← Red border
└─────────────┘  ← Light red background
```

### Empty Input (Before Validation)
```
┌─────────────┐
│             │  ← Normal border (gray)
└─────────────┘  ← White background
```

### Empty Input (With Error)
```
┌─────────────┐
│             │  ← Red border
└─────────────┘  ← Light red background
```

---

## Error Messages

### Table Mode Error Messages
- **Display Location:** Directly on input field (red border)
- **Type:** Visual only (no text message)
- **Cleared:** When user corrects value

### Paste Mode Error Messages
- **Display Location:** Below textarea in red box
- **Format:** Line-by-line error list
- **Examples:**
  ```
  ✗ Line 1: Latitude out of range (-90 to 90)
  ✗ Line 2: Invalid numbers
  ✗ Line 3: Expected format "lat,lon"
  ```
- **Cleared:** When all coordinates valid

### Alert Messages
- **Display Location:** Browser alert dialog
- **Trigger:** User tries to Generate with errors
- **Message:** "Please fix all coordinate errors before generating"

---

## Button States

### Normal State
```
[+ Add Row]  ← Available for click
[Clear]      ← Available for click
[Generate]   ← Available for click
```

### Max Coordinates Reached (100)
```
[+ Add Row]  ← Disabled (can't add more)
[Clear]      ← Still available
[Generate]   ← Still available
```

### Processing (After Click Generate)
```
[Generate]   ← Would be disabled during API call (future)
```

---

## Mode Toggle Behavior

### Switching Modes
```
Table Mode Active:
[TABLE] ← Black background (active)
[Paste] ← Light background (inactive)

User clicks [Paste]:
[Table] ← Light background (inactive)
[PASTE] ← Black background (active)
```

### Data Persistence
- **Table → Paste:** Data not transferred (new mode shows empty)
- **Paste → Table:** Data not transferred (new mode shows empty)
- **Switching Back:** Previous data lost

---

## Console Output

### Browser Console Location
```
F12 or Right-click → Inspect → Console tab
```

### Console Message Format
```
Batch Processing Coordinates: [
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

### How to Copy Console Output
1. Click on the array in console
2. Right-click → "Copy object"
3. Paste in text editor or API testing tool

---

## Keyboard Navigation

- **Tab Key:** Navigate between inputs
- **Enter Key:** Doesn't submit form (form submission disabled)
- **Escape Key:** Doesn't close panel (not implemented yet)
- **Arrow Keys:** Work in number inputs (increment/decrement)

---

## Responsive Behavior

### Desktop (Wide Screen)
```
Full panel visible
All content readable
Proper spacing maintained
```

### Tablet (Medium Screen)
```
Panel may be wider or narrower
Scrolling may be needed for long lists
Touch-friendly button sizes
```

### Mobile (Narrow Screen)
```
Panel may cover significant map area
Scrolling required for table with many rows
Touch-optimized controls
```

---

## Color Scheme

| Element | Color | Usage |
|---------|-------|-------|
| Background | White (#ffffff) | Panel and inputs |
| Header | Light Gray (#f8fafc) | Section dividers |
| Border | Light Border (#e2e8f0) | Normal state |
| Text | Dark (#0f172a) | Main text |
| Secondary | Medium Gray (#64748b) | Helper text |
| Error Border | Red (#dc2626) | Validation failure |
| Error Background | Light Red (#fee) | Error highlight |
| Active Button | Black (#0f172a) | Mode toggle active |
| Hover | Lighter Gray (#e2e8f0) | Button hover state |

---

## Accessibility Features

- **ARIA Labels:** All buttons have aria-label attributes
- **Semantic HTML:** Proper heading hierarchy
- **Keyboard Navigation:** All controls accessible via Tab key
- **Color + Text:** Errors not indicated by color alone
- **Error Messages:** Specific and helpful descriptions
- **Focus Indicators:** Clear focus states on inputs

---

## Animation Effects

- **Transitions:** 0.15s ease on all interactive elements
- **Hover Effects:** Subtle background/border color changes
- **Panel Open/Close:** Instant (no fade animation)
- **Button Press:** No animation (instant response)

---

## Performance Notes

- **Real-time Validation:** Runs on every keystroke (no debounce needed)
- **DOM Rendering:** Minimal reflows for validation updates
- **Memory:** Only stores valid coordinates (invalid ones discarded)
- **Max Size:** 100 coordinates × ~50 bytes = ~5KB JSON


