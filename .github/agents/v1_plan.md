## Plan: UMDScheduler v1 Deployment Hardening

Bring the project to production-ready v1 by implementing abuse controls, compute guardrails, upstream protection, security hardening, observability, deployment hygiene, and CI/test gates in phased order. Prioritize P0 controls that prevent service abuse and external API overuse, then validate with load/negative tests before canary rollout.

**Steps**

### Phase 0 — Blockers (must complete before public v1)
1. Establish production configuration and secret management baseline.
   - Create environment templates for backend/frontend and document required variables.
   - Centralize runtime config loading and validation.
   - *Blocks steps 2–7.*

2. Implement API abuse protection and endpoint budgets.
   - Add per-IP global limiter and per-route limits (especially strict for `POST /api/v1/schedules`).
   - Add burst controls and standard `429` responses.
   - Add route-level request-size/body guards for schedule payloads.
   - *Depends on step 1.*

3. Add schedule-generation compute guardrails.
   - Enforce strict bounds for required/optional courses, constraints, and excluded professor counts.
   - Add generation timeout and early termination when search space explodes.
   - Add deterministic cap on returned schedules and fail-fast pruning rules.
   - *Depends on step 1, parallel with step 4.*

4. Protect upstream usage (PlanetTerp/Testudo) with respectful limits.
   - Add timeout, retry with backoff+jitter, and circuit-breaker behavior for all external requests.
   - Route PlanetTerp access through backend cache/proxy to avoid uncontrolled browser fan-out.
   - Reduce scraper concurrency and add pacing/crawl politeness and 429 handling.
   - *Depends on step 1, parallel with step 3.*

5. Harden API transport/security defaults.
   - Add security headers and strict CORS allowlist validation.
   - Keep `allow_credentials` only where necessary and fail closed on malformed origin config.
   - Add request correlation IDs for traceability.
   - *Depends on step 1, parallel with step 3 and 4.*

6. Add baseline observability and actionable alerts.
   - Structured logs with route, status, latency, request-id.
   - Metrics for schedule compute duration, upstream failures, limiter hits, pool pressure.
   - Alerting rules for high error rate, high latency, and degraded upstream health.
   - *Depends on steps 2–5.*

7. Fix frontend quality-gate issues and correctness bug.
   - Resolve `checkJs` implicit-any warnings in `scheduleUtils.js`.
   - Fix markdown lint warning in frontend README.
   - Fix prohibited-professor counter text bug in `App.svelte`.
   - *Parallel with steps 2–6 once step 1 is done.*

### Phase 1 — Reliability and verification
8. Build comprehensive automated test coverage for critical flows.
   - Backend unit tests: scheduler conflict logic, payload validation, rate limit behavior, upstream wrapper behavior.
   - Integration tests: core API endpoints and degraded-upstream fallbacks.
   - Frontend tests: data client cache/error behavior and core component smoke tests.
   - *Depends on completion of phase 0 implementation.*

9. Add CI quality and security gates.
   - PR gates: backend tests, frontend lint/type checks, build verification.
   - Security checks: dependency audit/scans and secret scanning.
   - Enforce passing status before merge/deploy.
   - *Parallel with step 8.*

10. Execute load, stress, and abuse-focused validation.
   - Validate limiter behavior and schedule endpoint under concurrent load.
   - Validate timeout behavior and fallback response quality.
   - Validate no upstream request stampede under cache misses.
   - *Depends on steps 8–9.*

### Phase 2 — Deployment readiness and launch control
11. Add deployment runbook and production manifests.
   - Document build/start commands, env setup, health checks, rollback steps.
   - Add deployment config artifacts for the selected hosting platform(s).
   - *Depends on phase 1 gates passing.*

12. Launch using staged canary rollout and feature flags.
   - Rollout progression: low traffic slice → medium slice → full traffic.
   - Gate progression on error rate, p95 latency, schedule success rate, upstream health.
   - Maintain instant rollback path.
   - *Depends on step 11.*

13. Final pre-launch review and scope lock.
   - Confirm all P0/P1 items completed and verified.
   - Freeze non-critical feature work until 48h post-launch stability window passes.
   - *Final step.*

