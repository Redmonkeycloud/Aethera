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

-- Security Tables

-- Users: User accounts
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,  -- bcrypt hash
    full_name TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    oauth_provider TEXT,  -- 'google', 'microsoft', 'okta', etc.
    oauth_sub TEXT,  -- OAuth subject identifier
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Roles: User roles (e.g., admin, analyst, viewer)
CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Permissions: Individual permissions (e.g., 'projects:create', 'reports:read')
CREATE TABLE IF NOT EXISTS permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT UNIQUE NOT NULL,
    resource TEXT NOT NULL,  -- e.g., 'projects', 'reports', 'models'
    action TEXT NOT NULL,  -- e.g., 'create', 'read', 'update', 'delete'
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(resource, action)
);

-- User Roles: Many-to-many relationship
CREATE TABLE IF NOT EXISTS user_roles (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    assigned_by UUID REFERENCES users(id),
    PRIMARY KEY (user_id, role_id)
);

-- Role Permissions: Many-to-many relationship
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE,
    granted_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (role_id, permission_id)
);

-- Refresh Tokens: For JWT token refresh
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    revoked_at TIMESTAMPTZ,
    device_info TEXT,  -- User agent, IP, etc.
    ip_address TEXT
);

-- Audit Logs: Track all security-relevant actions
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    username TEXT,  -- Denormalized for historical records
    action TEXT NOT NULL,  -- e.g., 'LOGIN', 'CREATE_PROJECT', 'DELETE_RUN'
    resource_type TEXT,  -- e.g., 'project', 'run', 'user'
    resource_id TEXT,  -- ID of the affected resource
    ip_address TEXT,
    user_agent TEXT,
    request_method TEXT,  -- HTTP method
    request_path TEXT,  -- API endpoint
    request_body JSONB,  -- Request payload (sanitized)
    response_status INTEGER,  -- HTTP status code
    error_message TEXT,  -- If action failed
    metadata JSONB,  -- Additional context
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for security tables
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_oauth ON users(oauth_provider, oauth_sub);
CREATE INDEX IF NOT EXISTS idx_user_roles_user ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role ON user_roles(role_id);
CREATE INDEX IF NOT EXISTS idx_role_permissions_role ON role_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_role_permissions_permission ON role_permissions(permission_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token ON refresh_tokens(token);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires ON refresh_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at DESC);

-- Default roles and permissions (insert if not exists)
INSERT INTO roles (name, description) VALUES
    ('admin', 'Full system access'),
    ('analyst', 'Can create projects, run analyses, view results'),
    ('viewer', 'Read-only access to projects and reports')
ON CONFLICT (name) DO NOTHING;

-- Default permissions
INSERT INTO permissions (name, resource, action, description) VALUES
    ('projects:create', 'projects', 'create', 'Create new projects'),
    ('projects:read', 'projects', 'read', 'View projects'),
    ('projects:update', 'projects', 'update', 'Update projects'),
    ('projects:delete', 'projects', 'delete', 'Delete projects'),
    ('runs:create', 'runs', 'create', 'Create analysis runs'),
    ('runs:read', 'runs', 'read', 'View analysis runs'),
    ('runs:update', 'runs', 'update', 'Update analysis runs'),
    ('runs:delete', 'runs', 'delete', 'Delete analysis runs'),
    ('reports:read', 'reports', 'read', 'View reports'),
    ('reports:export', 'reports', 'export', 'Export reports'),
    ('models:read', 'models', 'read', 'View model information'),
    ('models:manage', 'models', 'manage', 'Manage model registry'),
    ('users:read', 'users', 'read', 'View user information'),
    ('users:manage', 'users', 'manage', 'Manage users and roles'),
    ('audit:read', 'audit', 'read', 'View audit logs')
ON CONFLICT (resource, action) DO NOTHING;

-- Assign permissions to roles
-- Admin: all permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'admin'
ON CONFLICT DO NOTHING;

-- Analyst: projects, runs, reports (read/export), models (read)
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'analyst'
  AND p.name IN (
    'projects:create', 'projects:read', 'projects:update',
    'runs:create', 'runs:read', 'runs:update',
    'reports:read', 'reports:export',
    'models:read'
  )
ON CONFLICT DO NOTHING;

-- Viewer: read-only access
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'viewer'
  AND p.name IN (
    'projects:read',
    'runs:read',
    'reports:read',
    'models:read'
  )
ON CONFLICT DO NOTHING;

