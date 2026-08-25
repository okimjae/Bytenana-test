# Geospatial Data Pipeline: City of Buda & Hays County

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![PostGIS](https://img.shields.io/badge/PostGIS-16--3.4-green.svg)](https://postgis.net/)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A production-grade, spec-driven geospatial ETL pipeline and analytical data product that ingests, normalizes, spatial-joins, and analyzes zoning districts from the **City of Buda** and parcels from **Hays County**, Texas.

Governed by a **4-Agent Collaborative Mesh** with specialized skills and closed safety feedback loops.

---

## ⚡ Quickstart (1-Command Execution)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Complete Pipeline (with Automated Evals)
```bash
python run_pipeline.py
```

### 3. Run Automated Test Suite
```bash
pytest tests/ -v
```

---

## 🏗️ Architecture & Core Invariants

- **Geodesic Accuracy**: Strictly calculates parcel lot size from geometry reprojected to **EPSG:2277 (Texas South Central, US Survey Feet)**, divided by $43,560\text{ sq ft/acre}$.
- **Residential Classification**: Strict regex matching `^(R|Residential)` against zone codes and descriptions.
- **Concave Safety**: Employs `ST_PointOnSurface` to guarantee representative join points lie strictly inside concave or L-shaped lots.
- **Multi-Agent Orchestration**: Decoupled roles for Ingestion, Spatial GIS, Analytics QA, and Documentation with closed safety loops.
- **Idempotency & Security**: Atomic transactions, parameterized queries, vertex limits ($< 50,000$), and bounding box sanity checks.
- **Observability**: Structured JSON logging with execution timings and Sentry APM integration.

---

## 📂 Deliverables & Documentation

1. **[Design Document (Deliverable 1)](docs/design_document.md)**: System decomposition, multi-agent architecture diagram, and key decisions.
2. **[Requirements & Assumptions (Deliverable 2)](docs/requirements_assumptions.md)**: Assumptions, stakeholder questions, and real-world data flaws.
3. **[Process & AI Note (Deliverable 4)](docs/process_ai_note.md)**: Agentic workflow methodology and automated QC guardrails.
4. **[System Specification (SPEC.md)](SPEC.md)**: Formal contracts, database schemas, and invariants.
5. **[Multi-Agent & Skills Architecture (AGENTS.md)](AGENTS.md)**: 4-agent collaborative mesh, skill definitions, and closed feedback loops.

---

## 🐳 Optional: Running with PostGIS Docker Container

```bash
# Start PostGIS container
docker compose up -d

# Run pipeline pointing to PostGIS
python run_pipeline.py --backend postgis
```
