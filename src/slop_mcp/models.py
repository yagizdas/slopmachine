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

Intent = Literal[
    "funny_toy",
    "useful_utility",
    "educational_explainer",
    "reference_browser",
    "small_game",
    "creative_instrument",
    "simulation",
    "developer_tool",
    "map_explorer",
    "data_converter",
    "diagnostic_tool",
    "fake_os_tool",
]

EnergyMode = Literal[
    "frantic",
    "cozy",
    "competitive",
    "tactical",
    "mischievous",
    "ceremonial",
    "mechanical",
    "elegant",
    "meditative",
    "practical",
    "gross",
    "bureaucratic",
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

INTENTS: tuple[Intent, ...] = (
    "funny_toy",
    "useful_utility",
    "educational_explainer",
    "reference_browser",
    "small_game",
    "creative_instrument",
    "simulation",
    "developer_tool",
    "map_explorer",
    "data_converter",
    "diagnostic_tool",
    "fake_os_tool",
)

ENERGY_MODES: tuple[EnergyMode, ...] = (
    "frantic",
    "cozy",
    "competitive",
    "tactical",
    "mischievous",
    "ceremonial",
    "mechanical",
    "elegant",
    "meditative",
    "practical",
    "gross",
    "bureaucratic",
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
    intent: Intent
    energy_mode: EnergyMode
    artifact_metaphor: str
    concept: str
    primary_signal: str
    supporting_signals: list[str]
    surprise_hook: str
    core_interaction: str
    suggested_stack: str
    build_constraints: list[str]
    done_criteria: list[str]
