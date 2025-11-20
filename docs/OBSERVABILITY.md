# Observability Guide

This document describes the observability features in AETHERA, including OpenTelemetry tracing, Prometheus metrics, and performance monitoring.

## Overview

AETHERA includes comprehensive observability features:

- **OpenTelemetry Tracing**: Distributed tracing across services
- **Prometheus Metrics**: Application and system metrics
- **Performance Monitoring**: Performance tracking and analysis

## Configuration

Observability is configured via environment variables:

```bash
# Enable/disable tracing
ENABLE_TRACING=true

# OTLP collector endpoint (optional, defaults to console)
OTLP_ENDPOINT=http://localhost:4318/v1/traces

# Service information
SERVICE_NAME=aethera-backend
SERVICE_VERSION=0.1.0

# Enable/disable metrics
ENABLE_METRICS=true

# Metrics server port
METRICS_PORT=9090
```

## OpenTelemetry Tracing

### Setup

Tracing is automatically initialized when the FastAPI app starts. It instruments:

- FastAPI requests/responses
- HTTPX client requests
- PostgreSQL/Psycopg database queries
- Redis operations
- Celery tasks

### Usage

#### Automatic Instrumentation

Most libraries are automatically instrumented. No code changes needed.

#### Manual Tracing

```python
from src.observability.tracing import get_tracer

tracer = get_tracer(__name__)

with tracer.start_as_current_span("my_operation") as span:
    span.set_attribute("key", "value")
    # Your code here
```

#### Function Decorator

```python
from src.observability.tracing import trace_function

@trace_function("my_function")
def my_function():
    # Automatically traced
    pass
```

### Viewing Traces

- **Console**: Traces are logged to console in development
- **OTLP Collector**: Configure `OTLP_ENDPOINT` to send traces to an OTLP collector
- **Jaeger**: Use OTLP collector with Jaeger backend
- **Zipkin**: Use OTLP collector with Zipkin backend

## Prometheus Metrics

### Metrics Endpoint

Metrics are available at `/metrics`:

```bash
curl http://localhost:8000/metrics
```

### Available Metrics

#### HTTP Metrics

- `http_requests_total`: Total HTTP requests by method, endpoint, status
- `http_request_duration_seconds`: HTTP request duration histogram
- `http_request_size_bytes`: HTTP request size histogram

#### Celery Metrics

- `celery_tasks_total`: Total Celery tasks by task name and status
- `celery_task_duration_seconds`: Celery task duration histogram

#### Database Metrics

- `database_queries_total`: Total database queries by operation and table
- `database_query_duration_seconds`: Database query duration histogram

#### Geospatial Metrics

- `geospatial_operations_total`: Total geospatial operations by type
- `geospatial_operation_duration_seconds`: Geospatial operation duration histogram

#### Cache Metrics

- `cache_hits_total`: Total cache hits by cache type
- `cache_misses_total`: Total cache misses by cache type

#### Application Metrics

- `active_runs`: Number of active analysis runs (gauge)
- `service_info`: Service information (info)

### Recording Custom Metrics

```python
from src.observability.metrics import (
    record_database_query,
    record_geospatial_operation,
    record_cache_hit,
    record_cache_miss,
)

# Record database query
record_database_query("SELECT", "projects", duration=0.123)

# Record geospatial operation
record_geospatial_operation("clip", duration=1.456)

# Record cache operations
record_cache_hit("dataset")
record_cache_miss("dataset")
```

### Prometheus Server Setup

1. Install Prometheus: https://prometheus.io/docs/prometheus/latest/installation/

2. Configure `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'aethera'
    static_configs:
      - targets: ['localhost:9090']
```

3. Start Prometheus:

```bash
prometheus --config.file=prometheus.yml
```

4. View metrics in Grafana or Prometheus UI (http://localhost:9090)

## Performance Monitoring

### PerformanceMonitor Class

```python
from src.observability.performance import PerformanceMonitor

monitor = PerformanceMonitor("my_operation")
monitor.start()
# ... do work ...
duration = monitor.stop()
monitor.log_summary()
```

### Context Manager

```python
from src.observability.performance import measure_operation

with measure_operation("my_operation") as monitor:
    # ... do work ...
    monitor.record_metric("items_processed", 100)
# Automatically logs summary
```

### Function Decorator

```python
from src.observability.performance import measure_time

@measure_time
def my_function():
    # Automatically measured and logged
    pass
```

## Observability Endpoints

### Health Check

```bash
GET /observability/health
```

Returns service health status and observability configuration.

### Diagnostics

```bash
GET /observability/diagnostics
```

Returns detailed service diagnostics.

### Metrics Registry Info

```bash
GET /observability/metrics/registry
```

Returns information about the metrics registry.

## Integration with Monitoring Tools

### Grafana

1. Install Grafana: https://grafana.com/docs/grafana/latest/installation/

2. Add Prometheus as data source:
   - URL: `http://localhost:9090`
   - Access: Server (default)

3. Create dashboards for:
   - HTTP request rates and latencies
   - Celery task performance
   - Database query performance
   - Geospatial operation metrics

### Jaeger

1. Install Jaeger: https://www.jaeger.io/docs/latest/getting-started/

2. Configure OTLP endpoint:
   ```bash
   OTLP_ENDPOINT=http://localhost:4318/v1/traces
   ```

3. View traces in Jaeger UI: http://localhost:16686

## Best Practices

1. **Use meaningful span names**: Use descriptive names like "process_aoi" not "func1"

2. **Add relevant attributes**: Include context like project_id, run_id, etc.

3. **Don't over-instrument**: Focus on important operations

4. **Monitor key metrics**: Track request rates, error rates, latencies

5. **Set up alerts**: Configure alerts for high error rates or latency

6. **Regular review**: Review traces and metrics to identify bottlenecks

## Troubleshooting

### Tracing not working

- Check `ENABLE_TRACING=true` is set
- Verify OpenTelemetry packages are installed
- Check logs for instrumentation errors

### Metrics not available

- Check `ENABLE_METRICS=true` is set
- Verify metrics port is not in use
- Check `/metrics` endpoint is accessible

### High overhead

- Disable tracing/metrics in development if needed
- Use sampling for high-traffic endpoints
- Monitor observability overhead

