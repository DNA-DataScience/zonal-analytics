# Batch Processing Implementation

## Current Implementation

### Files Created

- **[batch_processor.py](batch_processor.py)**: Core batch processing logic
- **[main.py](main.py)**: Added `POST /batch-generator` endpoint

### What's Working

1. **Optimized Batch Queries**: Two database calls (airport + MoD layers) process up to 100 coordinates simultaneously
2. **Query Structure**: Uses `jsonb_array_elements()` with `UNNEST` for efficient PostGIS spatial intersection
3. **Validation**: Max 100 coordinates per request, minimum 1
4. **Raw Results**: Returns all intersecting zones with coordinate ID (pid) for inspection

### API Endpoint

```
POST /batch-generator
Body: {
  "coordinates": [
    {"id": 1, "lat": 20.43, "lon": 76.12},
    {"id": 2, "lat": 19.07, "lon": 72.87}
  ]
}
```

Returns: JSON with `airport_zones`, `mod_zones`, and summary counts

---

## Next Steps

### 1. Most Restrictive Zone Logic

**Goal**: For each coordinate, determine the single most restrictive zone from each category

#### Airport Priority (most → least restrictive):

- funnel > inner > middle > outer

#### MoD Priority:

- **Special handling**: SPECIAL_ALLOWED or SPECIAL_LIMITED_HEIGHT = most restrictive (overrides all)
- **Otherwise**: NO_WTG > NOC > NO_NOC

**Implementation**: Create helper functions in [batch_processor.py](batch_processor.py):

- `find_most_restrictive_airport_zone(zones: List[Dict]) -> str`
- `find_most_restrictive_mod_zone(zones: List[Dict]) -> str`
- Return format: `"zone_type - zone_name"` or `"No zones exist"`

### 2. Overall Feasibility Determination

Reuse logic from [report_processor.py](report_processor.py#L350-L425) `merge_reports()`:

- Combine airport + MoD most restrictive zones
- Determine final feasibility: "Yes" / "NOC" / "No"
- Map to color: Green / Yellow / Red

### 3. CSV Generation

**Columns**:

1. Latitude
2. Longitude
3. Feasibility Color (Green/Yellow/Red)
4. Most Restrictive Airport Zone
5. Most Restrictive Mod Zone

**Implementation**:

- Use Python `csv.writer` with `StringIO`
- Return as `StreamingResponse` with download headers
- Filename: `batch_report_{timestamp}.csv`

### 4. Testing

- Test with single coordinate
- Test with 100 coordinates
- Verify CSV download in browser
- Validate zone priority logic correctness
