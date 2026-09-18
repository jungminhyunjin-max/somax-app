from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException

from . import content, db
from .auth import require_api_key
from .bandit import ArmPosterior, posterior_mean, select_arm
from .models import (
    ArmStat,
    FeedbackRequest,
    FeedbackResponse,
    RecommendRequest,
    RecommendResponse,
    StatsResponse,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init_db()
    yield


app = FastAPI(
    title="CueSoma Recommendation Engine",
    description="Thompson Sampling based exercise / diet / CBT content recommender.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/v1/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/v1/recommend", response_model=RecommendResponse, dependencies=[Depends(require_api_key)])
def recommend(req: RecommendRequest) -> RecommendResponse:
    candidates = content.items_for_context(req.risk_state)
    context_key = req.risk_state

    with db.session() as conn:
        arms = [
            ArmPosterior(content_id=item["id"], alpha=row["alpha"], beta=row["beta"])
            for item in candidates
            for row in [db.get_or_create_arm(conn, context_key, item["id"])]
        ]
        chosen = select_arm(arms)
        rec_id = db.log_recommendation(conn, req.user_id, context_key, chosen.content_id)

    item = content.get_item(chosen.content_id)
    return RecommendResponse(
        recommendation_id=rec_id,
        content_id=item["id"],
        category=item["category"],
        title=item["title"],
        description=item["description"],
        risk_state=req.risk_state,
    )


@app.post("/v1/feedback", response_model=FeedbackResponse, dependencies=[Depends(require_api_key)])
def feedback(req: FeedbackRequest) -> FeedbackResponse:
    reward = 1 if req.engaged else 0
    with db.session() as conn:
        rec = db.get_recommendation(conn, req.recommendation_id)
        if rec is None:
            raise HTTPException(status_code=404, detail="unknown recommendation_id")
        if rec["rewarded"] is not None:
            raise HTTPException(status_code=409, detail="feedback already recorded for this recommendation")
        db.update_arm(conn, rec["context_key"], rec["content_id"], reward)
        db.mark_recommendation_rewarded(conn, req.recommendation_id, reward)

    return FeedbackResponse(status="ok", recommendation_id=req.recommendation_id)


@app.get("/v1/stats/{risk_state}", response_model=StatsResponse, dependencies=[Depends(require_api_key)])
def stats(risk_state: str) -> StatsResponse:
    if risk_state not in content.RISK_STATES:
        raise HTTPException(status_code=400, detail=f"risk_state must be one of {content.RISK_STATES}")

    with db.session() as conn:
        rows = db.arms_for_context(conn, risk_state)

    arm_stats = []
    for row in rows:
        item = content.get_item(row["content_id"])
        if item is None:
            continue
        arm = ArmPosterior(content_id=row["content_id"], alpha=row["alpha"], beta=row["beta"])
        arm_stats.append(
            ArmStat(
                content_id=item["id"],
                title=item["title"],
                category=item["category"],
                alpha=row["alpha"],
                beta=row["beta"],
                pulls=row["pulls"],
                rewards=row["rewards"],
                estimated_engagement_rate=posterior_mean(arm),
            )
        )

    return StatsResponse(risk_state=risk_state, arms=arm_stats)
