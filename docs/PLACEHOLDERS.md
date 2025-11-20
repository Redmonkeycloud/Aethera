# Placeholders & Future Implementation Guide

This document catalogs all placeholders, TODOs, and future implementation items across the AETHERA codebase. Items are organized by phase and component.

## Phase 4 - Biodiversity AI & Legal Rules Engine ✅ COMPLETE

### Legal Rules Engine - ✅ **IMPLEMENTED**
- **Location**: `backend/src/legal/`
- **Status**: Fully implemented
- **Completed**:
  - ✅ YAML/JSON country-specific rules format
  - ✅ Parser/evaluator for rule evaluation (`RuleParser`, `LegalEvaluator`)
  - ✅ Compliance status generation with severity levels
  - ✅ Integration with backend orchestrator
  - ✅ 41 rules implemented for 4 countries (DEU, FRA, ITA, GRC)
  - ✅ Comprehensive source bibliography

### Legal Determinations Integration - ✅ **COMPLETE**
- **Location**: `backend/src/main_controller.py`
- **Status**: Fully integrated
- **Completed**:
  - ✅ Legal engine outputs wired into run results
  - ✅ Legal determinations appended to manifest
  - ✅ Results saved to `legal_evaluation.json`
  - ✅ `--country` argument added to CLI

## Phase 5 - Backend API & Orchestration ✅ COMPLETE

### Celery Workers - ✅ **IMPLEMENTED**
- **Location**: `backend/src/workers/`
- **Status**: Fully implemented
- **Completed**:
  - ✅ Async task queue for heavy geospatial operations
  - ✅ Integration with FastAPI endpoints
  - ✅ Task status tracking (`TaskTracker`)
  - ✅ Error handling and progress updates
  - ✅ Task cancellation support

### Storage Abstraction - ✅ **IMPLEMENTED**
- **Location**: `backend/src/storage/`
- **Status**: Fully implemented
- **Completed**:
  - ✅ Abstract storage interface (`StorageBackend`)
  - ✅ Local filesystem backend (`LocalStorageBackend`)
  - ✅ S3-compatible backend (`S3StorageBackend`)
  - ✅ Factory pattern for backend creation
  - ✅ File operations (save, read, delete, list, get_url)

### Additional API Endpoints - ✅ **IMPLEMENTED**
- **Status**: All endpoints implemented
- **Completed**:
  - ✅ `POST /projects/{id}/runs` - Trigger new analysis run (async)
  - ✅ `GET /runs/{id}/results` - Comprehensive results endpoint
  - ✅ `GET /runs/{id}/legal` - Legal compliance results
  - ✅ `GET /runs/{id}/export` - Export package download (ZIP)
  - ✅ `GET /tasks/{task_id}` - Task status polling
  - ✅ `DELETE /tasks/{task_id}` - Cancel task

## Phase 6 - Frontend Application

### Frontend Application - **PLACEHOLDER**
- **Location**: `frontend/`
- **Status**: Only README placeholder exists
- **Requirements**:
  - React + Vite + TypeScript setup
  - MapLibre GL JS integration
  - AOI upload/draw tool
  - Scenario form
  - Layer controls
  - Indicator panels
  - Result download area
  - Run status polling
  - Map layer management

## Phase 7 - Reporting, Learning Memory & Automation

### Report Learning Memory - **PLACEHOLDER**
- **Location**: `backend/src/reporting/report_memory.py`
- **Status**: In-memory placeholder only
- **Current Implementation**:
  - `ReportMemoryStore` class exists but only stores in memory
  - `find_similar()` method is a stub
- **Missing**:
  - Database-backed storage (PostgreSQL + pgvector)
  - Semantic similarity search using embeddings
  - Integration with `reports_history` and `report_embeddings` tables
  - FAISS or pgvector integration for vector search
- **TODO**: Line 45 - `# TODO: integrate pgvector/FAISS to search by semantic similarity.`

### Report Engine - **PARTIAL**
- **Location**: `backend/src/reporting/engine.py`
- **Status**: Basic template rendering exists
- **Missing**:
  - Retrieval-augmented generation (RAG)
  - Similar report section retrieval
  - Context augmentation from past reports
  - Integration with report memory store
- **Placeholder**: Line 31 - `# Placeholder hook: future versions will retrieve similar report sections and augment context.`

