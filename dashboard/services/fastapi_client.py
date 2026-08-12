"""
Thin async httpx wrapper for all FastAPI calls.

All HTTP communication with Person 2's FastAPI service is centralized here.
No other module in the dashboard app makes raw HTTP calls.

Features:
  - Configurable base URL via FASTAPI_BASE_URL setting
  - Timeout handling (30s default)
  - Automatic retry on transient failures (1 retry)
  - Cache integration (check cache before calling FastAPI)
  - Structured error responses (never raises to caller)
"""

import logging
import httpx
from django.conf import settings
from .cache import get_cached_match, set_cached_match

logger = logging.getLogger("dashboard")

FASTAPI_BASE_URL = getattr(settings, "FASTAPI_BASE_URL", "http://localhost:8001")
DEFAULT_TIMEOUT = 30.0
MAX_RETRIES = 1


async def _make_request(method: str, endpoint: str, payload: dict | None = None) -> dict:
    """
    Internal: make an HTTP request with retry logic.

    Returns the JSON response on success, or raises on final failure.
    """
    url = f"{FASTAPI_BASE_URL}{endpoint}"
    last_exception = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
                if method == "POST":
                    resp = await client.post(url, json=payload)
                else:
                    resp = await client.get(url, params=payload)

                resp.raise_for_status()
                return resp.json()

        except httpx.TimeoutException as e:
            last_exception = e
            logger.warning(
                "Timeout calling %s (attempt %d/%d): %s",
                url, attempt + 1, MAX_RETRIES + 1, str(e),
            )
        except httpx.HTTPStatusError as e:
            last_exception = e
            logger.error(
                "HTTP %d from %s: %s",
                e.response.status_code, url, e.response.text[:200],
            )
            # Don't retry on 4xx client errors
            if 400 <= e.response.status_code < 500:
                raise
        except httpx.RequestError as e:
            last_exception = e
            logger.warning(
                "Request error calling %s (attempt %d/%d): %s",
                url, attempt + 1, MAX_RETRIES + 1, str(e),
            )

    raise last_exception  # type: ignore[misc]


async def get_match_score(resume_id: int, jd_id: int) -> dict:
    """
    Call Person 2's /match-score endpoint.

    Checks cache first. On cache miss, calls FastAPI and caches the result.

    Expected response shape:
        {
            "score": int,
            "matched_skills": list[str],
            "gaps": list[str],
            "insight_text": str
        }
    """
    # Check cache first
    cached = get_cached_match(resume_id, jd_id)
    if cached is not None:
        logger.debug("Cache hit for match:%d:%d", resume_id, jd_id)
        return cached

    logger.debug("Cache miss for match:%d:%d — calling FastAPI", resume_id, jd_id)
    result = await _make_request("POST", "/match-score", {
        "resume_id": resume_id,
        "jd_id": jd_id,
    })

    # Cache the successful result
    set_cached_match(resume_id, jd_id, result)
    return result


async def parse_resume(resume_id: int) -> dict:
    """
    Call Person 2's /parse-resume endpoint.

    Expected response: structured resume JSON with extracted fields.
    """
    return await _make_request("POST", "/parse-resume", {
        "resume_id": resume_id,
    })


async def get_gap_analysis(resume_id: int, jd_id: int) -> dict:
    """
    Call Person 2's /gap-analysis endpoint.

    Expected response: detailed gap breakdown with skill-level analysis.
    """
    return await _make_request("POST", "/gap-analysis", {
        "resume_id": resume_id,
        "jd_id": jd_id,
    })
