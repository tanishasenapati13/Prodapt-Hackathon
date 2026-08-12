"""
Dashboard models.

Person 4 does not own any database tables — Person 3 manages the schema.
This file is intentionally minimal. If caching ever needs a DB-backed model
(unlikely for hackathon scope), it would go here. For now, we use Django's
built-in LocMemCache framework instead.
"""
from django.db import models  # noqa: F401 — kept for Django app discovery


# ---------------------------------------------------------------------------
# Feedback Loop models (Person 4 — additive, does not touch Person 3's schema)
# ---------------------------------------------------------------------------

class MatchFeedback(models.Model):
    """
    Stores recruiter feedback on a candidate match.

    Each row records whether a recruiter considered a match a "good_fit" or
    "not_a_fit", along with the skills that were matched at the time of
    feedback. This snapshot lets the skill-weight service know which skills
    to reward or penalize.
    """

    FEEDBACK_CHOICES = [
        ("good_fit", "Good Fit"),
        ("not_a_fit", "Not a Fit"),
    ]

    match_id = models.CharField(
        max_length=64,
        help_text="Resume/candidate ID (e.g. 'res_001'). Plain field — no FK for now.",
    )
    recruiter_id = models.IntegerField(
        default=0,
        help_text="Plain int — wire to auth.User FK when auth is set up.",
    )
    feedback = models.CharField(max_length=12, choices=FEEDBACK_CHOICES)
    skill_snapshot = models.JSONField(
        default=list,
        help_text="List of matched skill names at feedback time.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Feedback({self.match_id}, {self.feedback})"


class SkillWeightSnapshot(models.Model):
    """
    Single-row JSON store for skill weight multipliers.

    The skill-weight service reads/writes this row to persist weights
    between requests. Default weight for any unseen skill is 1.0.
    """

    weights = models.JSONField(
        default=dict,
        help_text='Mapping of {skill_name: weight_multiplier}. Default 1.0 for unseen.',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Skill Weight Snapshot"
        verbose_name_plural = "Skill Weight Snapshots"

    def __str__(self):
        return f"SkillWeights({len(self.weights)} skills)"
