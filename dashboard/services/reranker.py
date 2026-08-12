"""
Re-ranker — adjusts candidate match scores based on accumulated
recruiter feedback weights.

The re-ranker is a pure post-processing step: it takes a list of match
dicts (same shape as ``mock_data.get_mock_candidates()`` returns), computes
an ``adjusted_score`` for each based on the current skill weights, and
returns the list sorted by ``adjusted_score`` descending.

Public API:
    rerank_matches(matches) → list[dict]  (with original_score + adjusted_score)
"""

from dashboard.services.skill_weights import get_skill_weight


def rerank_matches(matches: list) -> list:
    """
    Adjust scores and re-sort *matches* using accumulated skill weights.

    For each match dict the function:
    1. Copies ``score`` into ``original_score`` (if not already present).
    2. Computes ``adjusted_score = original_score × avg(weight(skill)
       for skill in matched_skills)``, clamped to ``[0, 100]``.
    3. Overwrites ``score`` with ``adjusted_score`` so the template
       continues to use ``candidate.score`` for display.

    Returns the list sorted by ``adjusted_score`` descending.
    """
    for match in matches:
        # Preserve the original score on first pass
        if "original_score" not in match:
            match["original_score"] = match.get("score", 0)

        original = match["original_score"]
        skills = match.get("matched_skills", [])

        if skills:
            # Compute average weight multiplier across matched skills
            # Handle both plain strings and dict-style skills
            skill_names = []
            for s in skills:
                if isinstance(s, dict):
                    skill_names.append(s.get("skill", ""))
                else:
                    skill_names.append(str(s))

            total_weight = sum(get_skill_weight(name) for name in skill_names)
            avg_weight = total_weight / len(skill_names)
        else:
            avg_weight = 1.0

        adjusted = round(original * avg_weight, 2)
        adjusted = max(0, min(100, adjusted))

        match["adjusted_score"] = adjusted
        match["score"] = int(adjusted)

    # Sort by adjusted score descending
    matches.sort(key=lambda m: m["adjusted_score"], reverse=True)
    return matches
