import asyncio
import hashlib
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
from loguru import logger

from backend.config import settings


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_iso(dt: datetime | None) -> str | None:
    if not dt:
        return None
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_dt(value: Any) -> datetime | None:
    if not value:
        return None

    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)

    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value, tz=timezone.utc)
        except Exception:
            return None

    raw = str(value).strip()
    if not raw:
        return None

    raw = raw.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(raw)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        pass

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d %H:%M:%S"):
        try:
            parsed = datetime.strptime(raw, fmt)
            return parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    return None


class DeepfakeNewsService:
    BASE_URL = "https://newsdata.io/api/1/news"

    GLOBAL_QUERIES = [
        "deepfake",
        "deepfake detection",
        "AI fake video",
        "synthetic media crime",
        "face swap fraud",
        "deepfake arrest",
        "AI generated misinformation",
        "deepfake law",
    ]

    INDIA_QUERIES = [
        "deepfake India",
        "deepfake Bollywood",
        "AI crime India",
        "cyber fraud India",
        "deepfake arrest India",
    ]

    PLACEHOLDER_IMAGE_HINTS = (
        "placeholder",
        "default",
        "no-image",
        "noimage",
        "blank",
        "logo",
    )

    BREAKING_PHRASES = (
        "deepfake arrest",
        "deepfake law passed",
        "deepfake victim",
    )

    CATEGORY_KEYWORDS = {
        "india": (
            "india",
            "mumbai",
            "delhi",
            "bollywood",
            "bengaluru",
            "bangalore",
            "kolkata",
            "hyderabad",
            "chennai",
        ),
        "political": (
            "politician",
            "election",
            "government",
            "pm",
            "president",
            "parliament",
            "minister",
            "campaign",
        ),
        "celebrity": (
            "actor",
            "celebrity",
            "viral",
            "social media",
            "influencer",
            "bollywood",
            "star",
        ),
        "crime": (
            "arrest",
            "arrested",
            "police",
            "cybercrime",
            "cyber crime",
            "fraud",
            "victim",
            "scam",
            "crime",
        ),
        "legal": (
            "law",
            "regulation",
            "ban",
            "court",
            "legal",
            "bill",
            "judge",
            "act",
        ),
        "technology": (
            "detection",
            "ai",
            "technology",
            "research",
            "tool",
            "model",
            "synthetic media",
        ),
    }

    CATEGORY_LABELS = {
        "india": "India",
        "political": "Political",
        "celebrity": "Celebrity",
        "crime": "Crime",
        "legal": "Legal",
        "technology": "AI Deepfakes",
    }

    CATEGORY_PRIORITY = ["india", "political", "celebrity", "crime", "legal", "technology"]

    def __init__(self) -> None:
        self._articles: list[dict[str, Any]] = []
        self._last_updated: datetime | None = None
        self._last_error: str | None = None
        self._last_stats: dict[str, Any] = {}

        self._refresh_lock = asyncio.Lock()
        self._stop_event = asyncio.Event()
        self._background_task: asyncio.Task | None = None

        self.refresh_interval_seconds = int(os.getenv("NEWS_REFRESH_INTERVAL_SECONDS", "21600"))
        self.max_articles = int(os.getenv("NEWS_MAX_ARTICLES", "80"))

        project_root = Path(__file__).resolve().parents[3]
        self._env_paths = [
            project_root / ".env",
            project_root / "backend" / ".env",
        ]

    async def start(self) -> None:
        if self._background_task and not self._background_task.done():
            return

        self._stop_event.clear()
        self._background_task = asyncio.create_task(self._refresh_loop(), name="deepfake-news-refresh")

    async def stop(self) -> None:
        self._stop_event.set()
        if not self._background_task:
            return

        self._background_task.cancel()
        try:
            await self._background_task
        except asyncio.CancelledError:
            pass
        finally:
            self._background_task = None

    def get_news(
        self,
        tab: str = "all",
        search: str = "",
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        tab_key = (tab or "all").strip().lower()
        search_text = (search or "").strip().lower()

        items = list(self._articles)
        if tab_key and tab_key != "all":
            items = [item for item in items if self._matches_tab(item, tab_key)]

        if search_text:
            items = [
                item
                for item in items
                if search_text in (item.get("title") or "").lower()
                or search_text in (item.get("summary") or "").lower()
                or search_text in (item.get("source_name") or "").lower()
            ]

        total = len(items)
        paged = items[offset : offset + limit]

        breaking = next((item for item in items if item.get("is_breaking")), None)
        status = self.get_status()

        return {
            "items": paged,
            "total": total,
            "limit": limit,
            "offset": offset,
            "last_updated": _to_iso(self._last_updated),
            "live": status["live"],
            "stale": status["stale"],
            "stale_reason": status.get("stale_reason"),
            "breaking": breaking,
        }

    def get_status(self) -> dict[str, Any]:
        now = _utc_now()
        stale = True
        stale_reason = None

        if self._last_updated:
            stale = now - self._last_updated > timedelta(seconds=self.refresh_interval_seconds + 600)
            if stale:
                stale_reason = "last_refresh_too_old"
        else:
            stale_reason = "not_fetched_yet"

        if self._last_error and stale:
            stale_reason = "provider_error"

        return {
            "live": not stale and not self._last_error,
            "stale": stale,
            "stale_reason": stale_reason,
            "last_updated": _to_iso(self._last_updated),
            "last_error": self._last_error,
            "article_count": len(self._articles),
            "refresh_interval_seconds": self.refresh_interval_seconds,
            "last_stats": self._last_stats,
        }

    async def refresh_now(self, trigger: str = "manual") -> dict[str, Any]:
        api_key = self._resolve_api_key()
        if not api_key:
            self._last_error = "NEWS_API_KEY is not configured"
            return {
                "ok": False,
                "status": "error",
                "detail": self._last_error,
                "trigger": trigger,
            }

        if self._refresh_lock.locked() and trigger == "manual":
            return {
                "ok": True,
                "status": "busy",
                "detail": "refresh_already_running",
                "trigger": trigger,
            }

        async with self._refresh_lock:
            started_at = _utc_now()
            fetched_at_iso = _to_iso(started_at)
            raw_articles: list[dict[str, Any]] = []
            query_errors: list[str] = []

            try:
                async with httpx.AsyncClient(
                    follow_redirects=True,
                    timeout=10.0,
                    headers={"User-Agent": "DeepScan-NewsFetcher/1.0"},
                ) as client:
                    raw_articles, query_errors = await self._fetch_all_queries(client, api_key)
                    cleaned = await self._normalize_and_filter(client, raw_articles, started_at, fetched_at_iso)
            except Exception as exc:
                self._last_error = f"news_refresh_failed: {exc}"
                logger.warning(self._last_error)
                return {
                    "ok": False,
                    "status": "error",
                    "detail": self._last_error,
                    "trigger": trigger,
                }

            self._articles = cleaned
            self._last_updated = started_at
            self._last_error = None if cleaned else "no_valid_articles_after_filtering"
            self._last_stats = {
                "raw_count": len(raw_articles),
                "stored_count": len(cleaned),
                "query_errors": query_errors,
                "trigger": trigger,
            }

            logger.info(
                "[NEWS] refresh complete | trigger={} raw={} stored={} errors={}",
                trigger,
                len(raw_articles),
                len(cleaned),
                len(query_errors),
            )

            return {
                "ok": True,
                "status": "success",
                "trigger": trigger,
                "fetched": len(raw_articles),
                "stored": len(cleaned),
                "query_errors": query_errors,
                "last_updated": _to_iso(self._last_updated),
            }

    async def _refresh_loop(self) -> None:
        await self.refresh_now(trigger="startup")

        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self.refresh_interval_seconds)
            except asyncio.TimeoutError:
                await self.refresh_now(trigger="scheduled")
            except Exception as exc:
                logger.warning(f"[NEWS] refresh loop warning: {exc}")

    async def _fetch_all_queries(self, client: httpx.AsyncClient, api_key: str) -> tuple[list[dict[str, Any]], list[str]]:
        query_plan: list[tuple[str, str]] = []
        for query in self.GLOBAL_QUERIES:
            query_plan.append((query, "in,us,gb"))
        for query in self.INDIA_QUERIES:
            query_plan.append((query, "in"))

        all_articles: list[dict[str, Any]] = []
        errors: list[str] = []

        # Run sequentially with a small pause to reduce NewsData free-tier throttling.
        for index, (query, country) in enumerate(query_plan):
            query_result, articles, error = await self._fetch_single_query(
                client,
                api_key=api_key,
                query=query,
                country=country,
            )
            if error:
                errors.append(f"{query_result}: {error}")
            all_articles.extend(articles)

            if index < len(query_plan) - 1:
                await asyncio.sleep(0.35)

        return all_articles, errors

    async def _fetch_single_query(
        self,
        client: httpx.AsyncClient,
        api_key: str,
        query: str,
        country: str,
    ) -> tuple[str, list[dict[str, Any]], str | None]:
        params = {
            "apikey": api_key,
            "q": query,
            "language": "en",
            "category": "technology,politics,crime",
            "country": country,
            "size": 10,
        }

        try:
            for attempt in range(2):
                response = await client.get(self.BASE_URL, params=params)
                if response.status_code == 429 and attempt == 0:
                    await asyncio.sleep(1.2)
                    continue

                response.raise_for_status()
                payload = response.json()
                results = payload.get("results") or payload.get("articles") or []
                if not isinstance(results, list):
                    return query, [], "invalid_results_payload"
                return query, results, None

            return query, [], "rate_limited"
        except Exception as exc:
            return query, [], str(exc)

    def _resolve_api_key(self) -> str:
        candidates = [
            settings.NEWS_API_KEY,
            os.getenv("NEWS_API_KEY"),
            os.getenv("NEWSDATA_API_KEY"),
        ]

        for path in self._env_paths:
            key = self._read_key_from_env_file(path)
            if key:
                candidates.append(key)

        for candidate in candidates:
            value = (candidate or "").strip()
            if value and not self._is_placeholder_key(value):
                return value

        return ""

    def _read_key_from_env_file(self, env_path: Path) -> str:
        try:
            if not env_path.exists():
                return ""
            for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                raw = line.strip()
                if raw.startswith("NEWS_API_KEY=") or raw.startswith("NEWSDATA_API_KEY="):
                    return raw.split("=", 1)[1].strip().strip('"').strip("'")
        except Exception:
            return ""
        return ""

    def _is_placeholder_key(self, value: str) -> bool:
        upper = value.upper()
        if value in {"...", "YOUR_KEY", "YOUR_API_KEY"}:
            return True
        if "CHANGE" in upper or "PLACEHOLDER" in upper:
            return True
        return False

    async def _normalize_and_filter(
        self,
        client: httpx.AsyncClient,
        raw_articles: list[dict[str, Any]],
        now: datetime,
        fetched_at_iso: str,
    ) -> list[dict[str, Any]]:
        max_age = now - timedelta(days=30)
        seen_urls: set[str] = set()
        seen_source_title: set[tuple[str, str]] = set()
        url_reachability_cache: dict[str, bool] = {}
        candidates: list[dict[str, Any]] = []

        for raw in raw_articles:
            title = (raw.get("title") or "").strip()
            summary = self._compact_summary(raw.get("description") or raw.get("content") or "")
            source_url = (raw.get("link") or raw.get("url") or "").strip()
            thumbnail_url = (raw.get("image_url") or raw.get("image") or raw.get("urlToImage") or "").strip()
            source_name = self._extract_source_name(raw)
            published_at = _parse_dt(raw.get("pubDate") or raw.get("publishedAt") or raw.get("pubDateTZ"))

            if not title or not source_url or not source_name or not published_at:
                continue

            if published_at < max_age:
                continue

            if not self._is_deepfake_specific(title, summary):
                continue

            if not self._is_valid_url(source_url):
                continue

            if not self._is_valid_url(thumbnail_url):
                continue

            thumb_lower = thumbnail_url.lower()
            if any(hint in thumb_lower for hint in self.PLACEHOLDER_IMAGE_HINTS):
                continue

            normalized_url = self._normalize_url(source_url)
            source_title_key = (source_name.lower(), self._normalize_title(title))
            if normalized_url in seen_urls or source_title_key in seen_source_title:
                continue

            categories = self._detect_categories(title, summary)
            if not categories:
                categories = ["technology"]

            category_tag = self.CATEGORY_LABELS.get(self._pick_primary_category(categories), "AI Deepfakes")

            combined_text = f"{title} {summary}".lower()
            is_breaking = (now - published_at) <= timedelta(hours=2) and any(
                phrase in combined_text for phrase in self.BREAKING_PHRASES
            )

            article_id = raw.get("article_id") or self._build_article_id(
                normalized_url,
                title,
                published_at,
            )

            candidates.append(
                {
                    "article_id": article_id,
                    "title": title,
                    "summary": summary,
                    "source_name": source_name,
                    "source_url": normalized_url,
                    "thumbnail_url": thumbnail_url,
                    "published_at": _to_iso(published_at),
                    "fetched_at": fetched_at_iso,
                    "category_tag": category_tag,
                    "category_flags": categories,
                    "is_breaking": is_breaking,
                }
            )

            seen_urls.add(normalized_url)
            seen_source_title.add(source_title_key)

        validated: list[dict[str, Any]] = []
        sem = asyncio.Semaphore(8)

        async def _validate(candidate: dict[str, Any]) -> dict[str, Any] | None:
            url = candidate["source_url"]
            async with sem:
                if url in url_reachability_cache:
                    reachable = url_reachability_cache[url]
                else:
                    reachable = await self._is_reachable(client, url)
                    url_reachability_cache[url] = reachable

            if not reachable:
                return None
            return candidate

        checks = await asyncio.gather(*[_validate(c) for c in candidates])
        for item in checks:
            if item:
                validated.append(item)

        validated.sort(key=lambda row: row.get("published_at") or "", reverse=True)
        return validated[: self.max_articles]

    def _extract_source_name(self, raw: dict[str, Any]) -> str:
        source = raw.get("source_id") or raw.get("source_name") or raw.get("source")
        if isinstance(source, dict):
            return (source.get("name") or "Unknown Source").strip() or "Unknown Source"
        if isinstance(source, str):
            return source.strip() or "Unknown Source"
        return "Unknown Source"

    def _is_deepfake_specific(self, title: str, summary: str) -> bool:
        haystack = f"{title} {summary}".lower()
        if "deepfake" in haystack:
            return True
        return "face swap" in haystack and "fraud" in haystack

    def _detect_categories(self, title: str, summary: str) -> list[str]:
        text = f"{title} {summary}".lower()
        matched: list[str] = []

        for category in self.CATEGORY_PRIORITY:
            words = self.CATEGORY_KEYWORDS.get(category, ())
            if any(word in text for word in words):
                matched.append(category)

        return matched

    def _pick_primary_category(self, categories: list[str]) -> str:
        for category in self.CATEGORY_PRIORITY:
            if category in categories:
                return category
        return "technology"

    def _matches_tab(self, item: dict[str, Any], tab: str) -> bool:
        flags = set(item.get("category_flags") or [])

        if tab in ("all", ""):
            return True
        if tab in ("ai", "ai-deepfakes", "tech"):
            return "technology" in flags
        if tab == "political":
            return "political" in flags
        if tab == "celebrity":
            return "celebrity" in flags
        if tab in ("legal-crime", "legal", "crime"):
            return "legal" in flags or "crime" in flags
        if tab == "india":
            return "india" in flags
        return True

    def _is_valid_url(self, value: str) -> bool:
        if not value:
            return False
        parsed = urlparse(value)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)

    def _normalize_url(self, value: str) -> str:
        parsed = urlparse(value)
        path = parsed.path.rstrip("/")
        query = f"?{parsed.query}" if parsed.query else ""
        return f"{parsed.scheme}://{parsed.netloc}{path}{query}" if path else f"{parsed.scheme}://{parsed.netloc}{query}"

    def _normalize_title(self, value: str) -> str:
        lowered = value.lower().strip()
        lowered = re.sub(r"\s+", " ", lowered)
        lowered = re.sub(r"[^a-z0-9 ]", "", lowered)
        return lowered

    def _compact_summary(self, value: str) -> str:
        cleaned = re.sub(r"\s+", " ", value).strip()
        if not cleaned:
            return "Summary unavailable."
        if len(cleaned) > 220:
            return cleaned[:217].rstrip() + "..."
        return cleaned

    async def _is_reachable(self, client: httpx.AsyncClient, url: str) -> bool:
        try:
            head = await client.head(url, timeout=6.0)
            if head.status_code < 400:
                return True
            if head.status_code in (401, 403, 405):
                return True
        except Exception:
            pass

        try:
            get_resp = await client.get(url, timeout=8.0)
            return get_resp.status_code < 400
        except Exception:
            return False

    def _build_article_id(self, source_url: str, title: str, published_at: datetime) -> str:
        seed = f"{source_url}|{title}|{published_at.isoformat()}"
        return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:24]


deepfake_news_service = DeepfakeNewsService()
