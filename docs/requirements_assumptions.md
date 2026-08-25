# Requirements, Assumptions & Data Quality Findings

## 1. Assumptions Made

1. **Spatial Unit of "Area" for Summary Roll-up:**
   - *Assumption*: Grouped statistics by `subdivision` (neighborhood/development tract name) as the primary area unit, falling back to `zone_code` when subdivision is unpopulated.
2. **Jurisdiction Mismatch & Boundary Handling:**
   - *Assumption*: Hays County parcels extending outside the municipal limits of the City of Buda are preserved in staging but assigned `match_status = 'UNMATCHED_COUNTY_OUTSIDE_BUDA'`. They are excluded from municipal residential aggregations to prevent unzoned county tracts from distorting Buda statistics.
3. **Multi-Zoning Edge Cases:**
   - *Assumption*: Parcels touching multiple zoning polygons receive the zoning classification containing the parcel's interior representative point (`ST_PointOnSurface`).
4. **Residential Boundary Invariant:**
   - *Assumption*: Mixed-use codes (e.g. `MU-R`) are classified strictly based on prefix matching `^(R|Residential)`.

---

## 2. Questions for Stakeholders & Why They Matter

| # | Question for Stakeholders | Why It Matters (Technical & Business Impact) |
| :--- | :--- | :--- |
| **1** | *"For lots that cross zoning boundaries (e.g. 70% Residential R-1, 30% Commercial C-1), should we assign the dominant zone or split the lot into geometric fractions?"* | Splitting geometries changes the underlying entity from a legal tax parcel to geometric fragments, affecting parcel count metrics and tax roll integrity. |
| **2** | *"What should be the canonical geographic grouping for 'stats by area' (e.g., Subdivision, Census Tract, ZIP Code, or Voting Precinct)?"* | Subdivisions have varying completion rates ($~15\%$ nulls in county records). If stakeholders prefer Census Tracts or ZIP codes, we must ingest an additional administrative boundary layer. |
| **3** | *"How should Mixed-Use districts with residential permissions (e.g., 'MU', 'Downtown Business with Upper Residential') be accounted for?"* | If mixed-use lots with residential housing are excluded under the strict `^R` rule, residential housing capacity will be undercounted. |
| **4** | *"Are condominiums / multi-family vertical units represented as stacked overlapping polygons or single shared master parcels?"* | Vertical condos sharing a single footprint could skew lot size medians downward if individual unit titles are polygonized on top of each other. |

---

## 3. Real-World Data Quality Quirks & Findings

During our initial exploration of the public feeds (City of Buda ArcGIS FeatureServer and Hays County Open Data), we identified the following anomalies:

1. **Stale & Unreliable Stated Acreage Fields:**
   - Many county parcel records contain `stated_area` or `legal_acreage` that differs by up to $35\%$ from the actual planar polygon area, often due to historical deed recording errors or subdivisional splits that were never updated tabularly.
2. **Projection & Unit Inconsistencies:**
   - The ArcGIS REST feeds serve coordinates in geographic WGS84 (`EPSG:4326` in degrees). Calculating area directly on geographic coordinates without planar projection produces meaningless square-degree values. Reprojection to Texas State Plane South Central (`EPSG:2277`) was mandatory.
3. **Jurisdictional Extent Asymmetry:**
   - Hays County parcels cover $> 35,000$ records across the entire county, whereas the City of Buda covers only a small northeastern fraction of the county. A spatial join without proper indexing or jurisdiction filtering results in high join latency and millions of false non-matches.
4. **Self-Intersecting Polygons & Invalid Rings:**
   - Several parcel polygons contained degenerate "bow-tie" self-intersections. Ingesting them into PostGIS without `ST_MakeValid` throws GEOS topology exceptions during spatial intersection.
