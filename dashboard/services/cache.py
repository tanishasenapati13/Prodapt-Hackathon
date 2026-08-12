"""
Caching helpers for match-score results.

Uses Django's built-in cache framework (LocMemCache for hackathon,
Redis as production upgrade path).

Cache keys are deterministic: match:<resume_id>:<jd_id>
Default TTL: 1 hour (3600s) — scores don't change unless the JD or
resume is re-uploaded, so this is safe.
"""

from django.core.cache import cache

DEFAULT_TIMEOUT = 3600  # 1 hour


def make_cache_key(resume_id: int, jd_id: int) -> str:
    """Generate a deterministic cache key for a resume-JD match."""
    return f"match:{resume_id}:{jd_id}"


def get_cached_match(resume_id: int, jd_id: int) -> dict | None:
    """
    Retrieve a cached match result.

    Returns None on cache miss (caller should fetch from FastAPI).
    """
    return cache.get(make_cache_key(resume_id, jd_id))


def set_cached_match(
    resume_id: int,
    jd_id: int,
    result: dict,
    timeout: int = DEFAULT_TIMEOUT,
) -> None:
    """
    Store a match result in cache.

    Args:
        resume_id: Resume identifier.
        jd_id: Job description identifier.
        result: The match-score result dict from FastAPI.
        timeout: Cache TTL in seconds (default: 1 hour).
    """
    cache.set(make_cache_key(resume_id, jd_id), result, timeout)


def invalidate_match(resume_id: int, jd_id: int) -> None:
    """
    Remove a cached match result (e.g., when resume is re-uploaded).
    """
    cache.delete(make_cache_key(resume_id, jd_id))


def invalidate_all_for_jd(jd_id: int, resume_ids: list[int]) -> None:
    """
    Invalidate cached results for all resumes against a specific JD.
    Useful when a JD is updated.
    """
    keys = [make_cache_key(rid, jd_id) for rid in resume_ids]
    cache.delete_many(keys)
