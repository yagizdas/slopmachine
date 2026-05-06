# Slop Machine

Slop Machine is the hosted version of the "I'm Feeling Lucky" idea generator. It exposes MCP tools that fetch random semantic source material, ask Gemini 2.5 Flash-Lite to distill it into a weird-but-buildable project brief, and return structured JSON for Codex, Claude Code, or any MCP client to implement.

The server returns a brief, not generated code. That keeps cheap idea generation separate from the more expensive coding agent.

## Tools

- `slop_get_entropy`: fetches raw semantic source material from random Wikipedia pages.
- `slop_generate_brief`: fetches entropy and uses Gemini to produce a build-ready project brief.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

Set `GEMINI_API_KEY` in `.env` or your hosting provider's environment variables.

## Run

Hosted Streamable HTTP:

```bash
GEMINI_API_KEY=... slop-mcp --transport http --port 8000
```

The MCP endpoint is:

```text
http://localhost:8000/mcp
```

Local stdio transport:

```bash
GEMINI_API_KEY=... slop-mcp --transport stdio
```

## Build Flow

An MCP client should:

1. Call `slop_generate_brief`.
2. Read the returned `brief.output_dir`.
3. Build the generated project only inside that directory.
4. Preview locally.
5. Deploy only after explicit user approval.
