from __future__ import annotations

from typing import Literal, TypedDict


ProjectFormat = Literal[
    "website",
    "browser_game",
    "cli",
    "dashboard",
    "creative_tool",
    "simulation",
    "micro_app",
    "generative_art",
]

PROJECT_FORMATS: tuple[ProjectFormat, ...] = (
    "website",
    "browser_game",
    "cli",
    "dashboard",
    "creative_tool",
    "simulation",
    "micro_app",
    "generative_art",
)


class EntropySource(TypedDict):
    title: str
    extract: str
    url: str


class EntropyBundle(TypedDict):
    sources: list[EntropySource]
    fragments: list[str]
    generated_at: str


class SourceInfluence(TypedDict):
    source_title: str
    extracted_signal: str
    project_manifestation: str


class SlopBrief(TypedDict):
    title: str
    slug: str
    format: ProjectFormat
    chaos: int
    output_dir: str
    artifact_metaphor: str
    concept: str
    source_influences: list[SourceInfluence]
    fusion_mechanic: str
    surprise_hook: str
    core_interaction: str
    suggested_stack: str
    build_constraints: list[str]
    done_criteria: list[str]
