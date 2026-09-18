from typing import Literal

from pydantic import BaseModel, Field

RiskState = Literal["pms", "stress", "binge", "stable"]


class RecommendRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=128)
    risk_state: RiskState


class RecommendResponse(BaseModel):
    recommendation_id: str
    content_id: str
    category: str
    title: str
    description: str
    risk_state: RiskState


class FeedbackRequest(BaseModel):
    recommendation_id: str
    engaged: bool


class FeedbackResponse(BaseModel):
    status: str
    recommendation_id: str


class ArmStat(BaseModel):
    content_id: str
    title: str
    category: str
    alpha: float
    beta: float
    pulls: int
    rewards: int
    estimated_engagement_rate: float


class StatsResponse(BaseModel):
    risk_state: RiskState
    arms: list[ArmStat]
