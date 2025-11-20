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

-- Model Governance Tables

-- Model Registry: Centralized model versioning and lifecycle management
CREATE TABLE IF NOT EXISTS model_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name TEXT NOT NULL,
    version TEXT NOT NULL,
    stage TEXT NOT NULL DEFAULT 'development',  -- development, staging, production, archived
    description TEXT,
    model_path TEXT,  -- Path to serialized model file
    training_data_hash TEXT,  -- Hash of training data for reproducibility
    hyperparameters JSONB,
    training_metadata JSONB,  -- Training date, duration, dataset info
    created_by TEXT,
    approved_by TEXT,
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(model_name, version)
);

-- Indexes for model registry
CREATE INDEX IF NOT EXISTS idx_model_registry_name ON model_registry(model_name);
CREATE INDEX IF NOT EXISTS idx_model_registry_stage ON model_registry(stage);
CREATE INDEX IF NOT EXISTS idx_model_registry_created ON model_registry(created_at DESC);

-- Model Validation Metrics: Track performance metrics per model version
CREATE TABLE IF NOT EXISTS model_validation_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_registry_id UUID REFERENCES model_registry(id) ON DELETE CASCADE,
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    metric_name TEXT NOT NULL,  -- e.g., 'accuracy', 'precision', 'recall', 'f1', 'r2', 'mae', 'rmse'
    metric_value NUMERIC NOT NULL,
    metric_type TEXT NOT NULL,  -- 'classification', 'regression', 'ensemble'
    dataset_split TEXT,  -- 'train', 'validation', 'test'
    metadata JSONB,  -- Additional context (thresholds, class-specific metrics, etc.)
    evaluated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(model_registry_id, metric_name, dataset_split)
);

-- Indexes for validation metrics
CREATE INDEX IF NOT EXISTS idx_validation_metrics_model ON model_validation_metrics(model_name, model_version);
CREATE INDEX IF NOT EXISTS idx_validation_metrics_evaluated ON model_validation_metrics(evaluated_at DESC);

-- Model Drift Detection: Track data and concept drift
CREATE TABLE IF NOT EXISTS model_drift_detection (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_registry_id UUID REFERENCES model_registry(id) ON DELETE CASCADE,
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    drift_type TEXT NOT NULL,  -- 'data_drift', 'concept_drift', 'prediction_drift'
    feature_name TEXT,  -- Specific feature if applicable
    drift_score NUMERIC NOT NULL,  -- Drift magnitude (0-1 or distance metric)
    threshold NUMERIC NOT NULL,  -- Alert threshold
    is_alert BOOLEAN DEFAULT FALSE,  -- Whether drift exceeds threshold
    reference_statistics JSONB,  -- Baseline statistics
    current_statistics JSONB,  -- Current statistics
    detection_method TEXT,  -- 'ks_test', 'psi', 'chi_square', 'kl_divergence', etc.
    sample_size INTEGER,
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    acknowledged_at TIMESTAMPTZ,
    acknowledged_by TEXT
);

-- Indexes for drift detection
CREATE INDEX IF NOT EXISTS idx_drift_model ON model_drift_detection(model_name, model_version);
CREATE INDEX IF NOT EXISTS idx_drift_alert ON model_drift_detection(is_alert, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_drift_type ON model_drift_detection(drift_type);

-- A/B Testing Framework: Compare model versions
CREATE TABLE IF NOT EXISTS model_ab_tests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    test_name TEXT NOT NULL,
    description TEXT,
    model_a_registry_id UUID REFERENCES model_registry(id) ON DELETE SET NULL,  -- Control model
    model_b_registry_id UUID REFERENCES model_registry(id) ON DELETE SET NULL,  -- Treatment model
    model_a_name TEXT NOT NULL,
    model_a_version TEXT NOT NULL,
    model_b_name TEXT NOT NULL,
    model_b_version TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',  -- draft, running, completed, cancelled
    traffic_split NUMERIC DEFAULT 0.5,  -- Percentage of traffic to model B (0-1)
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTZ,
    min_samples INTEGER DEFAULT 100,  -- Minimum samples before evaluation
    success_metric TEXT NOT NULL,  -- Primary metric to compare (e.g., 'accuracy', 'f1', 'r2')
    success_threshold NUMERIC,  -- Minimum improvement to consider B better
    statistical_test TEXT DEFAULT 't_test',  -- 't_test', 'mann_whitney', 'chi_square'
    significance_level NUMERIC DEFAULT 0.05,
    created_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- A/B Test Results: Track performance comparison
CREATE TABLE IF NOT EXISTS model_ab_test_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ab_test_id UUID REFERENCES model_ab_tests(id) ON DELETE CASCADE,
    metric_name TEXT NOT NULL,
    model_a_value NUMERIC NOT NULL,
    model_b_value NUMERIC NOT NULL,
    difference NUMERIC NOT NULL,  -- model_b_value - model_a_value
    relative_improvement NUMERIC,  -- (difference / model_a_value) * 100
    p_value NUMERIC,  -- Statistical significance
    is_significant BOOLEAN,  -- Whether difference is statistically significant
    confidence_interval_lower NUMERIC,
    confidence_interval_upper NUMERIC,
    sample_size_a INTEGER,
    sample_size_b INTEGER,
    evaluated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for A/B tests
CREATE INDEX IF NOT EXISTS idx_ab_tests_status ON model_ab_tests(status, start_date);
CREATE INDEX IF NOT EXISTS idx_ab_test_results_test ON model_ab_test_results(ab_test_id);

