# CueSoma Recommendation Engine

Turns the Thompson Sampling concept from the IR deck into a working,
customer-facing API: given a user's current risk state (PMS / stress /
binge-eating / stable), it recommends one piece of exercise, diet, or CBT
content, and learns from engagement feedback which content works best for
each risk state, per the "측정 → 맞춤 → 지속" (measure → personalize →
sustain) flow described on the landing page.

## How it works

- Each `(risk_state, content_item)` pair is modeled as a Beta-Bernoulli
  bandit arm (`app/bandit.py`).
- `/v1/recommend` draws one random sample from every candidate arm's
  current Beta(alpha, beta) posterior and serves the item with the
  highest sample — Thompson Sampling's explore/exploit rule.
- `/v1/feedback` reports whether the user engaged with what was served,
  updating that arm's posterior (`alpha += 1` on engagement, `beta += 1`
  otherwise).
- State is persisted in SQLite (`app/db.py`) so recommendations keep
  improving across restarts and across all users sharing a risk state.
- The content catalog (`app/content.py`) is seed data — swap it for a CMS
  or DB table once real content pipelines exist.

## Running it

```bash
cd backend
pip install -r requirements.txt
export BANDIT_API_KEY=your-real-secret   # required for real deployments
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

If `BANDIT_API_KEY` isn't set, a dev-only key is generated and printed to
the logs on first request — fine for local testing, never for production.

## API

All endpoints except `/v1/health` require an `X-API-Key` header.

### `POST /v1/recommend`
```json
// request
{ "user_id": "u123", "risk_state": "pms" }

// response
{
  "recommendation_id": "95e0a3ad-...",
  "content_id": "diet_pms_magnesium",
  "category": "diet",
  "title": "마그네슘 보충 식단 가이드",
  "description": "PMS 부종·근육 긴장 완화를 돕는 마그네슘 함유 식품 가이드.",
  "risk_state": "pms"
}
```
`risk_state` is one of `pms`, `stress`, `binge`, `stable` — this is where
the biosignal/cycle model's risk forecast plugs in.

### `POST /v1/feedback`
```json
// request
{ "recommendation_id": "95e0a3ad-...", "engaged": true }

// response
{ "status": "ok", "recommendation_id": "95e0a3ad-..." }
```
Call this once the client observes whether the user actually engaged with
the recommended content (opened it, completed it, marked it helpful —
define "engaged" to match your product's definition of a positive
outcome). Each `recommendation_id` accepts feedback exactly once.

### `GET /v1/stats/{risk_state}`
Returns every arm's current posterior and estimated engagement rate for
that risk state — useful for an internal dashboard or sanity-checking
that the bandit is learning.

## Tests

```bash
python3 -m pytest -q
```

Covers the Thompson Sampling selection math directly (it favors the
better arm, explores new arms roughly evenly) and the full API flow,
including a test that runs ~260 simulated recommend/feedback cycles and
asserts the engine actually shifts traffic toward the content that gets
positive feedback.

## Wiring it into the real product

1. Have the mobile/web app call `/v1/recommend` whenever the
   biosignal + cycle model flags a risk state, and render the returned
   content.
2. Send `/v1/feedback` when the user's response to that content is known.
3. Replace `app/content.py` with your real content catalog (DB-backed),
   keeping the `target_contexts` tagging so bandit candidates stay scoped
   per risk state.
4. Put this service behind your API gateway/auth layer, set a real
   `BANDIT_API_KEY` (or swap `app/auth.py` for your existing auth), and
   run SQLite on a persistent volume — or swap `app/db.py`'s storage for
   Postgres if you need multi-instance deployment.
