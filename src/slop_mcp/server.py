from __future__ import annotations

import argparse
import os
from typing import Literal

from mcp.server.fastmcp import FastMCP

from .entropy import fetch_entropy_bundle
from .gemini import generate_brief_with_gemini
from .models import PROJECT_FORMATS, EntropyBundle, ProjectFormat, SlopBrief
from .schema import SLOP_BRIEF_RESPONSE_SCHEMA
from .util import clamp_int

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - python-dotenv comes with mcp[cli]
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv()


FormatInput = ProjectFormat | Literal["random"]

mcp = FastMCP(
    "Slop MCP",
    stateless_http=True,
    json_response=True,
)


@mcp.tool()
def slop_get_entropy(source_count: int = 3) -> EntropyBundle:
    """Fetch random semantic source material for Slop Machine."""
    return fetch_entropy_bundle(source_count)


@mcp.tool()
def slop_generate_brief(
    project_format: FormatInput = "random",
    chaos: int = 7,
    source_count: int = 3,
    user_theme: str | None = None,
    include_raw_entropy: bool = False,
) -> dict[str, object]:
    """Generate a weird build-ready project brief using Wikipedia entropy and Gemini Flash-Lite."""
    if project_format != "random" and project_format not in PROJECT_FORMATS:
        raise ValueError(f"project_format must be one of {PROJECT_FORMATS} or 'random'")

    entropy = fetch_entropy_bundle(source_count)
    brief = generate_brief_with_gemini(
        entropy,
        project_format=project_format,
        chaos=clamp_int(chaos, default=7, minimum=1, maximum=10),
        user_theme=user_theme,
    )

    if include_raw_entropy:
        return {"brief": brief, "entropy": entropy}

    return {"brief": brief}


@mcp.resource("slop://brief-schema")
def slop_brief_schema() -> dict[str, object]:
    """Return the JSON schema requested from Gemini."""
    return SLOP_BRIEF_RESPONSE_SCHEMA


@mcp.prompt()
def build_slop_project(project_format: FormatInput = "random", chaos: int = 7) -> str:
    """Prompt a coding agent to generate and build one Slop Machine project."""
    return (
        "Call slop_generate_brief with "
        f"project_format={project_format!r} and chaos={chaos}. "
        "Then implement the returned brief exactly in its output_dir. "
        "Keep the generated project self-contained and add a README."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Slop MCP server.")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default=os.getenv("SLOP_MCP_TRANSPORT", "http"),
        help="Use stdio for local MCP clients or http for hosted Streamable HTTP.",
    )
    parser.add_argument("--host", default=os.getenv("HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8000")))
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run()
        return

    mcp.settings.host = args.host
    mcp.settings.port = args.port
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
