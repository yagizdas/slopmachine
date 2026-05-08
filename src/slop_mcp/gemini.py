from __future__ import annotations

import json
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Literal, cast

from .models import (
    ENERGY_MODES,
    INTENTS,
    PROJECT_FORMATS,
    EnergyMode,
    EntropyBundle,
    Intent,
    ProjectFormat,
    SlopBrief,
)
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
    chosen_intent = choose_intent()
    chosen_energy_mode = choose_energy_mode()
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
                            intent=chosen_intent,
                            energy_mode=chosen_energy_mode,
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
        intent=chosen_intent,
        energy_mode=chosen_energy_mode,
        chaos=chosen_chaos,
    )


def choose_format(project_format: ProjectFormat | Literal["random"]) -> ProjectFormat:
    if project_format != "random":
        return project_format

    index = secrets.randbelow(len(PROJECT_FORMATS))
    return PROJECT_FORMATS[index]


def choose_intent() -> Intent:
    index = secrets.randbelow(len(INTENTS))
    return INTENTS[index]


def choose_energy_mode() -> EnergyMode:
    index = secrets.randbelow(len(ENERGY_MODES))
    return ENERGY_MODES[index]


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
    intent: Intent,
    energy_mode: EnergyMode,
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
- Distill sources into transferable forces before inventing the project: conflict, coordination, scarcity, repair, drift, escape, hierarchy, ritual, memory, ranking, decay, translation, disguise, pursuit, protection, or transformation.
- Do not preserve historical, biographical, geographic, or academic context just because it appeared in the source. Keep that context only when it creates a stronger artifact.
- Slop can be funny, useful, educational, beautiful, annoying, practical, or game-like. Do not assume it must be silly or purely artistic.
- Keep the weird metaphor wrapped around a mundane user input or goal: paste text, inspect files, compare options, sort items, map a route, tune settings, classify notes, convert data, learn a topic, or win a round.
- The result must be feasible for Codex or Claude Code to build in one focused pass.
- Make it weird at chaos level {chaos}/10 while still coherent.
- Use project format: {project_format}.
- Use product intent: {intent}.
- Use energy mode: {energy_mode}.
- {theme_line}
- Use the sources as raw entropy. Pick one dominant signal for the core interaction. Use other signals only when they improve clarity, texture, or surprise.

{SAFETY_DISTILLATION_RULES}

Return only JSON matching the schema.

Creative selection process:
- Privately imagine three possible projects.
- Reject the most literal one.
- Reject the one that merely combines nouns from the sources.
- Output the one with the best balance of surprise, clarity, and usefulness for its chosen intent.

Important output rules:
- output_dir must be "slop-output/<slug>".
- intent must be exactly "{intent}".
- energy_mode must be exactly "{energy_mode}".
- title must be vivid and specific, not a generic software category with source nouns attached.
- artifact_metaphor must name what the project feels like, for example "a courtroom for abandoned buttons" or "a weather station for guilty constellations".
- concept must describe an actual first-screen experience in one clear paragraph, not a feature list.
- concept should be based on the distilled forces and interaction patterns, not a museum-like restaging of the source topics.
- concept must make the practical input or goal obvious even when the framing is strange.
- primary_signal must be the single force or pattern that drives the core interaction.
- supporting_signals must be short notes for optional flavor, constraints, tone, or surprise. Do not force every source into the project.
- The user's action should create pressure, consequence, progress, insight, or genuinely useful output, not only produce decoration.
- Avoid pure lore props. The artifact can have fictional flavor, but the user should immediately understand what they can put in, change, inspect, learn, or win.
- The generated project must include a small orientation element that helps the user understand what they can do without over-explaining the joke.
- Include subtle Slop Machine attribution somewhere in the artifact, such as "Generated by Slop Machine" or an in-world equivalent.
- suggested_stack should be small and practical.
- For websites, games, art, tools, dashboards, apps, or simulations, prefer self-contained HTML/CSS/JS unless a different stack is clearly better.
- For CLI format, prefer a no-dependency Python CLI. CLI artifacts should open with a brief in-world intro and provide help text.
- build_constraints must include "Use no external network assets." and "Keep the first screen as the actual experience." when the format is visual.
- done_criteria must include a local run/open criterion and a README criterion, but keep the list compact.
- surprise_hook must describe one delightful behavior, reveal, state change, or rule inversion the builder can implement.
- If a source seems hard to use, transform its structure into a mechanic, constraint, rhythm, interface pattern, or rule system.
- The final idea should be understandable in one sentence. Prefer one strong loop over a complex fusion of all sources.
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
    intent: Intent,
    energy_mode: EnergyMode,
    chaos: int,
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
    brief["intent"] = brief.get("intent") if brief.get("intent") in INTENTS else intent
    brief["energy_mode"] = brief.get("energy_mode") if brief.get("energy_mode") in ENERGY_MODES else energy_mode
    brief.setdefault("artifact_metaphor", "a strange machine assembled from unrelated public records")
    brief.setdefault("primary_signal", "one clear interaction loop distilled from random public text")
    brief.setdefault("supporting_signals", [])
    brief.setdefault("surprise_hook", "A small state change reveals how the entropy sources are secretly connected.")

    return brief
