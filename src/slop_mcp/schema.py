from __future__ import annotations

from .models import PROJECT_FORMATS


SLOP_BRIEF_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "title": {"type": "STRING"},
        "slug": {"type": "STRING"},
        "format": {"type": "STRING", "enum": list(PROJECT_FORMATS)},
        "chaos": {"type": "INTEGER", "minimum": 1, "maximum": 10},
        "output_dir": {"type": "STRING"},
        "artifact_metaphor": {"type": "STRING"},
        "concept": {"type": "STRING"},
        "source_influences": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "source_title": {"type": "STRING"},
                    "extracted_signal": {"type": "STRING"},
                    "project_manifestation": {"type": "STRING"},
                },
                "required": [
                    "source_title",
                    "extracted_signal",
                    "project_manifestation",
                ],
                "propertyOrdering": [
                    "source_title",
                    "extracted_signal",
                    "project_manifestation",
                ],
            },
            "minItems": 3,
            "maxItems": 8,
        },
        "fusion_mechanic": {"type": "STRING"},
        "surprise_hook": {"type": "STRING"},
        "core_interaction": {"type": "STRING"},
        "suggested_stack": {"type": "STRING"},
        "build_constraints": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "minItems": 3,
            "maxItems": 5,
        },
        "done_criteria": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "minItems": 3,
            "maxItems": 5,
        },
    },
    "required": [
        "title",
        "slug",
        "format",
        "chaos",
        "output_dir",
        "artifact_metaphor",
        "concept",
        "source_influences",
        "fusion_mechanic",
        "surprise_hook",
        "core_interaction",
        "suggested_stack",
        "build_constraints",
        "done_criteria",
    ],
    "propertyOrdering": [
        "title",
        "slug",
        "format",
        "chaos",
        "output_dir",
        "artifact_metaphor",
        "concept",
        "source_influences",
        "fusion_mechanic",
        "surprise_hook",
        "core_interaction",
        "suggested_stack",
        "build_constraints",
        "done_criteria",
    ],
}
