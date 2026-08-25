# AGENTS.md - Multi-Agent Architecture, Sentry Skills & Closed Loops

## 1. Multi-Agent Orchestration Overview

This repository is governed by a **4-Agent Collaborative Mesh**, where each autonomous agent is bounded by specific **Skills** (including native **Sentry APM & Observability Skills**), strict **Invariants**, and operates inside a **Closed Feedback Loop (Safety Gate)**.

```mermaid
flowchart TD
    Orchestrator(["🎯 MASTER ORCHESTRATOR\n(State Machine & Quality Gates)"])

    subgraph Phase1 ["1. Ingestion & Schematization Layer"]
        A_Ingest["📥 Ingestion Agent"]
        S_Ingest["🛠️ Skills: arcgis_rest_crawler, idempotent_db_sink, input_sanitizer, sentry_apm_tracing"]
        L_Ingest{{"🔄 Loop 1: Schema Match & Idempotency Check"}}
    end

    subgraph Phase2 ["2. Spatial & Geodesic Layer"]
        A_Spatial["📐 Spatial GIS Agent"]
        S_Spatial["🛠️ Skills: spatial_projection_2277, postgis_area_calculator, point_on_surface_matcher, sentry_error_context_tagger"]
        L_Spatial{{"🔄 Loop 2: Geodesic Math & Topology Assertions"}}
    end

    subgraph Phase3 ["3. Analytics & QA Layer"]
        A_Analytics["📊 Analytics QA Agent"]
        S_Analytics["🛠️ Skills: zoning_regex_classifier, median_lot_aggregator, radius_proximity_query, sentry_security_anomaly_alerter"]
        L_Analytics{{"🔄 Loop 3: Regression Evals & Boundary Checks"}}
    end

    subgraph Phase4 ["4. Documentation & Defense Layer"]
        A_Docs["📝 Doc & Defense Agent"]
        S_Docs["🛠️ Skills: spec_synthesizer, assumptions_mapper, interview_prep_writer"]
        L_Docs{{"🔄 Loop 4: Assessment Rubric Verification"}}
    end

    Orchestrator --> A_Ingest
    A_Ingest --> S_Ingest --> L_Ingest
    L_Ingest -- "❌ Mismatch (Retry/Repair)" --> A_Ingest
    L_Ingest -- "✅ Approved" --> A_Spatial

    A_Spatial --> S_Spatial --> L_Spatial
    L_Spatial -- "❌ Topology Error (ST_MakeValid)" --> A_Spatial
    L_Spatial -- "✅ Approved" --> A_Analytics

    A_Analytics --> S_Analytics --> L_Analytics
    L_Analytics -- "❌ Assertion Failed" --> A_Analytics
    L_Analytics -- "✅ Approved" --> A_Docs

    A_Docs --> S_Docs --> L_Docs --> Orchestrator
```

---

## 2. Agent Roles, Specialized Skills & Sentry Integration

