from __future__ import annotations


SENSITIVE_KEYWORDS = (
    "abuse",
    "antisemit",
    "assault",
    "atrocity",
    "ethnic cleansing",
    "extremism",
    "führer",
    "fuhrer",
    "genocide",
    "hate crime",
    "holocaust",
    "murder",
    "nazi",
    "racism",
    "rape",
    "slavery",
    "suicide",
    "terrorism",
    "war crime",
)


SAFETY_DISTILLATION_RULES = """Safety distillation rules:
- Random sources may include genocide, extremist ideology, sexual violence, racism, murder, abuse, self-harm, or other severe real-world harm.
- Do not make the generated project celebrate, roleplay, trivialize, aestheticize, gamify, eroticize, or directly simulate those harms.
- If a source is sensitive, extract only abstract, non-harmful structure from it, such as hierarchy, record-keeping, geography, scheduling, contradiction, bureaucracy, ritual, logistics, or public memory.
- If a source involves medical care, disability, patients, minors, disasters, victims, or marginalized groups, do not turn those people into game pieces, resources, jokes, obstacles, or props. Extract care systems, access patterns, routines, built environments, public records, or institutional structure instead.
- Blend sensitive sources with safer sources so the final artifact is playful, surreal, educational, archival, or critical without becoming a project about the harmful event or ideology itself.
- Prefer titles and concepts that are safe for a general coding agent to implement without triggering policy issues."""


def looks_sensitive(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in SENSITIVE_KEYWORDS)
