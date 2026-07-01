# Report UI Examples

This document shows example API responses and their expected UI rendering.

## Example 1: Restrictive Location (Both Airport and MoD)

### API Response
```json
[
  {
    "layer": "combined",
    "zone": "Combined Analysis",
    "feasibility": "No",
    "min_height": "Restricted",
    "note": "Not feasible due to: Airport inner zone at Delhi Airport and MoD NO_WTG zone (Defense Area 123).",
    "contributing_restrictions": [
      "airport: inner - Delhi Airport",
      "mod: NO_WTG - Defense Area 123"
    ],
    "total_airport_zones": 1,
    "total_mod_zones": 1
  },
  {
    "layer": "airport",
    "zone": "inner",
    "name": "Delhi Airport",
    "feasibility": "No",
    "note": "No WTGs allowed in inner zone.",
    "min_height": "Restricted",
    "distance": 3500.25,
    "airport_elevation": 237.0,
    "type": "Civil",
    "radio": "IFR",
    "cczm": "Delhi",
    "autoSettle": "N/A"
  },
  {
    "layer": "mod",
    "zone": "NO_WTG",
    "name": "Defense Area 123",
    "type": "Restricted Zone",
    "feasibility": "No",
    "note": "No WTGs allowed in MoD restricted zone.",
    "min_height": "Restricted"
  }
]
```

### Expected UI Output
```
╔═══════════════════════════════════════════════╗
║ FEASIBILITY ANALYSIS       [NOT FEASIBLE]     ║
╠═══════════════════════════════════════════════╣
║ Not feasible due to: Airport inner zone at   ║
║ Delhi Airport and MoD NO_WTG zone (Defense   ║
║ Area 123).                                    ║
║                                               ║
║ Contributing Restrictions:                    ║
║  ● airport: inner - Delhi Airport             ║
║  ● mod: NO_WTG - Defense Area 123            ║
║                                               ║
║ [1 Airport Zone] [1 MoD Zone]                ║
║ Maximum Allowed Height: Restricted            ║
╚═══════════════════════════════════════════════╝

╔═══════════════════════════════════════════════╗
║ ▼ AIRPORT ZONES                          [1]  ║
╠═══════════════════════════════════════════════╣
║ ┃ Delhi Airport                               ║
║ ┃ Feasibility: [NOT FEASIBLE]                 ║
║ ┃ Zone Type: Inner Zone                       ║
║ ┃ Airport Type: Civil                         ║
║ ┃ Radio: IFR                                  ║
║ ┃ Elevation: 237m                             ║
║ ┃ Distance: 3500m                             ║
║ ┃ Min Height: Restricted                      ║
║ ┃ Auto-Settle: N/A                            ║
║ ┃ Note: No WTGs allowed in inner zone.        ║
║ ┃ CCZM Map: [View CCZM Map]                  ║
╚═══════════════════════════════════════════════╝

╔═══════════════════════════════════════════════╗
║ ▼ MoD ZONES                              [1]  ║
╠═══════════════════════════════════════════════╣
║ ┃ Defense Area 123                            ║
║ ┃ Feasibility: [NOT FEASIBLE]                 ║
║ ┃ Zone Classification: No WTG Allowed         ║
║ ┃ Type: Restricted Zone                       ║
║ ┃ Min Height: Restricted                      ║
║ ┃ Note: No WTGs allowed in MoD restricted     ║
║ ┃       zone.                                 ║
╚═══════════════════════════════════════════════╝
```

---

## Example 2: NOC Required (Middle Zone)

### API Response
```json
[
  {
    "layer": "combined",
    "zone": "Combined Analysis",
    "feasibility": "NOC",
    "min_height": "125.3m",
    "note": "NOC required due to middle zone at Mumbai Airport. Height limited to 125.3m.",
    "contributing_restrictions": [
      "airport: middle - Mumbai Airport"
    ],
    "total_airport_zones": 1,
    "total_mod_zones": 0
  },
  {
    "layer": "airport",
    "zone": "middle",
    "name": "Mumbai Airport",
    "feasibility": "NOC",
    "note": "NOC required with height limit of 125.3m.",
    "min_height": "125.3m",
    "distance": 8500.0,
    "airport_elevation": 11.0,
    "type": "Civil",
    "radio": "IFR",
    "cczm": "Mumbai",
    "autoSettle": "No"
  }
]
```

