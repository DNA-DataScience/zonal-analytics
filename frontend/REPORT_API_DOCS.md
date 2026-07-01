# Report Generator API

## Endpoint

```
GET /report-generator?lat={latitude}&lng={longitude}&elev={elevation}
```

**Parameters:**

- `lat` (required): Latitude
- `lng` (required): Longitude
- `elev` (optional): Elevation in meters (default: 0)

## Response Structure

Returns JSON array with:

1. **Combined Analysis** (first item) - Overall feasibility ruling
2. **Airport Zones** - All intersecting airport zones
3. **MoD Zones** - All intersecting MoD zones

## Feasibility Values

- `"No"` - Not feasible (RED)
- `"NOC"` - NOC required (YELLOW)
- `"Yes"` - Feasible (GREEN)

## Combined Analysis Object

```json
{
  "layer": "combined",
  "zone": "Combined Analysis",
  "feasibility": "No|NOC|Yes",
  "min_height": "Restricted|Not Required|125.3m|83.5m AGL",
  "note": "Comprehensive explanation with specific zones",
  "contributing_restrictions": ["airport: inner - Delhi Airport"],
  "total_airport_zones": 1,
  "total_mod_zones": 1
}
```

**Key Fields:**

- `feasibility`: Final ruling for the location
- `note`: Human-readable explanation mentioning specific restrictive zones
- `contributing_restrictions`: Array of zones that influenced the decision
- `total_airport_zones` / `total_mod_zones`: Count of zones found

## Airport Zone Object

```json
{
  "layer": "airport",
  "zone": "funnel|inner|middle|outer",
  "name": "Airport name",
  "type": "Airport type",
  "radio": "VFR|IFR",
  "feasibility": "No|NOC|Yes",
  "min_height": "Restricted|125.3m|Not Required",
  "note": "Individual zone explanation",
  "distance": 1234.56,
  "airport_elevation": 245.5,
  "cczm": "City name",
  "autoSettle": "Yes|No|N/A"
}
```

## MoD Zone Object

```json
{
  "layer": "mod",
  "zone": "NO_WTG|NOC|NO_NOC|SPECIAL_ALLOWED|SPECIAL_LIMITED_HEIGHT",
  "name": "Zone name",
  "type": "Zone description",
  "feasibility": "No|NOC|Yes",
  "min_height": "Restricted|83.5m AGL|Not Required",
  "note": "Individual zone explanation"
}
```

## Zone Types

**Airport Zones:**

- `funnel` / `inner`: No WTGs allowed → `"No"`
- `middle`: NOC required with height limits → `"NOC"`
- `outer`: Feasible but NOC recommended → `"Yes"`

**MoD Zones:**

- `NO_WTG`: No WTGs allowed → `"No"`
- `NOC`: NOC required → `"NOC"`
- `NO_NOC`: No NOC needed → `"Yes"`
- `SPECIAL_ALLOWED`: Specially allowed → `"Yes"`
- `SPECIAL_LIMITED_HEIGHT`: 83.5m limit → `"NOC"`

## Example Response

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

## Display Recommendations

**Summary View:**

- Show first item (Combined Analysis) prominently
- Color-code feasibility badge
- Display comprehensive note as main text
- Show zone counts: "Found X airport and Y MoD zones"

**Detail View:**

- Group remaining items by layer type
- Expandable sections for Airport Zones and MoD Zones
- Show individual notes and restrictions

**Batch Processing:**

- Extract only `layer: "combined"` items
- Display as table: Location | Feasibility | Note
- Filter by feasibility status

## Priority Logic

Final feasibility is determined by most restrictive zone:

1. If any zone says "No" → Final is "No"
2. If any zone requires "NOC" → Final is "NOC"
3. If all zones say "Yes" → Final is "Yes"

Most restrictive zone from each layer is mentioned in the comprehensive note.