### Report Template - **PLACEHOLDER**
- **Location**: `backend/src/reporting/templates/base_report.md.jinja`
- **Status**: Basic template structure exists
- **Missing**:
  - Comprehensive EIA chapter templates
  - Docx export support (python-docx)
  - PDF generation (Playwright/WeasyPrint)
  - Excel/CSV export
  - Scenario comparison sections
  - Versioning support

### Report Export Formats - **NOT IMPLEMENTED**
- **Location**: `backend/src/reporting/exports/` (to be created)
- **Status**: Missing
- **Requirements**:
  - CSV/Excel table exports
  - Shapefile/GeoPackage exports
  - PDF summary generation
  - Playwright or WeasyPrint integration
  - Export package bundling

### Reviewer Feedback Ingestion - **NOT IMPLEMENTED**
- **Location**: `backend/src/reporting/feedback/` (to be created)
- **Status**: Missing
- **Requirements**:
  - Feedback ingestion API
  - Automatic memory store updates
  - Version tracking
  - Approval/rejection workflow

## Cross-Cutting Concerns

### Testing - **PARTIALLY IMPLEMENTED**
- **Status**: Basic pytest setup exists
- **Missing**:
  - Comprehensive test coverage
  - Hypothesis for property-based testing
  - Playwright tests for frontend
  - Integration tests for full pipeline
  - Performance/load testing

### Observability - **NOT IMPLEMENTED**
- **Location**: `backend/src/observability/` (to be created)
- **Status**: Missing
- **Requirements**:
  - OpenTelemetry traces
  - Prometheus metrics
  - Structured logging (partially done)
  - Performance monitoring
  - Error tracking

### Performance Optimizations - **PARTIALLY IMPLEMENTED**
- **Status**: Dataset caching exists
- **Missing**:
  - Tiling/chunking for large AOIs
  - Dask-Geopandas integration
  - Advanced geospatial join caching
  - Raster processing optimizations

### Security - **NOT IMPLEMENTED**
- **Location**: `backend/src/auth/` (to be created)
- **Status**: Missing
- **Requirements**:
  - RBAC (Role-Based Access Control)
  - OAuth/OpenID Connect integration
  - Audit logs
  - API authentication/authorization
  - Data encryption at rest

### Model Governance - **PARTIALLY IMPLEMENTED**
- **Status**: Model run logging exists
- **Missing**:
  - Comprehensive model versioning
  - Drift detection
  - Model validation pipelines
  - A/B testing framework
  - Model registry management

## Data & Datasets

### External Dataset Integration - **PARTIALLY IMPLEMENTED**
- **Status**: Basic biodiversity sources exist
- **Missing**:
  - Automated dataset discovery
  - Vetted source catalog expansion
  - Automatic dataset updates
  - Data quality validation
  - Dataset versioning

### Training Data - **PARTIALLY IMPLEMENTED**
- **Status**: Synthetic data generation exists
- **Missing**:
  - Real-world training dataset collection
  - Data augmentation pipelines
  - Label quality assurance
  - Training data versioning

## Infrastructure

### CI/CD - **PARTIALLY IMPLEMENTED**
- **Status**: Basic GitHub Actions workflow exists
- **Missing**:
  - TypeScript/ESLint linting (frontend not yet created)
  - Comprehensive test coverage requirements
  - Automated deployment
  - Docker image publishing
  - Release automation

### Development Environment - **PARTIALLY IMPLEMENTED**
- **Status**: Basic setup scripts exist
- **Missing**:
  - Node.js/pnpm setup for frontend
  - Complete environment validation
  - Development container support
  - Pre-commit hooks for all file types

## Documentation

### API Documentation - **PARTIALLY IMPLEMENTED**
- **Status**: FastAPI auto-docs exist
- **Missing**:
  - Comprehensive API examples
  - Integration guides
  - Error code documentation
  - Rate limiting documentation

### User Documentation - **PARTIALLY IMPLEMENTED**
- **Status**: Basic README and setup guides exist
- **Missing**:
  - End-user guides
  - Tutorials
  - Video walkthroughs
  - FAQ

## Notes

- Items marked as "PLACEHOLDER" have skeleton code but need full implementation
- Items marked as "NOT IMPLEMENTED" are completely missing
- Items marked as "PARTIALLY IMPLEMENTED" have some functionality but need completion
- Priority levels should be determined based on project roadmap and user needs

## Update History

- **2025-01-XX**: Initial placeholder documentation created
- This document should be updated as placeholders are implemented or new ones are identified