### Expected UI Output
```
╔═══════════════════════════════════════════════╗
║ FEASIBILITY ANALYSIS       [NOC REQUIRED]     ║
╠═══════════════════════════════════════════════╣
║ NOC required due to middle zone at Mumbai    ║
║ Airport. Height limited to 125.3m.           ║
║                                               ║
║ Contributing Restrictions:                    ║
║  ● airport: middle - Mumbai Airport           ║
║                                               ║
║ [1 Airport Zone] [0 MoD Zones]               ║
║ Maximum Allowed Height: 125.3m               ║
╚═══════════════════════════════════════════════╝

╔═══════════════════════════════════════════════╗
║ ▼ AIRPORT ZONES                          [1]  ║
╠═══════════════════════════════════════════════╣
║ ┃ Mumbai Airport                              ║
║ ┃ Feasibility: [NOC REQUIRED]                 ║
║ ┃ Zone Type: Middle Zone                      ║
║ ┃ Airport Type: Civil                         ║
║ ┃ Radio: IFR                                  ║
║ ┃ Elevation: 11m                              ║
║ ┃ Distance: 8500m                             ║
║ ┃ Min Height: 125.3m                          ║
║ ┃ Auto-Settle: No                             ║
║ ┃ Note: NOC required with height limit of     ║
║ ┃       125.3m.                               ║
║ ┃ CCZM Map: [View CCZM Map]                  ║
╚═══════════════════════════════════════════════╝

╔═══════════════════════════════════════════════╗
║ MoD ZONES                                [0]  ║
╠═══════════════════════════════════════════════╣
║ ✓ No MoD zones found at this location        ║
╚═══════════════════════════════════════════════╝
```

---

## Example 3: Feasible Location (Outer Zone)

### API Response
```json
[
  {
    "layer": "combined",
    "zone": "Combined Analysis",
    "feasibility": "Yes",
    "min_height": "Not Required",
    "note": "Feasible. Located in outer zone of Bangalore Airport.",
    "contributing_restrictions": [],
    "total_airport_zones": 1,
    "total_mod_zones": 0
  },
  {
    "layer": "airport",
    "zone": "outer",
    "name": "Bangalore Airport",
    "feasibility": "Yes",
    "note": "Feasible in outer zone. NOC recommended but not mandatory.",
    "min_height": "Not Required",
    "distance": 15000.0,
    "airport_elevation": 906.0,
    "type": "Civil",
    "radio": "IFR",
    "cczm": "Bangalore",
    "autoSettle": "Yes"
  }
]
```

### Expected UI Output
```
╔═══════════════════════════════════════════════╗
║ FEASIBILITY ANALYSIS          [FEASIBLE]      ║
╠═══════════════════════════════════════════════╣
║ Feasible. Located in outer zone of           ║
║ Bangalore Airport.                            ║
║                                               ║
║ [1 Airport Zone] [0 MoD Zones]               ║
║ Maximum Allowed Height: Not Required         ║
╚═══════════════════════════════════════════════╝

╔═══════════════════════════════════════════════╗
║ ▼ AIRPORT ZONES                          [1]  ║
╠═══════════════════════════════════════════════╣
║ ┃ Bangalore Airport                           ║
║ ┃ Feasibility: [FEASIBLE]                     ║
║ ┃ Zone Type: Outer Zone                       ║
║ ┃ Airport Type: Civil                         ║
║ ┃ Radio: IFR                                  ║
║ ┃ Elevation: 906m                             ║
║ ┃ Distance: 15000m                            ║
║ ┃ Min Height: Not Required                    ║
║ ┃ [Auto-Settle: Yes] ← Green highlighted     ║
║ ┃ Note: Feasible in outer zone. NOC           ║
║ ┃       recommended but not mandatory.        ║
║ ┃ CCZM Map: [View CCZM Map]                  ║
╚═══════════════════════════════════════════════╝

╔═══════════════════════════════════════════════╗
║ MoD ZONES                                [0]  ║
╠═══════════════════════════════════════════════╣
║ ✓ No MoD zones found at this location        ║
╚═══════════════════════════════════════════════╝
```

