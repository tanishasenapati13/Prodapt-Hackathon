"""
Batch resume processing with bounded concurrency.

Uses asyncio.Semaphore to cap concurrent FastAPI/Groq calls, preventing
rate-limit exhaustion. Failed items are captured as error dicts — never
crash the whole batch.

Why Semaphore(5)?
  Groq's free-tier rate limit is ~30 RPM. With a 5-concurrent cap and
  ~2s per call, we stay well under the limit. Tune this value once
  Person 2 confirms the actual Groq rate limit.
"""

import asyncio
import logging
from .fastapi_client import get_match_score

logger = logging.getLogger("dashboard")

# Concurrency cap — tune based on Groq rate limits from Person 2
DEFAULT_CONCURRENCY = 5


async def process_resumes_async(
    resume_jd_pairs: list[tuple[int, int]],
    concurrency: int = DEFAULT_CONCURRENCY,
) -> list[dict]:
    """
    Process multiple resume-JD pairs concurrently with bounded parallelism.

    Args:
        resume_jd_pairs: List of (resume_id, jd_id) tuples to process.
        concurrency: Max concurrent FastAPI calls (default: 5).

    Returns:
        List of match results in the same order as input.
        Failed items have {"error": "..."} instead of crashing the batch.
    """
    if not resume_jd_pairs:
        return []

    semaphore = asyncio.Semaphore(concurrency)

    async def bounded_call(pair: tuple[int, int], index: int) -> dict:
        """Execute a single match-score call within the semaphore bound."""
        resume_id, jd_id = pair
        async with semaphore:
            logger.info(
                "Processing pair %d/%d: resume=%d, jd=%d",
                index + 1, len(resume_jd_pairs), resume_id, jd_id,
            )
            return await get_match_score(resume_id, jd_id)

    # Fire all tasks; semaphore ensures only `concurrency` run at once
    results = await asyncio.gather(
        *(bounded_call(pair, i) for i, pair in enumerate(resume_jd_pairs)),
        return_exceptions=True,
    )

    # Convert exceptions to graceful error entries
    processed = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            resume_id, jd_id = resume_jd_pairs[i]
            logger.error(
                "Failed to process resume=%d, jd=%d: %s",
                resume_id, jd_id, str(result),
            )
            processed.append({
                "resume_id": resume_id,
                "jd_id": jd_id,
                "score": 0,
                "matched_skills": [],
                "gaps": [],
                "insight_text": "",
                "error": str(result),
                "status": "error",
            })
        else:
            result["status"] = "completed"
            processed.append(result)

    completed = sum(1 for r in processed if r.get("status") == "completed")
    failed = sum(1 for r in processed if r.get("status") == "error")
    logger.info(
        "Batch processing complete: %d/%d succeeded, %d failed",
        completed, len(resume_jd_pairs), failed,
    )

    return processed
