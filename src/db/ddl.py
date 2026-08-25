from src.db.connection import db_manager
from src.observability.logger import logger

POSTGRES_DDL = """
CREATE EXTENSION IF NOT EXISTS postgis;

-- 1. Staging Zoning
CREATE TABLE IF NOT EXISTS stg_zoning (
    zoning_id VARCHAR(64) PRIMARY KEY,
    zone_code VARCHAR(32) NOT NULL,
    zone_name VARCHAR(128),
    jurisdiction VARCHAR(64) DEFAULT 'City of Buda',
    is_residential BOOLEAN GENERATED ALWAYS AS (
        zone_code ~* '^(R|Residential)' OR zone_name ~* '^(R|Residential)'
    ) STORED,
    geom GEOMETRY(Geometry, 2277) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_zoning_geom ON stg_zoning USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_zoning_is_res ON stg_zoning (is_residential);

-- 2. Staging Parcels
CREATE TABLE IF NOT EXISTS stg_parcels (
    parcel_id VARCHAR(64) PRIMARY KEY,
    subdivision VARCHAR(128),
    legal_description TEXT,
    raw_stated_area DOUBLE PRECISION,
    geom GEOMETRY(Geometry, 2277) NOT NULL,
    calculated_area_sqft DOUBLE PRECISION GENERATED ALWAYS AS (ST_Area(geom)) STORED,
    calculated_area_acres DOUBLE PRECISION GENERATED ALWAYS AS (ST_Area(geom) / 43560.0) STORED,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_parcels_geom ON stg_parcels USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_parcels_subdiv ON stg_parcels (subdivision);
CREATE INDEX IF NOT EXISTS idx_parcels_acres ON stg_parcels (calculated_area_acres);

-- 3. Enriched Fact View
CREATE OR REPLACE VIEW fct_parcels_enriched AS
SELECT
    p.parcel_id,
    p.subdivision,
    p.legal_description,
    p.calculated_area_sqft,
    p.calculated_area_acres,
    z.zoning_id,
    z.zone_code,
    z.zone_name,
    COALESCE(z.is_residential, FALSE) AS is_residential,
    CASE 
        WHEN z.zoning_id IS NOT NULL THEN 'BUDA_MATCHED'
        ELSE 'UNMATCHED_COUNTY_OUTSIDE_BUDA'
    END AS match_status,
    p.geom
FROM stg_parcels p
LEFT JOIN LATERAL (
    SELECT z.zoning_id, z.zone_code, z.zone_name, z.is_residential
    FROM stg_zoning z
    WHERE ST_Intersects(ST_PointOnSurface(p.geom), z.geom)
    LIMIT 1
) z ON TRUE;

-- 4. Agent & Safety Loop Audit Table
CREATE TABLE IF NOT EXISTS agent_loop_audits (
    audit_id VARCHAR(64) PRIMARY KEY,
    phase_order INTEGER,
    agent_name VARCHAR(64) NOT NULL,
    skills_used VARCHAR(256),
    loop_name VARCHAR(64),
    status VARCHAR(32),
    duration_ms DOUBLE PRECISION,
    records_count INTEGER,
    details TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
"""

DUCKDB_DDL = """
-- DuckDB Tables for local single-file operation
CREATE TABLE IF NOT EXISTS stg_zoning (
    zoning_id VARCHAR PRIMARY KEY,
    zone_code VARCHAR NOT NULL,
    zone_name VARCHAR,
    jurisdiction VARCHAR DEFAULT 'City of Buda',
    is_residential BOOLEAN,
    geom_wkt VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stg_parcels (
    parcel_id VARCHAR PRIMARY KEY,
    subdivision VARCHAR,
    legal_description VARCHAR,
    raw_stated_area DOUBLE,
    geom_wkt VARCHAR,
    calculated_area_sqft DOUBLE,
    calculated_area_acres DOUBLE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fct_parcels_enriched (
    parcel_id VARCHAR PRIMARY KEY,
    subdivision VARCHAR,
    legal_description VARCHAR,
    calculated_area_sqft DOUBLE,
    calculated_area_acres DOUBLE,
    zoning_id VARCHAR,
    zone_code VARCHAR,
    zone_name VARCHAR,
    is_residential BOOLEAN,
    match_status VARCHAR,
    geom_wkt VARCHAR
);

CREATE TABLE IF NOT EXISTS agent_loop_audits (
    audit_id VARCHAR PRIMARY KEY,
    phase_order INTEGER,
    agent_name VARCHAR,
    skills_used VARCHAR,
    loop_name VARCHAR,
    status VARCHAR,
    duration_ms DOUBLE,
    records_count INTEGER,
    details VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def initialize_schemas(backend: str = "duckdb"):
    """Initializes schemas, spatial indexes, and agent audit tables in the chosen backend."""
    if backend == "postgis":
        engine = db_manager.get_postgres_engine()
        with engine.begin() as conn:
            conn.execute(POSTGRES_DDL)
        logger.info("PostGIS DDL and spatial indexes initialized.")
    else:
        conn = db_manager.get_duckdb_connection()
        conn.execute(DUCKDB_DDL)
        logger.info("DuckDB Spatial and Agent audit tables initialized.")
