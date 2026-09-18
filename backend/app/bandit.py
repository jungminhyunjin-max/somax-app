"""Thompson Sampling for content recommendation (exercise / diet / CBT).

Each (risk context, content item) pair is modeled as an independent
Beta-Bernoulli arm. To recommend, we draw one sample from each candidate
arm's current Beta(alpha, beta) posterior and serve the item with the
highest sample — the standard Thompson Sampling exploration/exploitation
rule. Feedback (did the user engage with the content) updates that arm's
posterior, so the engine keeps adapting per risk state as real usage data
comes in.
"""

import random
from dataclasses import dataclass


@dataclass
class ArmPosterior:
    content_id: str
    alpha: float
    beta: float


def select_arm(arms: list[ArmPosterior], rng: random.Random | None = None) -> ArmPosterior:
    if not arms:
        raise ValueError("select_arm requires at least one candidate arm")
    rng = rng or random
    sampled = [(rng.betavariate(arm.alpha, arm.beta), arm) for arm in arms]
    _, best = max(sampled, key=lambda pair: pair[0])
    return best


def posterior_mean(arm: ArmPosterior) -> float:
    return arm.alpha / (arm.alpha + arm.beta)
