# Report UI Visual Reference

## Color Palette

### Feasibility Status Colors
```
Red (Not Feasible):     #dc2626 on #fee background
Yellow (NOC Required):  #d97706 on #fef3c7 background
Green (Feasible):       #16a34a on #dcfce7 background
Gray (Unknown):         #64748b on #f1f5f9 background
```

### Zone Type Colors
```
Airport Zones:  Blue left border (#4338ca)
MoD Zones:      Red left border (#dc2626)
```

### Contributing Restrictions Dots
```
Airport: Red dot (#ef4444)
MoD:     Orange dot (#f59e0b)
Other:   Gray dot (#94a3b8)
```

## Layout Structure

```
┌─────────────────────────────────────────────────┐
│  FEASIBILITY REPORT                         [×] │
├─────────────────────────────────────────────────┤
│  Lat: 28.12345                                  │
│  Lng: 77.12345                                  │
│  Elev: 250 m                                    │
│                                                 │
│  ┌───────────────────────────────────────────┐ │
│  │ COMBINED ANALYSIS                [BADGE]  │ │
│  ├───────────────────────────────────────────┤ │
│  │ Comprehensive note explaining the         │ │
│  │ feasibility ruling...                     │ │
│  │                                           │ │
│  │ Contributing Restrictions:                │ │
│  │  ● airport: inner - Delhi Airport         │ │
│  │  ● mod: NO_WTG - Defense Area 123        │ │
│  │                                           │ │
│  │ [1 Airport Zone] [1 MoD Zone]            │ │
│  │                                           │ │
│  │ Maximum Allowed Height: Restricted        │ │
│  └───────────────────────────────────────────┘ │
│                                                 │
│  ┌───────────────────────────────────────────┐ │
│  │ ▶ AIRPORT ZONES                      [1]  │ │
│  └───────────────────────────────────────────┘ │
│    ┌─────────────────────────────────────────┐│
│    │ Delhi Airport          [Nearest Airport]││
│  ┃ ├─────────────────────────────────────────┤│
│  ┃ │ Feasibility:    [NOT FEASIBLE]          ││
│  ┃ │ Zone Type:      Inner Zone              ││
│  ┃ │ Airport Type:   Civil                   ││
│  ┃ │ Radio:          IFR                     ││
│  ┃ │ Elevation:      237m                    ││
│  ┃ │ Distance:       3500m                   ││
│  ┃ │ Min Height:     Restricted              ││
│  ┃ │ [Auto-Settle: Yes]                      ││
│  ┃ │ Note: No WTGs allowed in inner zone.    ││
│  ┃ │ CCZM Map: [View CCZM Map]              ││
│    └─────────────────────────────────────────┘│
│                                                 │
│  ┌───────────────────────────────────────────┐ │
│  │ ▼ MoD ZONES                          [1]  │ │
│  └───────────────────────────────────────────┘ │
│    ┌─────────────────────────────────────────┐│
│    │ Defense Area 123                        ││
│  ┃ ├─────────────────────────────────────────┤│
│  ┃ │ Feasibility:          [NOT FEASIBLE]    ││
│  ┃ │ Zone Classification:  No WTG Allowed    ││
│  ┃ │ Type:                 Restricted Zone   ││
│  ┃ │ Min Height:           Restricted        ││
│  ┃ │ Note: No WTGs allowed in MoD zone...    ││
│    └─────────────────────────────────────────┘│
└─────────────────────────────────────────────────┘

Legend:
┃ = Blue/Red left border for card type
▶ = Collapsed section (click to expand)
▼ = Expanded section (click to collapse)
[×] = Close button
[BADGE] = Color-coded feasibility badge
```

## Badge Examples

### Not Feasible (Red)
```
┌──────────────────┐
│  NOT FEASIBLE    │  #dc2626 text on #fee background
└──────────────────┘
```

### NOC Required (Yellow/Orange)
```
┌──────────────────┐
│  NOC REQUIRED    │  #d97706 text on #fef3c7 background
└──────────────────┘
```

### Feasible (Green)
```
┌──────────────────┐
│    FEASIBLE      │  #16a34a text on #dcfce7 background
└──────────────────┘
```

### Unknown (Gray)
```
┌──────────────────┐
│    UNKNOWN       │  #64748b text on #f1f5f9 background
└──────────────────┘
```

## Count Badges

### Airport Zones
```
┌────────────────┐
│ 1 Airport Zone │  #4338ca text on #e0e7ff background
└────────────────┘
```

### MoD Zones
```
┌────────────────┐
│  1 MoD Zone    │  #dc2626 text on #fee2e2 background
└────────────────┘
```

## Empty States

### No Zones Found
```
┌─────────────────────────────────────────┐
│ ✓ No airport zones found at this       │  Green success message
│   location                              │  #16a34a text on #f0fdf4 background
└─────────────────────────────────────────┘
```

### No Data Available
```
┌─────────────────────────────────────────┐
│ No data available for this location.   │  Gray informational message
│ Unable to determine feasibility.        │
└─────────────────────────────────────────┘
```

## Interactive Elements

### Section Header (Clickable)
```
Closed:
┌─────────────────────────────────────────┐
│ ▶ AIRPORT ZONES                    [3]  │  Hover: lighter background
└─────────────────────────────────────────┘

Open:
┌─────────────────────────────────────────┐
│ ▼ AIRPORT ZONES                    [3]  │  Arrow rotates 90°
└─────────────────────────────────────────┘
   [Zone cards displayed below]
```

### CCZM Button
```
┌──────────────────────┐
│ 📄 View CCZM Map     │  Blue button (#007bff)
└──────────────────────┘  Hover: darker blue (#0056b3)
```

## Responsive Behavior

### Panel Scrolling
- Max height: 60vh (60% of viewport height)
- Internal scrolling when content exceeds height
- Smooth scroll with overscroll-behavior: contain

### Section Expansion Rules
- **1-3 zones**: Section expanded by default
- **4+ zones**: Section collapsed by default
- User can toggle at any time

## Typography Scale

```
Panel Header:        18px, bold
Section Titles:      16px, semi-bold
Subsection Titles:   14px, semi-bold
Card Titles:         14px, semi-bold
Field Labels:        12px, bold
Field Values:        12px, regular
Badges (large):      12px, uppercase, bold
Badges (small):      11px, uppercase, bold
Notes:               12px, regular, line-height: 1.5
```

## Spacing System

```
Gap between sections:     16px
Section padding:          14px
Card padding:             12px
Field gap:                8px
Badge padding:            4px 10px (vertical horizontal)
Border radius (large):    8px
Border radius (medium):   6px
Border radius (small):    4px
```

## Animation Timing

```
Details arrow rotation:   0.2s ease
Button background:        0.15s ease
Section hover:            0.15s ease
Card hover shadow:        0.2s ease
```

## Accessibility Features

- Semantic HTML (details/summary for collapsible sections)
- ARIA labels on interactive elements
- Focus styles on buttons and links
- High contrast color choices
- Keyboard navigation support
- Screen reader friendly structure

## Print Styles (Future Enhancement)

```css
@media print {
  .report-panel__close { display: none; }
  .zone-details { display: block !important; }
  .zone-details summary::before { display: none; }
  .badge { border: 2px solid currentColor; }
}
```