---

## Example 4: Nearest Airport Only (No Zones)

### API Response
```json
[
  {
    "layer": "airport",
    "zone": "outer",
    "name": "Hyderabad Airport",
    "feasibility": "Yes",
    "note": "No zones intersecting. Nearest airport provided for reference.",
    "min_height": "Not Required",
    "distance": 45000.0,
    "airport_elevation": 545.0,
    "type": "Civil",
    "radio": "IFR",
    "cczm": "Hyderabad",
    "autoSettle": "Yes"
  }
]
```

### Expected UI Output
```
╔═══════════════════════════════════════════════╗
║ FEASIBILITY ANALYSIS          [FEASIBLE]      ║
╠═══════════════════════════════════════════════╣
║ Location is feasible based on nearest        ║
║ airport auto-settlement policy.               ║
║                                               ║
║ [1 Airport Zone] [0 MoD Zones]               ║
╚═══════════════════════════════════════════════╝

╔═══════════════════════════════════════════════╗
║ ▼ AIRPORT ZONES                          [1]  ║
╠═══════════════════════════════════════════════╣
║ ┃ Hyderabad Airport   [Nearest Airport]      ║
║ ┃ Feasibility: [FEASIBLE]                     ║
║ ┃ Zone Type: Outer Zone                       ║
║ ┃ Airport Type: Civil                         ║
║ ┃ Radio: IFR                                  ║
║ ┃ Elevation: 545m                             ║
║ ┃ Distance: 45000m                            ║
║ ┃ Min Height: Not Required                    ║
║ ┃ [Auto-Settle: Yes]                          ║
║ ┃ Note: No zones intersecting. Nearest        ║
║ ┃       airport provided for reference.       ║
║ ┃ CCZM Map: [View CCZM Map]                  ║
╚═══════════════════════════════════════════════╝
```

---

## Example 5: Multiple Zones (4+ Each)

### API Response
```json
[
  {
    "layer": "combined",
    "zone": "Combined Analysis",
    "feasibility": "No",
    "min_height": "Restricted",
    "note": "Not feasible due to multiple restrictions.",
    "contributing_restrictions": [
      "airport: inner - Airport A",
      "airport: middle - Airport B",
      "mod: NO_WTG - Zone 1",
      "mod: NOC - Zone 2"
    ],
    "total_airport_zones": 5,
    "total_mod_zones": 4
  },
  { "layer": "airport", /* ... Airport A ... */ },
  { "layer": "airport", /* ... Airport B ... */ },
  { "layer": "airport", /* ... Airport C ... */ },
  { "layer": "airport", /* ... Airport D ... */ },
  { "layer": "airport", /* ... Airport E ... */ },
  { "layer": "mod", /* ... MoD Zone 1 ... */ },
  { "layer": "mod", /* ... MoD Zone 2 ... */ },
  { "layer": "mod", /* ... MoD Zone 3 ... */ },
  { "layer": "mod", /* ... MoD Zone 4 ... */ }
]
```

### Expected UI Output
```
╔═══════════════════════════════════════════════╗
║ FEASIBILITY ANALYSIS       [NOT FEASIBLE]     ║
╠═══════════════════════════════════════════════╣
║ Not feasible due to multiple restrictions.   ║
║                                               ║
║ Contributing Restrictions:                    ║
║  ● airport: inner - Airport A                 ║
║  ● airport: middle - Airport B                ║
║  ● mod: NO_WTG - Zone 1                      ║
║  ● mod: NOC - Zone 2                         ║
║                                               ║
║ [5 Airport Zones] [4 MoD Zones]              ║
║ Maximum Allowed Height: Restricted            ║
╚═══════════════════════════════════════════════╝

╔═══════════════════════════════════════════════╗
║ ▶ AIRPORT ZONES                          [5]  ║ ← Collapsed
╚═══════════════════════════════════════════════╝

╔═══════════════════════════════════════════════╗
║ ▶ MoD ZONES                              [4]  ║ ← Collapsed
╚═══════════════════════════════════════════════╝

(Click to expand sections and see all zone details)
```

