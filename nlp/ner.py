from __future__ import annotations

import re
from functools import lru_cache
from typing import Iterable

ENTITY_LABEL_MAP = {
    "PERSON": "Person",
    "PER": "Person",
    "ORG": "Organization",
    "GPE": "Place",
    "LOC": "Place",
    "FAC": "Place",
}

TITLE_PREFIXES = {"Dr", "Prof", "Professor", "Sir", "Mr", "Mrs", "Ms"}
STOP_ENTITY_TEXT = {
    "He",
    "She",
    "They",
    "It",
    "His",
    "Her",
    "Their",
    "The",
    "A",
    "An",
}

CAPITALIZED_PHRASE_RE = re.compile(
    r"\b(?:[A-Z][a-z]+|[A-Z]{2,}|von|de|of|the)"
    r"(?:\s+(?:[A-Z][a-z]+|[A-Z]{2,}|von|de|of|the|Machine|Theory|Award|Prize|University|Institute|Park)){0,5}\b"
)


@lru_cache(maxsize=1)
def _load_spacy():
    try:
        import spacy
    except ImportError:
        return None

    for model_name in ("en_core_web_sm", "en_core_web_md", "xx_ent_wiki_sm"):
        try:
            return spacy.load(model_name)
        except Exception:
            continue
    return None


def infer_entity_type(text: str, label: str | None = None) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip(" .,:;!?\"'")
    lowered = cleaned.lower()
    if label and label.upper() in ENTITY_LABEL_MAP:
        return ENTITY_LABEL_MAP[label.upper()]
    if any(token in cleaned for token in ("Machine", "Theory", "Test")):
        return "Theory"
    if any(token in cleaned for token in ("Award", "Prize", "Medal")):
        return "Award"
    if any(token in cleaned for token in ("University", "Institute", "Laboratory", "Lab", "College", "Park")):
        return "Organization"
    if lowered in {"london", "cambridge", "manchester", "princeton", "bletchley", "maida vale"}:
        return "Place"
    parts = cleaned.split()
    if parts and parts[0] in TITLE_PREFIXES:
        return "Person"
    if len(parts) >= 2 and all(p[:1].isupper() or p in {"von", "de", "of"} for p in parts):
        return "Person"
    return "Organization"


def _iter_known_entity_matches(text: str, known_entity_names: Iterable[str]) -> list[dict]:
    matches = []
    for name in sorted(set(known_entity_names), key=len, reverse=True):
        if not name:
            continue
        for match in re.finditer(re.escape(name), text, flags=re.IGNORECASE):
            mention = text[match.start() : match.end()]
            matches.append(
                {
                    "text": mention,
                    "type": infer_entity_type(name),
                    "start": match.start(),
                    "end": match.end(),
                }
            )
    return matches


def _regex_entities(text: str) -> list[dict]:
    entities = []
    for match in CAPITALIZED_PHRASE_RE.finditer(text):
        mention = match.group(0).strip()
        mention = re.sub(r"^(?:The|A|An)\s+", "", mention)
        mention = mention.strip(" .,:;!?\"'")
        if not mention or mention in STOP_ENTITY_TEXT or len(mention) < 2:
            continue
        entities.append(
            {
                "text": mention,
                "type": infer_entity_type(mention),
                "start": match.start(),
                "end": match.end(),
            }
        )
    return entities


def recognize_entities(text: str, known_entity_names: Iterable[str] | None = None) -> list[dict]:
    candidates: list[dict] = []

    nlp = _load_spacy()
    if nlp is not None:
        doc = nlp(text)
        for ent in doc.ents:
            mention = ent.text.strip()
            if mention in STOP_ENTITY_TEXT:
                continue
            candidates.append(
                {
                    "text": mention,
                    "type": infer_entity_type(mention, ent.label_),
                    "start": ent.start_char,
                    "end": ent.end_char,
                }
            )

    if known_entity_names:
        candidates.extend(_iter_known_entity_matches(text, known_entity_names))

    candidates.extend(_regex_entities(text))

    dedup: dict[tuple[int, int, str], dict] = {}
    for item in candidates:
        key = (item["start"], item["end"], item["text"].lower())
        current = dedup.get(key)
        if current is None or current["type"] == "Organization":
            dedup[key] = item

    items = sorted(dedup.values(), key=lambda item: (item["start"], -(item["end"] - item["start"])))
    filtered: list[dict] = []
    for item in items:
        overlapped = False
        for kept in filtered:
            if item["start"] >= kept["start"] and item["end"] <= kept["end"]:
                overlapped = True
                break
        if not overlapped:
            filtered.append(item)

    return sorted(filtered, key=lambda item: (item["start"], item["end"]))
