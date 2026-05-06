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


class SlopBrief(TypedDict):
    title: str
    slug: str
    format: ProjectFormat
    chaos: int
    output_dir: str
    one_line_pitch: str
    concept: str
    source_influences: list[str]
    core_interaction: str
    visual_direction: str
    suggested_stack: str
    build_constraints: list[str]
    expected_files: list[str]
    done_criteria: list[str]
    entropy_digest: str
