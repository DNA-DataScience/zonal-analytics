# Quick Test Guide - Batch Processing Feature

## How to Test

### Step 1: Open the Browser
1. Start the Next.js development server (if not already running)
2. Open `http://localhost:3000` in your browser
3. Open browser Developer Tools: **F12** or **Right-click → Inspect → Console tab**

### Step 2: Find the Batch Processing Tab
- Look at the **right side of the map** (middle-right position)
- You should see a button labeled **"📦 Batch"**
- Click it to open the Batch Processing panel

### Step 3: Test Table Mode (Default)

**Add coordinates:**
1. Panel opens in Table mode by default
2. Click **"+ Add Row"** button
3. Enter Latitude: `20.43`
4. Enter Longitude: `76.12`
5. Click **"+ Add Row"** again
6. Enter Latitude: `19.07`
7. Enter Longitude: `72.87`
8. Click **"Generate"** button
9. **Check the console** (F12) - you should see:
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

### Step 4: Test Paste Mode

1. Click the **"Paste"** button in the panel header
2. Click in the textarea
3. **Paste this text:**
```
28.5355,77.3910;28.4595,77.1362;28.7041,77.1025
```
4. You should see "Detected: 3 coordinates" appear
5. Click **"Generate"** button
6. **Check the console** - you should see the 3 coordinates logged with IDs 1, 2, 3

### Step 5: Test Validation

**In Table Mode:**
1. Click **"Table"** mode
2. Click **"+ Add Row"**
3. Enter Latitude: `95` (invalid - out of range)
   - The input field should turn **red**
4. Delete and try: `abc` (text instead of number)
   - Should turn **red**
5. Valid range is -90 to 90 for latitude, -180 to 180 for longitude

**In Paste Mode:**
1. Click **"Paste"** mode
2. Paste invalid data: `91,180;20,abc;30,200`
3. You should see **error messages** below the textarea:
   - "Line 1: Latitude out of range (-90 to 90)"
   - "Line 2: Invalid numbers"
   - "Line 3: Longitude out of range (-180 to 180)"

### Step 6: Test Clear Button

1. Add coordinates in either mode
2. Click **"Clear"** button
3. All data should be cleared
4. Counter resets to 0

### Step 7: Test Error Prevention

1. Try to add a row, but **don't fill in the coordinates**
2. Click **"Generate"**
3. Should see error message: "Please fix all coordinate errors before generating"

### Step 8: Test Up to 100 Coordinates

1. In Table mode, keep clicking **"+ Add Row"** 
2. After adding 100 rows, the **"+ Add Row"** button will warn you if you try to exceed the limit
3. Counter displays current count vs. 100

## Expected JSON Format

The console should always display coordinates in this exact format:

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

**Note:** IDs are auto-incremented starting from 1, regardless of which mode is used.

## Browser Console Tips

- **To view console:** F12 or Ctrl+Shift+I (Windows) / Cmd+Option+I (Mac)
- **Look for messages starting with:** "Batch Processing Coordinates:"
- **Copy the output:** Right-click on the log → Copy object
- **Expand the array:** Click the arrow (▶) next to the array to see all coordinates

## What's Not Yet Implemented

- Backend API call to `/batch-generator`
- CSV file download
- Processing status indicator
- Success/error messages for backend

These will be added in the next phase of implementation.

