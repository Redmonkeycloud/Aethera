CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    country TEXT,
    sector TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id TEXT UNIQUE,
    project_id UUID REFERENCES projects(id),
    status TEXT DEFAULT 'completed',
    started_at TIMESTAMPTZ DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS reports_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id),
    run_id UUID REFERENCES runs(id),
    version INTEGER NOT NULL,
    status TEXT NOT NULL,
    summary TEXT,
    storage_path TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS report_embeddings (
    report_id UUID REFERENCES reports_history(id),
    section TEXT NOT NULL,
    embedding VECTOR(1536),
    metadata JSONB,
    PRIMARY KEY (report_id, section)
);

CREATE TABLE IF NOT EXISTS model_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id TEXT NOT NULL,
    model_name TEXT NOT NULL,
    model_version TEXT,
    dataset_source TEXT,
    candidate_models JSONB,
    selected_model TEXT,
    metrics JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

