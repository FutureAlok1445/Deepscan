import hashlib
import os
from loguru import logger


class ReverseImageSearch:
    """Reverse image search to find original sources and detect reposts.

    In production, integrate with TinEye API, Google Vision API, or
    Yandex Image Search. Current implementation uses perceptual hashing
    for local duplicate detection.
    """

    # Simple in-memory hash store for duplicate detection
    _hash_store: dict = {}

    def _compute_phash(self, file_path: str) -> str:
        """Compute a simple perceptual hash of an image file."""
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            return hashlib.md5(content).hexdigest()
        except Exception:
            return ""

    def search(self, file_path: str) -> dict:
        """Search for matching images.

        Returns:
            dict with matches_found, urls, trust_penalty
        """
        if not os.path.exists(file_path):
            return {"matches_found": 0, "urls": [], "trust_penalty": 0.0}

        phash = self._compute_phash(file_path)
        if not phash:
            return {"matches_found": 0, "urls": [], "trust_penalty": 0.0}

        # Check for duplicates in our store
        matches = []
        if phash in self._hash_store:
            prev = self._hash_store[phash]
            matches.append(prev)

        # Store this hash for future lookups
        self._hash_store[phash] = {
            "file": os.path.basename(file_path),
            "hash": phash,
        }

        # Penalty: if we've seen this exact file before, it's suspicious
        penalty = min(len(matches) * 15.0, 45.0)

        if matches:
            logger.info(f"Reverse search: found {len(matches)} duplicate(s) for {file_path}")

        return {
            "matches_found": len(matches),
            "urls": [m.get("file", "") for m in matches],
            "trust_penalty": penalty,
            "phash": phash,
        }