| Agent | Core Responsibility | Skills Assigned (including Sentry) | Safety Loop & Quality Gate |
| :--- | :--- | :--- | :--- |
| **1. Ingestion Agent** | Extracts data from ArcGIS REST APIs, handles pagination, enforces schema contracts, and manages atomic database ingestion. | • `arcgis_rest_crawler`<br>• `idempotent_db_sink`<br>• `input_sanitizer`<br>• **`sentry_apm_tracing`** | **Loop 1:** Re-executes the ingestion pipeline 2 consecutive times. Measures HTTP latency spans with Sentry APM. Asserts identical row counts, zero primary key collisions, and Texas bounds compliance ($25^\circ \le \text{Lat} \le 37^\circ$). |
| **2. Spatial GIS Agent** | Transforms coordinate reference systems to EPSG:2277, repairs invalid geometries (`ST_MakeValid`), computes planar lot acreage, and matches parcels via `ST_PointOnSurface`. | • `spatial_projection_2277`<br>• `postgis_area_calculator`<br>• `point_on_surface_matcher`<br>• **`sentry_error_context_tagger`** | **Loop 2:** Injects a synthetic $1000 \times 1000\text{ ft}$ square. Asserts computed lot size equals exactly $22.956841\text{ acres}$ (absolute error $< 0.000001\text{ ac}$). Attaches `parcel_id` and WKT to Sentry error context in case of topological anomalies. |
| **3. Analytics QA Agent** | Applies the residential regex rule `^(R|Residential)`, computes continuous medians (`PERCENTILE_CONT(0.5)`), filters lot sizes $> 1.0\text{ ac}$, and calculates 1 km proximity buffers. | • `zoning_regex_classifier`<br>• `median_lot_aggregator`<br>• `radius_proximity_query`<br>• **`sentry_security_anomaly_alerter`** | **Loop 3:** Evaluates a 12-case Golden Dataset of tricky zoning strings. Triggers Sentry anomaly alerts if record volumes skew $> 200\%$ or non-residential zones leak into residential marts. |
| **4. Doc & Defense Agent** | Synthesizes architecture diagrams, assumptions documents, process notes, and prepares interview defense cheat sheets for CTO technical discussions. | • `spec_synthesizer`<br>• `assumptions_mapper`<br>• `interview_prep_writer` | **Loop 4:** Cross-references the generated Markdown artifacts against all evaluation criteria in the take-home prompt to ensure 100% compliance. |

---

## 3. Sentry Observability & Error Intelligence Skills

The repository incorporates three dedicated Sentry skills implemented in `src/observability/sentry_integration.py`:

1. **`sentry_apm_tracing`**:
   - Instruments end-to-end distributed trace spans for external HTTP calls (`fetch_arcgis_zoning`), spatial indexing (`postgis_spatial_join`), and statistical queries (`calculate_median_percentiles`).
2. **`sentry_error_context_tagger`**:
   - Automatically enriches exception stack traces with geospatial metadata (`srid`, `polygon_vertex_count`, `parcel_id`, `calculated_sqft`) when topological repair is needed.
3. **`sentry_security_anomaly_alerter`**:
   - Monitors execution invariants and captures security alert events for out-of-bounds bounding boxes, vertex overflows ($> 50,000$ vertices), and unexpected schema drift.

---

## 4. The 4 Closed Feedback Loops (Safety Gates)

```text
[Loop 1: Ingestion Gate]  ───▶ Ensures Idempotency & Rejects Out-of-Bounds Coords (Sentry Traced)
[Loop 2: Spatial Gate]    ───▶ Validates EPSG:2277 Projection & Sub-Millimeter Area Accuracy
[Loop 3: Analytics Gate]  ───▶ Enforces Zero False-Positive Classifications & Statistical Sanity
[Loop 4: Delivery Gate]   ───▶ Confirms All 4 Take-Home Deliverables are Documented
```

### Self-Correction Mechanism:
- If **Loop 1** detects that an external feed is unreachable or returns malformed GeoJSON, it automatically engages the verified local sample fallback and tags the incident with structured JSON / Sentry logs.
- If **Loop 2** encounters a self-intersecting polygon ("bow-tie" ring), it triggers `shapely.validation.make_valid` / `ST_MakeValid` before attempting area computation.
- If **Loop 3** detects any non-residential zone in `mart_residential_gt_1ac`, it immediately halts execution with an assertion error.

---

## 5. Guidelines for AI Agents Modifying This Codebase

When modifying or extending this repository (e.g., during live coding interview exercises):
1. **Never read raw tabular area fields**: Always compute area dynamically from geometry projected to `EPSG:2277`.
2. **Never interpolate SQL strings**: Always use parameterized query bindings to maintain SQL-injection proofing.
3. **Keep Modules Decoupled**:
   - Ingestion changes $\rightarrow$ `src/ingestion/`
   - Spatial math / Matching $\rightarrow$ `src/spatial/`
   - Queries and Reporting $\rightarrow$ `src/analytics/`
   - Observability & Sentry $\rightarrow$ `src/observability/`
   - Evaluation checks $\rightarrow$ `src/evals/`
4. **Always Run the Safety Loops**:
   ```bash
   # Run all automated tests
   pytest tests/ -v
   
   # Run the full pipeline and evaluation harness
   python run_pipeline.py
   ```
