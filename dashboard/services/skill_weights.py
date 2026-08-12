"""
Skill Weight Store — manages per-skill weight multipliers for the
Recruiter Feedback Loop.

Weights are persisted in a single ``SkillWeightSnapshot`` DB row and
loaded/saved on every feedback event.  The design is intentionally simple
(no caching layer, no locking) — good enough for a hackathon demo.

Public API:
    get_skill_weight(skill_name)  → float (default 1.0)
    get_all_weights()             → dict[str, float]
    record_feedback(match_id, recruiter_id, feedback, skill_snapshot)
"""

import logging

from dashboard.models import MatchFeedback, SkillWeightSnapshot

logger = logging.getLogger("dashboard")

# Tuning knobs
WEIGHT_DELTA = 0.05
WEIGHT_MIN = 0.3
WEIGHT_MAX = 2.0


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_weights() -> dict:
    """Load the current weight dict from DB, or return {} if none exists."""
    snapshot = SkillWeightSnapshot.objects.first()
    if snapshot is None:
        return {}
    return snapshot.weights or {}


def _save_weights(weights: dict) -> None:
    """Upsert the singleton SkillWeightSnapshot row."""
    snapshot, _created = SkillWeightSnapshot.objects.get_or_create(pk=1)
    snapshot.weights = weights
    snapshot.save()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_skill_weight(skill_name: str) -> float:
    """Return the weight multiplier for *skill_name* (default 1.0)."""
    weights = _load_weights()
    return weights.get(skill_name.lower(), 1.0)


def get_all_weights() -> dict:
    """Return the full {skill: weight} mapping."""
    return _load_weights()


def record_feedback(
    match_id: str,
    recruiter_id: int,
    feedback: str,
    skill_snapshot: list,
) -> None:
    """
    Persist a feedback event and adjust skill weights.

    Parameters
    ----------
    match_id : str
        The candidate/resume identifier (e.g. ``"res_001"``).
    recruiter_id : int
        Plain integer for now (``0`` when auth is not wired).
    feedback : str
        ``"good_fit"`` or ``"not_a_fit"``.
    skill_snapshot : list[str]
        The matched-skill names at the time of feedback.
    """
    # 1. Persist the feedback row
    MatchFeedback.objects.create(
        match_id=str(match_id),
        recruiter_id=recruiter_id,
        feedback=feedback,
        skill_snapshot=skill_snapshot,
    )

    # 2. Adjust weights
    weights = _load_weights()
    delta = WEIGHT_DELTA if feedback == "good_fit" else -WEIGHT_DELTA

    for skill in skill_snapshot:
        key = skill.lower()
        current = weights.get(key, 1.0)
        new_weight = current + delta
        new_weight = max(WEIGHT_MIN, min(WEIGHT_MAX, new_weight))
        weights[key] = round(new_weight, 4)

    _save_weights(weights)
    logger.info(
        "Recorded %s feedback for match %s (%d skills adjusted)",
        feedback, match_id, len(skill_snapshot),
    )
