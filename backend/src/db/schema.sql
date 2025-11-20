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
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS report_embeddings (
    report_id UUID REFERENCES reports_history(id),
    section TEXT NOT NULL,
    embedding VECTOR,  -- Variable dimension to support different embedding models
    metadata JSONB,
    PRIMARY KEY (report_id, section)
);

-- Add index for vector similarity search
CREATE INDEX IF NOT EXISTS idx_report_embeddings_vector ON report_embeddings 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

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

