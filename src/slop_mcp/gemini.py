from __future__ import annotations

import json
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Literal, cast

from .models import EntropyBundle, PROJECT_FORMATS, ProjectFormat, SlopBrief
from .schema import SLOP_BRIEF_RESPONSE_SCHEMA
from .util import clamp_int, slugify


GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash-lite"


def generate_brief_with_gemini(
    entropy: EntropyBundle,
    *,
    project_format: ProjectFormat | Literal["random"] = "random",
    chaos: int = 7,
    user_theme: str | None = None,
) -> SlopBrief:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is required to generate Slop Machine briefs")

    chosen_format = choose_format(project_format)
    chosen_chaos = clamp_int(chaos, default=7, minimum=1, maximum=10)
    model = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
    url = build_gemini_url(model=model, api_key=api_key)

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": build_prompt(
                            entropy,
                            project_format=chosen_format,
                            chaos=chosen_chaos,
                            user_theme=user_theme,
                        )
                    }
                ],
            }
        ],
        "generationConfig": {
            "temperature": min(1.8, 0.55 + chosen_chaos / 10),
            "topP": 0.95,
            "responseMimeType": "application/json",
            "responseSchema": SLOP_BRIEF_RESPONSE_SCHEMA,
        },
    }

    response = post_json(url, payload)
    text = extract_gemini_text(response)
    brief = cast(SlopBrief, json.loads(text))
    return normalize_brief(brief, project_format=chosen_format, chaos=chosen_chaos)


def choose_format(project_format: ProjectFormat | Literal["random"]) -> ProjectFormat:
    if project_format != "random":
        return project_format

    index = secrets.randbelow(len(PROJECT_FORMATS))
    return PROJECT_FORMATS[index]


def build_gemini_url(*, model: str, api_key: str) -> str:
    escaped_model = urllib.parse.quote(model, safe="")
    escaped_key = urllib.parse.quote(api_key, safe="")
    return f"{GEMINI_API_BASE}/models/{escaped_model}:generateContent?key={escaped_key}"


def post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return cast(dict[str, Any], json.loads(response.read().decode("utf-8")))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini request failed with HTTP {error.code}: {body}") from error
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Gemini request failed: {error}") from error


def extract_gemini_text(response: dict[str, Any]) -> str:
    candidates = response.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise RuntimeError("Gemini returned no candidates")

    parts = (
        candidates[0]
        .get("content", {})
        .get("parts", [])
    )
    if not isinstance(parts, list):
        raise RuntimeError("Gemini response had no content parts")

    text = "".join(str(part.get("text", "")) for part in parts if isinstance(part, dict)).strip()
    if not text:
        raise RuntimeError("Gemini returned an empty structured response")

    return text


def build_prompt(
    entropy: EntropyBundle,
    *,
    project_format: ProjectFormat,
    chaos: int,
    user_theme: str | None,
) -> str:
    sources = format_sources(entropy)
    theme_line = (
        f"The user also requested this theme or direction: {user_theme}"
        if user_theme
        else "The user did not provide an extra theme."
    )

    return f"""You are Slop Machine, a semantic chaos distiller for coding agents.

Your job:
- Transform random source text into one strange but buildable software project.
- Use real details from the sources, but remix them hard.
- Avoid generic startup ideas, productivity dashboards, and bland portfolio pages.
- The result must be feasible for Codex or Claude Code to build in one focused pass.
- Make it weird at chaos level {chaos}/10 while still coherent.
- Use project format: {project_format}.
- {theme_line}

Return only JSON matching the schema.

Important output rules:
- output_dir must be "slop-output/<slug>".
- suggested_stack should be small and practical.
- For websites, games, art, tools, dashboards, apps, or simulations, prefer self-contained HTML/CSS/JS unless a different stack is clearly better.
- For CLI format, prefer a no-dependency Python CLI.
- build_constraints must include "Use no external network assets." and "Keep the first screen as the actual experience." when the format is visual.
- done_criteria must include a local run/open criterion and a README criterion.
- source_influences must mention concrete source details, not abstract vibes.

Random semantic source material:

{sources}
"""


def format_sources(entropy: EntropyBundle) -> str:
    if entropy["sources"]:
        blocks = []
        for index, source in enumerate(entropy["sources"], start=1):
            blocks.append(
                f"SOURCE {index}: {source['title']}\n"
                f"URL: {source['url']}\n"
                f"TEXT: {source['extract']}"
            )
        return "\n\n".join(blocks)

    blocks = []
    for index, fragment in enumerate(entropy["fragments"], start=1):
        blocks.append(f"FALLBACK FRAGMENT {index}: {fragment}")
    return "\n\n".join(blocks)


def normalize_brief(brief: SlopBrief, *, project_format: ProjectFormat, chaos: int) -> SlopBrief:
    slug = slugify(brief.get("slug") or brief.get("title") or "")
    brief["slug"] = slug
    brief["format"] = brief.get("format") if brief.get("format") in PROJECT_FORMATS else project_format
    brief["chaos"] = chaos
    brief["output_dir"] = f"slop-output/{slug}"
    return brief
