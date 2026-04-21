from __future__ import annotations

import re

SUPPORTED_RELATIONS = {
    "BORN_IN",
    "STUDIED_AT",
    "WORKED_AT",
    "PROPOSED",
    "RELATED_TO",
    "AWARDED",
    "LOCATED_IN",
    "INFLUENCED",
}

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|[。\n]+")
TRAILING_CLAUSE_RE = re.compile(r"(?:,| and | but | while ).*$", re.IGNORECASE)

RELATION_PATTERNS = [
    ("BORN_IN", re.compile(r"(?P<head>.+?)\s+(?:was born in|born in)\s+(?P<tail>.+)", re.IGNORECASE)),
    ("STUDIED_AT", re.compile(r"(?P<head>.+?)\s+(?:studied at|graduated from)\s+(?P<tail>.+)", re.IGNORECASE)),
    ("WORKED_AT", re.compile(r"(?P<head>.+?)\s+(?:worked at|worked for|served at)\s+(?P<tail>.+)", re.IGNORECASE)),
    ("PROPOSED", re.compile(r"(?P<head>.+?)\s+(?:proposed|invented|developed|introduced)\s+(?P<tail>.+)", re.IGNORECASE)),
    ("AWARDED", re.compile(r"(?P<head>.+?)\s+(?:won|received|was awarded)\s+(?P<tail>.+)", re.IGNORECASE)),
    ("LOCATED_IN", re.compile(r"(?P<head>.+?)\s+(?:is located in|was located in|located in)\s+(?P<tail>.+)", re.IGNORECASE)),
    ("INFLUENCED", re.compile(r"(?P<head>.+?)\s+(?:influenced|inspired)\s+(?P<tail>.+)", re.IGNORECASE)),
    ("RELATED_TO", re.compile(r"(?P<head>.+?)\s+(?:is related to|related to|associated with)\s+(?P<tail>.+)", re.IGNORECASE)),
]

SUBJECT_TYPE_BY_RELATION = {
    "BORN_IN": "Person",
    "STUDIED_AT": "Person",
    "WORKED_AT": "Person",
    "PROPOSED": "Person",
    "AWARDED": "Person",
    "LOCATED_IN": "Organization",
    "INFLUENCED": "Person",
}

OBJECT_TYPE_BY_RELATION = {
    "BORN_IN": "Place",
    "STUDIED_AT": "Organization",
    "WORKED_AT": "Organization",
    "PROPOSED": "Theory",
    "AWARDED": "Award",
    "LOCATED_IN": "Place",
}

PRONOUNS = {"he", "she", "they", "his", "her", "their"}


def split_sentences(text: str) -> list[str]:
    return [part.strip() for part in SENTENCE_SPLIT_RE.split(text) if part.strip()]


def clean_fragment(text: str) -> str:
    value = text.strip().strip(" .,:;!?\"'")
    value = re.sub(r"^(?:the|a|an)\s+", "", value, flags=re.IGNORECASE)
    value = TRAILING_CLAUSE_RE.sub("", value).strip()
    return value


def _match_entity_fragment(fragment: str, entities: list[dict]) -> str:
    cleaned = clean_fragment(fragment)
    cleaned_folded = cleaned.casefold()
    for entity in sorted(entities, key=lambda item: len(item["text"]), reverse=True):
        entity_text = entity["text"]
        entity_folded = entity_text.casefold()
        if cleaned_folded == entity_folded:
            return entity_text
        if entity_folded in cleaned_folded:
            return entity_text
    return cleaned


def extract_relations(
    sentence: str,
    entities: list[dict] | None = None,
    last_subject: str | None = None,
) -> list[dict]:
    entities = entities or []
    triples = []

    for relation, pattern in RELATION_PATTERNS:
        match = pattern.search(sentence)
        if not match:
            continue

        raw_head = clean_fragment(match.group("head"))
        raw_tail = clean_fragment(match.group("tail"))
        if not raw_head or not raw_tail:
            continue

        if raw_head.casefold() in PRONOUNS and last_subject:
            head_mention = last_subject
        else:
            head_mention = _match_entity_fragment(raw_head, entities)
        tail_mention = _match_entity_fragment(raw_tail, entities)

        triples.append(
            {
                "head_mention": head_mention,
                "head_type": SUBJECT_TYPE_BY_RELATION.get(relation),
                "relation": relation,
                "tail_mention": tail_mention,
                "tail_type": OBJECT_TYPE_BY_RELATION.get(relation),
                "source_sentence": sentence,
            }
        )

    dedup: dict[tuple[str, str, str], dict] = {}
    for triple in triples:
        key = (
            triple["head_mention"].casefold(),
            triple["relation"],
            triple["tail_mention"].casefold(),
        )
        dedup[key] = triple
    return list(dedup.values())
