from __future__ import annotations

import csv
from pathlib import Path

from .entity_linking import EntityLinker
from .ner import recognize_entities
from .relation_extraction import extract_relations, split_sentences

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

MANUAL_ENTITIES_CSV = DATA_DIR / "entities.csv"
AUTO_ENTITIES_CSV = DATA_DIR / "entities_auto.csv"
AUTO_RELATIONS_CSV = DATA_DIR / "relations_auto.csv"
EXTRACTED_TRIPLES_CSV = DATA_DIR / "extracted_triples.csv"


def _read_csv_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _write_csv_rows(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _next_entity_id() -> int:
    max_id = 0
    for path in (MANUAL_ENTITIES_CSV, AUTO_ENTITIES_CSV):
        for row in _read_csv_rows(path):
            try:
                max_id = max(max_id, int(row.get("id", 0)))
            except (TypeError, ValueError):
                continue
    return max_id + 1


def append_entities_to_auto_csv(entities: list[dict]) -> list[dict]:
    existing_rows = _read_csv_rows(AUTO_ENTITIES_CSV)
    existing_by_name = {
        str(row.get("name", "")).strip(): row
        for row in existing_rows
        if str(row.get("name", "")).strip()
    }

    next_id = _next_entity_id()
    for entity in entities:
        name = entity["name"]
        if name in existing_by_name:
            existing_by_name[name]["type"] = entity["type"]
            existing_by_name[name]["source"] = entity.get("source", "auto")
            continue
        existing_by_name[name] = {
            "id": next_id,
            "name": name,
            "type": entity["type"],
            "source": entity.get("source", "auto"),
        }
        next_id += 1

    rows = sorted(existing_by_name.values(), key=lambda row: str(row["name"]).casefold())
    _write_csv_rows(AUTO_ENTITIES_CSV, ["id", "name", "type", "source"], rows)
    return rows


def append_relations_to_auto_csv(triples: list[dict]) -> list[dict]:
    existing_rows = _read_csv_rows(AUTO_RELATIONS_CSV)
    dedup: dict[tuple[str, str, str], dict] = {}

    for row in existing_rows:
        start = str(row.get("start", "")).strip()
        end = str(row.get("end", "")).strip()
        relation = str(row.get("relation", "")).strip()
        if start and end and relation and start != end:
            dedup[(start, end, relation)] = {
                "start": start,
                "end": end,
                "relation": relation,
            }

    for triple in triples:
        if triple["head"] == triple["tail"]:
            continue
        key = (triple["head"], triple["tail"], triple["relation"])
        dedup[key] = {
            "start": triple["head"],
            "end": triple["tail"],
            "relation": triple["relation"],
        }

    rows = sorted(dedup.values(), key=lambda row: (row["start"], row["relation"], row["end"]))
    _write_csv_rows(AUTO_RELATIONS_CSV, ["start", "end", "relation"], rows)
    return rows


def write_extracted_triples_csv(triples: list[dict]) -> None:
    rows = [
        {
            "head": triple["head"],
            "relation": triple["relation"],
            "tail": triple["tail"],
            "source_sentence": triple["source_sentence"],
        }
        for triple in triples
    ]
    _write_csv_rows(
        EXTRACTED_TRIPLES_CSV,
        ["head", "relation", "tail", "source_sentence"],
        rows,
    )


def _dedup_entities(entities: list[dict]) -> list[dict]:
    dedup = {}
    for entity in entities:
        dedup[entity["name"]] = entity
    return sorted(dedup.values(), key=lambda item: item["name"].casefold())


def _dedup_triples(triples: list[dict]) -> list[dict]:
    dedup = {}
    for triple in triples:
        dedup[(triple["head"], triple["relation"], triple["tail"])] = triple
    return [
        dedup[key]
        for key in sorted(dedup, key=lambda item: (item[0].casefold(), item[1], item[2].casefold()))
    ]


def extract_kg_from_text(
    text: str,
    *,
    persist: bool = True,
    write_neo4j: bool = True,
) -> dict:
    linker = EntityLinker()
    sentences = split_sentences(text)

    resolved_entities: list[dict] = []
    resolved_triples: list[dict] = []
    last_person: str | None = None

    for sentence in sentences:
        sentence_entities = recognize_entities(sentence, linker.known_entity_names())

        for entity in sentence_entities:
            resolved = linker.resolve_entity(
                entity["text"],
                context=sentence,
                entity_type=entity["type"],
            )
            resolved_entities.append(
                {
                    "name": resolved["name"],
                    "type": resolved["type"],
                    "source": resolved.get("source", "auto"),
                }
            )

        for raw_triple in extract_relations(sentence, sentence_entities, last_subject=last_person):
            head = linker.resolve_entity(
                raw_triple["head_mention"],
                context=sentence,
                entity_type=raw_triple.get("head_type"),
            )
            tail = linker.resolve_entity(
                raw_triple["tail_mention"],
                context=sentence,
                entity_type=raw_triple.get("tail_type"),
            )
            resolved_entities.extend(
                [
                    {"name": head["name"], "type": head["type"], "source": head.get("source", "auto")},
                    {"name": tail["name"], "type": tail["type"], "source": tail.get("source", "auto")},
                ]
            )
            resolved_triples.append(
                {
                    "head": head["name"],
                    "relation": raw_triple["relation"],
                    "tail": tail["name"],
                    "source_sentence": raw_triple["source_sentence"],
                }
            )
            if head["type"] == "Person":
                last_person = head["name"]

    entities = _dedup_entities(resolved_entities)
    triples = _dedup_triples(resolved_triples)

    if persist:
        append_entities_to_auto_csv(entities)
        append_relations_to_auto_csv(triples)
        write_extracted_triples_csv(triples)

    neo4j_written = False
    neo4j_error = None
    if write_neo4j and triples:
        try:
            from scripts.import_to_neo4j import upsert_to_neo4j

            upsert_to_neo4j(
                entity_rows=entities,
                relation_rows=[
                    {"start": triple["head"], "end": triple["tail"], "relation": triple["relation"]}
                    for triple in triples
                ],
                clear_existing=False,
            )
            neo4j_written = True
        except Exception as exc:  # pragma: no cover
            neo4j_error = str(exc)

    return {
        "entities": entities,
        "triples": [(triple["head"], triple["relation"], triple["tail"]) for triple in triples],
        "triple_details": triples,
        "neo4j_written": neo4j_written,
        "neo4j_error": neo4j_error,
    }
