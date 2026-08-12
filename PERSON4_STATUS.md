# Person 4 — Status Report

**Project:** Prodapt Hackathon — Group 27 — AI Resume Screening Assistant
**Owner:** Person 4
**Branch:** `person-4`
**Date:** 2026-08-12

---

## ✅ What's Built

### Dashboard App (`dashboard/`)
| Component | Status | Notes |
|---|---|---|
| `apps.py` | ✅ Complete | App configured as "Screening Dashboard" |
| `urls.py` | ✅ Complete | `/dashboard/` and `/dashboard/candidate/<id>/` |
| `views.py` | ✅ Complete | Thin views with error handling, delegates to services |
| `models.py` | ✅ Complete | Intentionally empty — dashboard is read-only |

### Services Layer (`dashboard/services/`)
| Component | Status | Notes |
|---|---|---|
| `mock_data.py` | ✅ Complete | 6 candidates, full gap analyses, error case included |
| `fastapi_client.py` | ✅ Complete | Async httpx wrapper, retry logic, cache integration |
| `batch_processor.py` | ✅ Complete | Semaphore(5) bounded concurrency, graceful error handling |
| `cache.py` | ✅ Complete | Django LocMemCache wrappers, invalidation helpers |

### Templates (`dashboard/templates/dashboard/`)
| Component | Status | Notes |
|---|---|---|
| `results.html` | ✅ Complete | Ranked table + Chart.js (bar + doughnut), dark theme |
| `candidate_detail.html` | ✅ Complete | Score ring, radar chart, gap severity chart, skill cards |

### Static Files (`dashboard/static/dashboard/`)
| Component | Status | Notes |
|---|---|---|
| `dashboard.css` | ✅ Complete | Premium dark theme, glassmorphism, animations |
| `charts.js` | ✅ Complete | 4 chart types (bar, doughnut, radar, horizontal bar) |

### Tests (`dashboard/tests/`)
| Test File | Tests | Status |
|---|---|---|
| `test_batch_processor.py` | 5 | ✅ All pass |
| `test_cache.py` | 7 | ✅ All pass |
| `test_views.py` | 16 | ✅ All pass |
| **Total** | **28** | **✅ All pass** |

### Postman Collection
| File | Status |
|---|---|
| `resume_screening.postman_collection.json` | ✅ Complete — covers `/match-score`, `/parse-resume`, `/gap-analysis` + edge cases |

### Deployment Config
| File | Status |
|---|---|
| `Procfile` | ✅ Complete |
| `render.yaml` | ✅ Complete — Django + FastAPI services + PostgreSQL |
| `.env.example` | ✅ Complete |
| `.gitignore` | ✅ Complete |

### Project Scaffold (temporary — for standalone testing)
| File | Status | Notes |
|---|---|---|
| `manage.py` | ✅ Complete | Points to `config.settings` |
| `config/settings.py` | ✅ Complete | LocMemCache, SQLite dev DB, FASTAPI_BASE_URL env var |
| `config/urls.py` | ✅ Complete | Includes `dashboard.urls` at `/dashboard/` |
| `config/wsgi.py` | ✅ Complete | Standard WSGI |
| `config/asgi.py` | ✅ Complete | ASGI for async view support |
| `requirements.txt` | ✅ Complete | django, httpx, python-dotenv |

---

## 🔶 Mock Data vs. Real Integration

| Data Source | Current State | Switch Required |
|---|---|---|
| Candidate list | **Mock** (`mock_data.py`) | Swap to Person 3's DB models (read-only queries) |
| Match scores | **Mock** | Swap to `fastapi_client.get_match_score()` calls |
| Gap analysis | **Mock** | Swap to `fastapi_client.get_gap_analysis()` calls |
| PII decryption | **Stubbed** (passthrough) | Wire Person 3's `security.crypto.decrypt_field()` |

**How to swap:** Set `USE_MOCK = False` in `views.py` and uncomment the real data paths. The mock data layer has identical function signatures to the real integration — zero template/CSS changes needed.

---

## ⚠️ Assumptions That Need Team Confirmation

1. **Upload redirect URL:** Assumed Person 1 redirects to `dashboard:results` after successful upload. **→ Confirm with Person 1.**

2. **FastAPI response shape:** Assumed `/match-score` returns:
   ```json
   {"score": int, "matched_skills": [...], "gaps": [...], "insight_text": str}
   ```
   **→ Confirm with Person 2.**

3. **Gap analysis response shape:** Assumed `/gap-analysis` returns per-skill proficiency/evidence and per-gap importance/recommendation. **→ Confirm with Person 2.**

4. **Semaphore cap:** Set to `5` concurrent calls — may need tuning based on Groq's actual rate limit. **→ Ask Person 2.**

