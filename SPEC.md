# Spatial Data Pipeline Specification (SPEC.md)

## 1. Objective
Build an idempotent, production-grade geospatial ETL pipeline and analytical data mart that ingests, normalizes, spatial-joins, and analyzes zoning boundaries from the **City of Buda** and parcels from **Hays County**, Texas.

---

## 2. Core Business Rules & Invariants

1. **Residential Classification Rule:**
   - A zoning district is strictly classified as `residential` if and only if its zone code or zone name matches the case-insensitive regular expression:
     $$\text{Pattern: } \text{\textasciicircum(R|Residential)}$$
   - Examples of valid residential zones: `R-1`, `R-2`, `RM`, `Residential - Single Family`, `Residential Estates`.
   - Examples of non-residential zones: `B-1`, `C-2`, `Commercial`, `I-1`, `Agriculture`.

2. **Lot Size Calculation Rule (Mandatory Geodesic Rule):**
   - **Do NOT** read or trust pre-existing tabular area attributes in the raw feeds.
   - Parcel area must be computed dynamically from the polygon geometry.
   - Polygon geometries are projected to the official local coordinate system: **EPSG:2277 (NAD83 / Texas South Central - US Survey Feet)**.
   - Formula for area in acres:
     $$\text{Area}_{\text{acres}} = \frac{\text{ST\_Area}(\text{geom}_{\text{EPSG:2277}})}{43560.0}$$

3. **Spatial Relationship & Jurisdiction Matching:**
   - Hays County parcels encompass the entire county, whereas City of Buda zoning covers only the municipal extent.
   - Point-in-polygon assignment is performed using `ST_PointOnSurface(parcel.geom)` to guarantee the representative point lies strictly inside concave polygons.
   - Parcels with no intersecting Buda zoning polygon are retained in staging and classified as `match_status = 'UNMATCHED_COUNTY_OUTSIDE_BUDA'`.

4. **Aggregation & Area Roll-Up:**
   - Roll-up statistics are aggregated by `subdivision` (neighborhood/development name) or fallback to `zone_code`:
     - Total count of parcels with area $> 1.0\text{ acre}$.
     - Median lot size in acres calculated via continuous 50th percentile: $\text{PERCENTILE\_CONT}(0.5)$.
     - Mean, minimum, and maximum lot size in acres.

---

## 3. Database Schema Contract (PostGIS / DuckDB Spatial)

### Table: `stg_zoning`
- `zoning_id` (VARCHAR PK): Unique identifier for zoning polygon.
- `zone_code` (VARCHAR NOT NULL): Standard zoning acronym.
- `zone_name` (VARCHAR): Descriptive zoning title.
- `jurisdiction` (VARCHAR): Default `'City of Buda'`.
- `is_residential` (BOOLEAN): Computed via regex `^(R|Residential)`.
- `geom` (GEOMETRY EPSG:2277): Validated multipolygon geometry.

### Table: `stg_parcels`
- `parcel_id` (VARCHAR PK): Hays County property identifier / QuickRefID.
- `subdivision` (VARCHAR): Subdivision or neighborhood name.
- `legal_description` (TEXT): Cadastral description.
- `raw_stated_area` (DOUBLE PRECISION): Original area field (retained for audit purposes only).
- `geom` (GEOMETRY EPSG:2277): Validated parcel polygon geometry.
- `calculated_area_sqft` (DOUBLE PRECISION): `ST_Area(geom)`.
- `calculated_area_acres` (DOUBLE PRECISION): `calculated_area_sqft / 43560.0`.

### Table / View: `fct_parcels_enriched`
- `parcel_id` (VARCHAR PK)
- `subdivision` (VARCHAR)
- `legal_description` (TEXT)
- `calculated_area_acres` (DOUBLE PRECISION)
- `zoning_id` (VARCHAR)
- `zone_code` (VARCHAR)
- `zone_name` (VARCHAR)
- `is_residential` (BOOLEAN)
- `match_status` (VARCHAR: `BUDA_MATCHED` or `UNMATCHED_COUNTY_OUTSIDE_BUDA`)
- `geom` (GEOMETRY EPSG:2277)

---

## 4. Operational Invariants & Quality Gates

1. **Idempotency**: Running the pipeline $N$ consecutive times produces identical state, row counts, and checksums without duplicate records.
2. **Security & Input Sanitization**:
   - Geometries with $> 50,000$ vertices are flagged and sanitized to prevent Denial-of-Service / Memory Exhaustion.
   - Bounding boxes outside Texas geographical bounds (Lat $[25^\circ, 37^\circ]$, Lon $[-107^\circ, -93^\circ]$) are rejected.
   - All SQL execution uses parameterized bindings.
3. **Observability**:
   - Structured JSON logging with trace IDs, execution duration in milliseconds, memory usage, and record counts.
   - Sentry APM integration for spans and error context tracking.
