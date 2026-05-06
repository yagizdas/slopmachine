from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timezone

from .models import EntropyBundle, EntropySource
from .util import clamp_int, compact_whitespace


WIKIPEDIA_RANDOM_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/random/summary"

FALLBACK_FRAGMENTS = [
    "lavender calibration notes found beside a silent observatory instrument",
    "a municipal form that asks the moon to explain its recurring absences",
    "obsolete railway switches catalogued as if they were endangered flowers",
    "a classroom graph where every triangle insists it is a weather event",
    "the maintenance manual for a fountain that predicts minor inconveniences",
    "a museum placard describing a spoon-shaped comet with legal opinions",
]


def fetch_entropy_bundle(source_count: int = 3) -> EntropyBundle:
    count = clamp_int(source_count, default=3, minimum=1, maximum=6)
    sources: list[EntropySource] = []

    for _ in range(count):
        try:
            sources.append(fetch_wikipedia_summary())
        except RuntimeError:
            continue

    if not sources:
        return {
            "sources": [],
            "fragments": FALLBACK_FRAGMENTS,
            "generated_at": now_iso(),
        }

    return {
        "sources": sources,
        "fragments": [
            compact_whitespace(source["extract"])[:700]
            for source in sources
        ],
        "generated_at": now_iso(),
    }


def fetch_wikipedia_summary() -> EntropySource:
    request = urllib.request.Request(
        WIKIPEDIA_RANDOM_SUMMARY_URL,
        headers={
            "Accept": "application/json",
            "User-Agent": "slop-mcp/0.1.0 random semantic project brief generator",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Wikipedia entropy request failed: {error}") from error

    title = str(payload.get("title") or "").strip()
    extract = str(payload.get("extract") or "").strip()
    url = (
        payload.get("content_urls", {})
        .get("desktop", {})
        .get("page", "")
    )

    if not title or not extract or not url:
        raise RuntimeError("Wikipedia entropy response was missing title, extract, or URL")

    return {
        "title": title,
        "extract": extract,
        "url": str(url),
    }


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

if __name__ == "__main__":
    bundle = fetch_entropy_bundle()
    print(json.dumps(bundle, indent=2))