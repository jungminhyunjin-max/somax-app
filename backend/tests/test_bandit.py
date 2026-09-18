import random

from app.bandit import ArmPosterior, posterior_mean, select_arm


def test_select_arm_requires_candidates():
    try:
        select_arm([])
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for empty arm list")


def test_select_arm_converges_to_better_arm():
    rng = random.Random(42)
    good = ArmPosterior(content_id="good", alpha=80, beta=20)  # ~0.8 engagement
    bad = ArmPosterior(content_id="bad", alpha=20, beta=80)    # ~0.2 engagement

    counts = {"good": 0, "bad": 0}
    for _ in range(2000):
        chosen = select_arm([good, bad], rng=rng)
        counts[chosen.content_id] += 1

    assert counts["good"] > counts["bad"]
    assert counts["good"] / sum(counts.values()) > 0.85


def test_posterior_mean():
    arm = ArmPosterior(content_id="x", alpha=3, beta=1)
    assert posterior_mean(arm) == 0.75


def test_new_arms_get_explored_roughly_evenly():
    rng = random.Random(7)
    a = ArmPosterior(content_id="a", alpha=1, beta=1)
    b = ArmPosterior(content_id="b", alpha=1, beta=1)

    counts = {"a": 0, "b": 0}
    for _ in range(500):
        chosen = select_arm([a, b], rng=rng)
        counts[chosen.content_id] += 1

    ratio = counts["a"] / sum(counts.values())
    assert 0.35 < ratio < 0.65