---

## Example 6: Empty Response

### API Response
```json
[]
```

### Expected UI Output
```
╔═══════════════════════════════════════════════╗
║ FEASIBILITY ANALYSIS          [UNKNOWN]       ║
╠═══════════════════════════════════════════════╣
║ No data available for this location. Unable  ║
║ to determine feasibility.                     ║
╚═══════════════════════════════════════════════╝
```

---

## Example 7: MoD Special Limited Height

### API Response
```json
[
  {
    "layer": "combined",
    "zone": "Combined Analysis",
    "feasibility": "NOC",
    "min_height": "83.5m AGL",
    "note": "NOC required. Height limited to 83.5m AGL due to MoD special zone.",
    "contributing_restrictions": [
      "mod: SPECIAL_LIMITED_HEIGHT - Coastal Area 456"
    ],
    "total_airport_zones": 0,
    "total_mod_zones": 1
  },
  {
    "layer": "mod",
    "zone": "SPECIAL_LIMITED_HEIGHT",
    "name": "Coastal Area 456",
    "type": "Special Coastal Zone",
    "feasibility": "NOC",
    "note": "Height limited to 83.5m AGL. NOC required.",
    "min_height": "83.5m AGL"
  }
]
```

### Expected UI Output
```
╔═══════════════════════════════════════════════╗
║ FEASIBILITY ANALYSIS       [NOC REQUIRED]     ║
╠═══════════════════════════════════════════════╣
║ NOC required. Height limited to 83.5m AGL    ║
║ due to MoD special zone.                      ║
║                                               ║
║ Contributing Restrictions:                    ║
║  ● mod: SPECIAL_LIMITED_HEIGHT - Coastal     ║
║         Area 456                              ║
║                                               ║
║ [0 Airport Zones] [1 MoD Zone]               ║
║ Maximum Allowed Height: 83.5m AGL            ║
╚═══════════════════════════════════════════════╝

╔═════════════════════════════════════════���═════╗
║ AIRPORT ZONES                            [0]  ║
╠═══════════════════════════════════════════════╣
║ ✓ No airport zones found at this location    ║
╚═══════════════════════════════════════════════╝

╔═══════════════════════════════════════════════╗
║ ▼ MoD ZONES                              [1]  ║
╠═══════════════════════════════════════════════╣
║ ┃ Coastal Area 456                            ║
║ ┃ Feasibility: [NOC REQUIRED]                 ║
║ ┃ Zone Classification: Special Limited Height ║
║ ┃ Type: Special Coastal Zone                  ║
║ ┃ Min Height: 83.5m AGL                       ║
║ ┃ Note: Height limited to 83.5m AGL. NOC      ║
║ ┃       required.                             ║
╚═══════════════════════════════════════════════╝
```

---

## Legend

```
[NOT FEASIBLE]   = Red badge (#dc2626 on #fee)
[NOC REQUIRED]   = Yellow badge (#d97706 on #fef3c7)
[FEASIBLE]       = Green badge (#16a34a on #dcfce7)
[UNKNOWN]        = Gray badge (#64748b on #f1f5f9)

┃ = Colored left border (blue for airport, red for MoD)
▶ = Collapsed section
▼ = Expanded section
● = Colored bullet (red for airport, orange for MoD)
✓ = Green checkmark for empty states
```

## Key UI Features Demonstrated

1. **Color-coded feasibility badges** - Instant visual feedback
2. **Contributing restrictions** - Clear list of limiting factors
3. **Zone count badges** - Quick overview of complexity
4. **Collapsible sections** - Better organization for multiple zones
5. **Empty states** - Friendly messages when zones are absent
6. **Nearest airport labeling** - Clear distinction from intersecting zones
7. **AutoSettle highlighting** - Important information stands out
8. **Consistent card layout** - Easy to scan and compare
9. **Typography hierarchy** - Important info is more prominent
10. **Responsive scrolling** - Handles any number of zones gracefully