5. **Person 3's decrypt utility:** `security.crypto.decrypt_field()` — not implemented here, stubbed with passthrough. **→ Get from Person 3 when ready.**

6. **Database access pattern:** Dashboard currently doesn't read from any DB tables directly. When Person 3's models are ready, we need to know: Django ORM models, raw SQL, or an API? **→ Confirm with Person 3.**

---

## 📁 Files Created / Modified

```
dashboard/
├── __init__.py
├── apps.py
├── urls.py
├── views.py
├── models.py
├── templates/dashboard/
│   ├── results.html
│   └── candidate_detail.html
├── static/dashboard/
│   ├── dashboard.css
│   └── charts.js
├── services/
│   ├── __init__.py
│   ├── mock_data.py
│   ├── fastapi_client.py
│   ├── batch_processor.py
│   ├── cache.py
│   ├── skill_weights.py    ← NEW (Feedback Loop)
│   └── reranker.py         ← NEW (Feedback Loop)
├── tests/
│   ├── __init__.py
│   ├── test_batch_processor.py
│   ├── test_cache.py
│   ├── test_views.py
│   ├── test_skill_weights.py   ← NEW (Feedback Loop)
│   ├── test_reranker.py        ← NEW (Feedback Loop)
│   └── test_feedback_view.py   ← NEW (Feedback Loop)
├── management/commands/
│   └── seed_demo_feedback.py   ← NEW (Feedback Loop)
└── postman/
    └── resume_screening.postman_collection.json

config/
├── __init__.py
├── settings.py    ← 'dashboard' in INSTALLED_APPS
├── urls.py        ← path('dashboard/', include('dashboard.urls'))
├── wsgi.py
└── asgi.py

requirements.txt
manage.py
Procfile
render.yaml
.env.example
.gitignore
```

Root-level shared files touched:
- `config/urls.py` — one line: `path('dashboard/', include('dashboard.urls'))`
- `config/settings.py` — one line: `'dashboard'` in `INSTALLED_APPS`

---

## 🔄 Feedback Loop Feature

**Branch:** `feedback-loop`
**Status:** ✅ Complete — 50 tests passing (28 existing + 22 new)

### What It Does

Recruiters can mark a candidate match as "👍 Good Fit" or "👎 Not a Fit" directly from the results page. Each feedback event adjusts per-skill weight multipliers, which are then used to re-rank candidate scores on future page loads — no model retraining needed.

### How It Works

1. **Feedback buttons** on each candidate row → POST to `/dashboard/feedback/` via `fetch()` (no page reload)
2. **Skill weights** are adjusted: `good_fit` → `+0.05` per matched skill (capped at `2.0`), `not_a_fit` → `-0.05` (floored at `0.3`)
3. **Re-ranker** computes `adjusted_score = original_score × avg(skill_weights)`, clamped to `[0, 100]`
4. Results page shows both original and adjusted scores when they differ (e.g., `82 → 85`)

### New Files

| File | Purpose |
|---|---|
| `dashboard/models.py` | Added `MatchFeedback` + `SkillWeightSnapshot` models |
| `dashboard/services/skill_weights.py` | Skill weight CRUD + feedback recording |
| `dashboard/services/reranker.py` | Score adjustment + re-sorting |
| `dashboard/tests/test_skill_weights.py` | 8 tests for weight logic |
| `dashboard/tests/test_reranker.py` | 8 tests for reranking |
| `dashboard/tests/test_feedback_view.py` | 6 tests for the POST endpoint |
| `dashboard/management/commands/seed_demo_feedback.py` | Demo data seeder |

### Modified Files (append-only to minimize merge conflicts)

| File | Change |
|---|---|
| `dashboard/views.py` | Added `submit_feedback` view + `rerank_matches()` call |
| `dashboard/urls.py` | Added `path("feedback/", ...)` |
| `dashboard/templates/dashboard/results.html` | Feedback buttons + adjusted score badge + JS |
| `dashboard/static/dashboard/dashboard.css` | Feedback button + badge styles |

### Demo Command

```bash
python manage.py seed_demo_feedback         # seed fake feedback
python manage.py seed_demo_feedback --reset  # clear + re-seed
```

### ⚠️ Design Decisions (Flagged)

1. **Delta values:** `+/-0.05` per feedback event — tune as needed
2. **Weight bounds:** Min `0.3`, Max `2.0`
3. **Recruiter ID:** Plain `IntegerField(default=0)` — wire to `auth.User` FK when auth is set up
4. **CSRF:** `@csrf_exempt` on the feedback endpoint (acceptable for hackathon demo; add CSRF token handling for production)

