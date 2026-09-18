import os
import tempfile

os.environ["BANDIT_API_KEY"] = "test-key-123"
_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["BANDIT_DB_PATH"] = _tmp_db.name

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)
client.__enter__()
HEADERS = {"X-API-Key": "test-key-123"}


def test_health_needs_no_auth():
    resp = client.get("/v1/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_recommend_requires_api_key():
    resp = client.post("/v1/recommend", json={"user_id": "u1", "risk_state": "pms"})
    assert resp.status_code == 401


def test_recommend_returns_matching_category_content():
    resp = client.post(
        "/v1/recommend", json={"user_id": "u1", "risk_state": "stress"}, headers=HEADERS
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["risk_state"] == "stress"
    assert body["category"] in {"exercise", "diet", "cbt"}
    assert body["recommendation_id"]


def test_recommend_rejects_invalid_risk_state():
    resp = client.post(
        "/v1/recommend", json={"user_id": "u1", "risk_state": "not_a_state"}, headers=HEADERS
    )
    assert resp.status_code == 422


def test_feedback_updates_arm_stats():
    rec = client.post(
        "/v1/recommend", json={"user_id": "u2", "risk_state": "binge"}, headers=HEADERS
    ).json()

    fb = client.post(
        "/v1/feedback",
        json={"recommendation_id": rec["recommendation_id"], "engaged": True},
        headers=HEADERS,
    )
    assert fb.status_code == 200
    assert fb.json() == {"status": "ok", "recommendation_id": rec["recommendation_id"]}

    stats = client.get("/v1/stats/binge", headers=HEADERS).json()
    arm = next(a for a in stats["arms"] if a["content_id"] == rec["content_id"])
    assert arm["pulls"] == 1
    assert arm["rewards"] == 1
    assert arm["alpha"] == 2.0
    assert arm["beta"] == 1.0


def test_feedback_rejects_duplicate_and_unknown_ids():
    rec = client.post(
        "/v1/recommend", json={"user_id": "u3", "risk_state": "stable"}, headers=HEADERS
    ).json()

    first = client.post(
        "/v1/feedback",
        json={"recommendation_id": rec["recommendation_id"], "engaged": False},
        headers=HEADERS,
    )
    assert first.status_code == 200

    dup = client.post(
        "/v1/feedback",
        json={"recommendation_id": rec["recommendation_id"], "engaged": True},
        headers=HEADERS,
    )
    assert dup.status_code == 409

    unknown = client.post(
        "/v1/feedback",
        json={"recommendation_id": "does-not-exist", "engaged": True},
        headers=HEADERS,
    )
    assert unknown.status_code == 404


def test_stats_rejects_unknown_risk_state():
    resp = client.get("/v1/stats/not_a_state", headers=HEADERS)
    assert resp.status_code == 400


def test_bandit_shifts_traffic_toward_engaged_content():
    risk_state = "pms"
    from app import content

    candidate_ids = [item["id"] for item in content.items_for_context(risk_state)]
    winner = candidate_ids[0]

    for _ in range(60):
        rec = client.post(
            "/v1/recommend", json={"user_id": "learner", "risk_state": risk_state}, headers=HEADERS
        ).json()
        engaged = rec["content_id"] == winner
        client.post(
            "/v1/feedback",
            json={"recommendation_id": rec["recommendation_id"], "engaged": engaged},
            headers=HEADERS,
        )

    counts = {cid: 0 for cid in candidate_ids}
    for _ in range(200):
        rec = client.post(
            "/v1/recommend", json={"user_id": "learner2", "risk_state": risk_state}, headers=HEADERS
        ).json()
        counts[rec["content_id"]] += 1
        client.post(
            "/v1/feedback",
            json={"recommendation_id": rec["recommendation_id"], "engaged": rec["content_id"] == winner},
            headers=HEADERS,
        )

    assert counts[winner] == max(counts.values())