**Relevant files**
- `/Users/nicocarbone/Documents/dev/umdscheduler/backend/api/main.py` — add middleware wiring, stricter CORS parsing/validation, security headers, request-id support.
- `/Users/nicocarbone/Documents/dev/umdscheduler/backend/api/scheduler.py` — add generation timeout, early-stop pruning, guardrails for combinatorial explosion, upstream-call delegation.
- `/Users/nicocarbone/Documents/dev/umdscheduler/backend/api/schemas.py` — tighten payload constraints (`required_courses`, `optional_courses`, constraints/professor list limits).
- `/Users/nicocarbone/Documents/dev/umdscheduler/backend/api/database.py` — add safety around pool errors/metrics instrumentation.
- `/Users/nicocarbone/Documents/dev/umdscheduler/backend/common/db_config.py` — make pool/timeout/keepalive settings configurable via env and production-safe defaults.
- `/Users/nicocarbone/Documents/dev/umdscheduler/backend/scraper/scraper.py` — reduce concurrency, add retries/backoff, pacing, and clear upstream-failure handling.
- `/Users/nicocarbone/Documents/dev/umdscheduler/backend/scraper/dbmanager.py` — add stronger error handling/metrics around ingestion and DB update paths.
- `/Users/nicocarbone/Documents/dev/umdscheduler/frontend/src/lib/utils/dataClient.js` — move PlanetTerp fetches behind backend endpoints or strict client throttling fallback; strengthen timeout/error/cache behavior.
- `/Users/nicocarbone/Documents/dev/umdscheduler/frontend/src/lib/utils/scheduleUtils.js` — resolve `checkJs` type warnings with JSDoc typing.
- `/Users/nicocarbone/Documents/dev/umdscheduler/frontend/src/App.svelte` — fix prohibited-professors count display and verify schedule-request payload guardrails in UI.
- `/Users/nicocarbone/Documents/dev/umdscheduler/frontend/README.md` — fix markdown lint issue and align run/deploy docs.
- `/Users/nicocarbone/Documents/dev/umdscheduler/.github/workflows/scraper.yml` — add safeguards/retry strategy and observability outputs for scraper execution.
- `/Users/nicocarbone/Documents/dev/umdscheduler/.github/workflows/test.yml` — add backend/frontend automated test gates (new file).
- `/Users/nicocarbone/Documents/dev/umdscheduler/.github/workflows/lint.yml` — add lint/type gates (new file).
- `/Users/nicocarbone/Documents/dev/umdscheduler/.github/workflows/security.yml` — add dependency/security scanning (new file).
- `/Users/nicocarbone/Documents/dev/umdscheduler/backend/.env.example` — required backend env template (new file).
- `/Users/nicocarbone/Documents/dev/umdscheduler/frontend/.env.example` — required frontend env template (new file).
- `/Users/nicocarbone/Documents/dev/umdscheduler/SECURITY.md` — security policy, disclosure process, and operational guardrails (new file).
- `/Users/nicocarbone/Documents/dev/umdscheduler/DEPLOYMENT_RUNBOOK.md` — deployment/canary/rollback instructions (new file).

**Suggested defaults (v1 conservative profile)**
1. API limits
   - Global: 300–600 req/min per IP.
   - `POST /api/v1/schedules`: 5–12 req/min per IP, small burst only.
2. Scheduler bounds
   - Required courses max: 6.
   - Optional courses max: 3–4.
   - Time-constraint slots max: 10.
   - Excluded professors max: 50.
   - Generation timeout: 20–30 seconds hard cap.
   - Returned schedules cap: 100 (UI can still display fewer by default).
3. Upstream protection
   - PlanetTerp timeout: 2–3 seconds; retries: up to 2–3 with jittered exponential backoff.
   - Circuit breaker opens on repeated failures and serves cache/degraded response.
   - Cache TTL: ratings/course metadata 12–24h; short TTL for unstable endpoints.
4. Scraper responsibility
   - `MAX_WORKERS` reduce from 25 to ~8–15.
   - Add inter-request pacing and explicit 429/5xx backoff.
5. DB runtime safety
   - Production-tuned pool sizes from env, statement timeout, and connection lifetime limits.

**Verification**
1. Static quality checks pass in CI:
   - Backend type/lint checks and frontend lint/type checks.
2. Unit/integration tests pass for:
   - Scheduler correctness and guardrails.
   - Rate-limiting behavior (`429` and retry semantics).
   - Upstream wrapper timeout/retry/circuit fallback.
3. Abuse-focused tests pass:
   - Oversized schedule payloads rejected with `422`.
   - High-frequency schedule requests throttled.
   - Upstream outage returns degraded but stable responses.
4. Load validation passes:
   - Concurrent schedule traffic does not crash API or starve DB pool.
   - p95 latency and error-rate remain inside agreed release thresholds.
5. Launch-readiness checks pass:
   - Runbook dry run (deploy + rollback).
   - Canary progression gates satisfied before 100% rollout.

**Decisions**
- Included in this v1-hardening push:
  - Abuse/rate controls, compute guardrails, upstream protection, security headers/CORS hardening, observability baseline, tests/CI gates, deployment docs, and frontend quality fixes.
- Deliberately excluded from this push:
  - Full user account/auth product, advanced analytics, major feature additions, and non-essential refactors.
- Architecture preference:
  - Keep API publicly consumable without full user auth for v1, but enforce strict per-IP and per-route limits plus optional service key path for trusted internal operations.

**Further Considerations**
1. Deployment target choice should be fixed early (single provider first) to avoid duplicate infra work.
2. If direct browser-to-PlanetTerp calls are retained temporarily, enforce very conservative client-side throttling and migrate behind backend ASAP.
3. Use staged flags for riskier scheduler guardrail changes so ranking behavior can be tuned without full rollback.