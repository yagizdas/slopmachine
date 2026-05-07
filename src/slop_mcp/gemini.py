from __future__ import annotations

import json
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Literal, cast

from .models import EntropyBundle, PROJECT_FORMATS, ProjectFormat, SlopBrief
from .safety import SAFETY_DISTILLATION_RULES, looks_sensitive
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
    return normalize_brief(
        brief,
        project_format=chosen_format,
        chaos=chosen_chaos,
        entropy=entropy,
    )


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
- Transform random source text into one strange but buildable software artifact.
- Use ideas from the sources, but remix them hard.
- The output should feel like a discovered object from a tiny alternate internet, not a normal utility app.
- Avoid the most literal or default software interpretation of the sources.
- The result must be feasible for Codex or Claude Code to build in one focused pass.
- Make it weird at chaos level {chaos}/10 while still coherent.
- Use project format: {project_format}.
- {theme_line}
- Every source must visibly affect the final project. Do not let one source dominate while the others become decorative.

{SAFETY_DISTILLATION_RULES}

Return only JSON matching the schema.

Creative selection process:
- Privately imagine three possible projects.
- Reject the most literal one.
- Reject the one that merely combines nouns from the sources.
- Output the one with the strongest central metaphor, clearest interaction, and most surprising buildable artifact.

Important output rules:
- output_dir must be "slop-output/<slug>".
- title must be vivid and specific, not a generic software category with source nouns attached.
- artifact_metaphor must name what the project feels like, for example "a courtroom for abandoned buttons" or "a weather station for guilty constellations".
- concept must describe an actual first-screen experience, not a feature list.
- suggested_stack should be small and practical.
- For websites, games, art, tools, dashboards, apps, or simulations, prefer self-contained HTML/CSS/JS unless a different stack is clearly better.
- For CLI format, prefer a no-dependency Python CLI.
- build_constraints must include "Use no external network assets." and "Keep the first screen as the actual experience." when the format is visual.
- done_criteria must include a local run/open criterion and a README criterion, but keep the list compact.
- source_influences must contain one object per source, using the exact source title, a concrete extracted signal, and the specific UI/mechanic/content manifestation in the project.
- fusion_mechanic must explain the central design move that combines the sources into one artifact, not three unrelated references.
- surprise_hook must describe one delightful behavior, reveal, state change, or rule inversion the builder can implement.
- If a source seems hard to use, transform its structure into a mechanic, constraint, rhythm, interface pattern, or rule system.
- Every format, including CLI, should have a vivid interaction loop rather than only a list of ordinary operations.

Random semantic source material:

{sources}
"""


def format_sources(entropy: EntropyBundle) -> str:
    if entropy["sources"]:
        blocks = []
        for index, source in enumerate(entropy["sources"], start=1):
            sensitive_note = ""
            if looks_sensitive(f"{source['title']} {source['extract']}"):
                sensitive_note = (
                    "\nSAFETY NOTE: This source appears to contain severe real-world harm "
                    "or extremist/hateful material. Use only abstract non-harmful structure "
                    "from it; do not center the generated project on the harmful content."
                )
            blocks.append(
                f"SOURCE {index}: {source['title']}\n"
                f"URL: {source['url']}\n"
                f"TEXT: {source['extract']}"
                f"{sensitive_note}"
            )
        return "\n\n".join(blocks)

    blocks = []
    for index, fragment in enumerate(entropy["fragments"], start=1):
        blocks.append(f"FALLBACK FRAGMENT {index}: {fragment}")
    return "\n\n".join(blocks)


def normalize_brief(
    brief: SlopBrief,
    *,
    project_format: ProjectFormat,
    chaos: int,
    entropy: EntropyBundle | None = None,
) -> SlopBrief:
    title = brief.get("title") or "Slop Machine Project"
    if looks_sensitive(title):
        title = "Absurd Archive Control Panel"
        brief["title"] = title

    slug = slugify(brief.get("slug") or title)
    if looks_sensitive(slug):
        slug = slugify(title)

    brief["slug"] = slug
    brief["format"] = brief.get("format") if brief.get("format") in PROJECT_FORMATS else project_format
    brief["chaos"] = chaos
    brief["output_dir"] = f"slop-output/{slug}"
    brief.setdefault("artifact_metaphor", "a strange machine assembled from unrelated public records")
    brief.setdefault("fusion_mechanic", "Blend each entropy source into one coherent interaction loop.")
    brief.setdefault("surprise_hook", "A small state change reveals how the entropy sources are secretly connected.")

    if entropy and entropy["sources"]:
        expected_count = min(len(entropy["sources"]), 8)
        influence_count = len(brief.get("source_influences", []))
        if influence_count < expected_count:
            raise RuntimeError(
                "Gemini returned too few source_influences; each entropy source must have a mapping"
            )

    return brief
