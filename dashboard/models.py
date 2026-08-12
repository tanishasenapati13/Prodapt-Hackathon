"""
Dashboard models.

Person 4 does not own any database tables — Person 3 manages the schema.
This file is intentionally minimal. If caching ever needs a DB-backed model
(unlikely for hackathon scope), it would go here. For now, we use Django's
built-in LocMemCache framework instead.
"""
from django.db import models  # noqa: F401 — kept for Django app discovery
