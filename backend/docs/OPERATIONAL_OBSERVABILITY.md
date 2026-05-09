# OVM Enterprise Observability & Operational Monitoring

## 1. Scheduler Observability
Background operational scanning jobs (Alerts, SLAs, Risk) are monitored via APScheduler event listeners in `app/core/scheduler.py`.
- **Start/End/Duration**: Tracked dynamically.
- **Failures & Misses**: Automatically recorded to `metrics.job_failure_total` and `metrics.job_skipped_total`.
- **Visibility**: Exposes via `GET /ops/scheduler/jobs` and visible on the React frontend Operations Dashboard.

## 2. Request Tracing Middleware
Every request is instrumented by `RequestTracingMiddleware` (`app/middleware/tracing.py`).
- **Correlation ID**: Validates or issues `X-Request-ID` and stores it safely via contextvars.
- **Latency & Status**: Emits a single structured log line per request natively including duration (ms), endpoint, and method.
- **Exception Tracing**: Traps 500s safely and emits exception stack traces directly into structured logs.

## 3. Metrics Lifecycle
Application-level telemetry is maintained via `MetricsRegistry` in `app/services/metrics.py`.
- **Thread-safe**: Increments and observations utilize `threading.Lock`.
- **Dimensions**: Segments metrics into `system`, `workflow`, `idp`, and `scheduler`.
- **API Exfiltration**: Consumed globally through `GET /ops/metrics` and visualized on the Operations Dashboard.

## 4. Retry Handling & Failure Tracking
The `OperationalError` append-only store tracks out-of-band execution failures:
- **Centralized Tracking**: Captures OCR, notification, and scheduler pipeline failures.
- **Retries**: Flags whether an action is `retryable` and logs the `retry_count`.
- **Isolation**: Prevents cascading operational failures from interrupting strict financial workflows.

## 5. Operational Debugging Flow
When diagnosing issues in OVM production:
1. Identify macro health from the **Operations Dashboard** (`/ops`).
2. Search Kibana/Splunk for correlation IDs logged via `JSONFormatter`.
3. Check `GET /ops/errors/recent` for failing async processes.
4. Verify backend dependencies via `GET /health` (`db`, `redis`, `scheduler`, `ocr`, `storage`).
