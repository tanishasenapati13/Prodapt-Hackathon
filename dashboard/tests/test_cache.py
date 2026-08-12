"""
Tests for dashboard.services.cache.

Validates:
  - Cache key generation is deterministic
  - get_cached_match returns None on miss
  - set_cached_match stores and get_cached_match retrieves
  - invalidate_match removes the entry
  - invalidate_all_for_jd removes multiple entries
"""

from django.test import TestCase, override_settings
from dashboard.services.cache import (
    make_cache_key,
    get_cached_match,
    set_cached_match,
    invalidate_match,
    invalidate_all_for_jd,
)


# Use LocMemCache for tests (isolated per test)
@override_settings(CACHES={
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-cache",
    }
})
class CacheTests(TestCase):
    """Tests for caching helpers."""

    def test_make_cache_key_deterministic(self):
        """Same inputs should always produce the same key."""
        key1 = make_cache_key(1, 10)
        key2 = make_cache_key(1, 10)
        self.assertEqual(key1, key2)
        self.assertEqual(key1, "match:1:10")

    def test_make_cache_key_different_inputs(self):
        """Different inputs should produce different keys."""
        key1 = make_cache_key(1, 10)
        key2 = make_cache_key(2, 10)
        key3 = make_cache_key(1, 20)
        self.assertNotEqual(key1, key2)
        self.assertNotEqual(key1, key3)

    def test_cache_miss_returns_none(self):
        """Getting a non-existent key should return None."""
        result = get_cached_match(999, 999)
        self.assertIsNone(result)

    def test_set_and_get(self):
        """Stored data should be retrievable."""
        data = {"score": 85, "matched_skills": ["Python"]}
        set_cached_match(42, 7, data)
        result = get_cached_match(42, 7)
        self.assertEqual(result, data)
        self.assertEqual(result["score"], 85)

    def test_invalidate_match(self):
        """Invalidating should remove the entry."""
        data = {"score": 90}
        set_cached_match(1, 1, data)

        # Confirm it's there
        self.assertIsNotNone(get_cached_match(1, 1))

        # Invalidate
        invalidate_match(1, 1)
        self.assertIsNone(get_cached_match(1, 1))

    def test_invalidate_all_for_jd(self):
        """Invalidating all for a JD should remove all matching entries."""
        jd_id = 10
        for rid in [1, 2, 3]:
            set_cached_match(rid, jd_id, {"score": rid * 10})

        # All should exist
        for rid in [1, 2, 3]:
            self.assertIsNotNone(get_cached_match(rid, jd_id))

        # Invalidate all
        invalidate_all_for_jd(jd_id, [1, 2, 3])

        # All should be gone
        for rid in [1, 2, 3]:
            self.assertIsNone(get_cached_match(rid, jd_id))

    def test_cache_does_not_cross_keys(self):
        """Setting one key should not affect another."""
        set_cached_match(1, 10, {"score": 80})
        set_cached_match(2, 10, {"score": 90})

        # Invalidate one
        invalidate_match(1, 10)

        # Other should still exist
        self.assertIsNone(get_cached_match(1, 10))
        self.assertIsNotNone(get_cached_match(2, 10))
        self.assertEqual(get_cached_match(2, 10)["score"], 90)
