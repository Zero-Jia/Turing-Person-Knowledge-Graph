from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Iterable

try:
    from neo4j import GraphDatabase
except ImportError:  # pragma: no cover
    GraphDatabase = None

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = BASE_DIR / "data"

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "12345678")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "turning-kg")

DEFAULT_ENTITY_FILES = [
    DEFAULT_DATA_DIR / "entities.csv",
    DEFAULT_DATA_DIR / "entities_auto.csv",
]
DEFAULT_RELATION_FILES = [
    DEFAULT_DATA_DIR / "relations.csv",
    DEFAULT_DATA_DIR / "relations_auto.csv",
]

VALID_RELATIONS = {
    "BORN_IN",
    "STUDIED_AT",
    "WORKED_AT",
    "PROPOSED",
    "RELATED_TO",
    "AWARDED",
    "LOCATED_IN",
    "INFLUENCED",
}


def _parse_path_list(env_name: str, default_paths: list[Path]) -> list[Path]:
    raw = os.getenv(env_name, "").strip()
    if not raw:
        return default_paths
    return [Path(item.strip()) for item in raw.split(",") if item.strip()]


ENTITY_CSV_FILES = _parse_path_list("ENTITY_CSV_FILES", DEFAULT_ENTITY_FILES)
RELATION_CSV_FILES = _parse_path_list("RELATION_CSV_FILES", DEFAULT_RELATION_FILES)


def ensure_neo4j_available() -> None:
    if GraphDatabase is None:
        raise ImportError(
            "neo4j package is not installed. Run `pip install neo4j` before importing data."
        )


def read_csv_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_entity_rows(paths: Iterable[Path]) -> list[dict]:
    rows_by_name: dict[str, dict] = {}
    for path in paths:
        default_source = "auto" if "auto" in path.stem else "manual"
        for row in read_csv_rows(path):
            name = str(row.get("name", "")).strip()
            if not name:
                continue
            incoming = {
                "id": row.get("id") or None,
                "name": name,
                "type": str(row.get("type", "Entity")).strip() or "Entity",
                "source": str(row.get("source", default_source)).strip() or default_source,
            }
            current = rows_by_name.get(name)
            if current and current.get("source") == "manual" and incoming["source"] != "manual":
                continue
            rows_by_name[name] = incoming
    return list(rows_by_name.values())


def load_relation_rows(paths: Iterable[Path]) -> list[dict]:
    dedup: dict[tuple[str, str, str], dict] = {}
    for path in paths:
        for row in read_csv_rows(path):
            start = str(row.get("start", "")).strip()
            end = str(row.get("end", "")).strip()
            relation = str(row.get("relation", "")).strip().upper()
            if not start or not end or relation not in VALID_RELATIONS:
                continue
            dedup[(start, end, relation)] = {
                "start": start,
                "end": end,
                "relation": relation,
            }
    return list(dedup.values())


def create_constraints(tx):
    tx.run(
        "CREATE CONSTRAINT entity_name_unique IF NOT EXISTS "
        "FOR (e:Entity) REQUIRE e.name IS UNIQUE"
    )


def clear_graph(tx):
    tx.run("MATCH (n) DETACH DELETE n")


def import_entities(tx, rows: list[dict]):
    query = """
    UNWIND $rows AS row
    MERGE (e:Entity {name: row.name})
    SET e.type = row.type,
        e.source = coalesce(row.source, e.source, "manual"),
        e.id = CASE
            WHEN row.id IS NULL OR row.id = "" THEN e.id
            ELSE toInteger(row.id)
        END
    """
    tx.run(query, rows=rows)


def import_relations_by_type(tx, relation_type: str, rows: list[dict]):
    if relation_type not in VALID_RELATIONS:
        raise ValueError(f"Unsupported relation type: {relation_type}")

    query = f"""
    UNWIND $rows AS row
    MATCH (a:Entity {{name: row.start}})
    MATCH (b:Entity {{name: row.end}})
    MERGE (a)-[r:{relation_type}]->(b)
    """
    tx.run(query, rows=rows)


def upsert_to_neo4j(
    entity_rows: list[dict],
    relation_rows: list[dict],
    *,
    clear_existing: bool = False,
) -> None:
    ensure_neo4j_available()

    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
    )
    try:
        with driver.session(database=NEO4J_DATABASE) as session:
            session.execute_write(create_constraints)
            if clear_existing:
                session.execute_write(clear_graph)
            if entity_rows:
                session.execute_write(import_entities, entity_rows)
            relation_groups: dict[str, list[dict]] = {}
            for row in relation_rows:
                relation_groups.setdefault(row["relation"], []).append(row)
            for relation, rows in relation_groups.items():
                session.execute_write(import_relations_by_type, relation, rows)
    finally:
        driver.close()


def main() -> None:
    ensure_neo4j_available()

    entity_rows = load_entity_rows(ENTITY_CSV_FILES)
    relation_rows = load_relation_rows(RELATION_CSV_FILES)

    print("=== Importing CSV data into Neo4j ===")
    print(f"NEO4J_URI      = {NEO4J_URI}")
    print(f"NEO4J_DATABASE = {NEO4J_DATABASE}")
    print(f"ENTITY_CSVS    = {', '.join(str(p) for p in ENTITY_CSV_FILES)}")
    print(f"RELATION_CSVS  = {', '.join(str(p) for p in RELATION_CSV_FILES)}")
    print(f"Loaded entities : {len(entity_rows)}")
    print(f"Loaded relations: {len(relation_rows)}")

    answer = input("Clear existing graph before import? (yes/no): ").strip().lower()
    upsert_to_neo4j(
        entity_rows,
        relation_rows,
        clear_existing=(answer == "yes"),
    )

    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
    )
    try:
        with driver.session(database=NEO4J_DATABASE) as session:
            entity_count = session.run(
                "MATCH (n:Entity) RETURN count(n) AS entity_count"
            ).single()["entity_count"]
            relation_count = session.run(
                "MATCH ()-[r]->() RETURN count(r) AS relation_count"
            ).single()["relation_count"]
    finally:
        driver.close()

    print("=== Import complete ===")
    print(f"Graph entities : {entity_count}")
    print(f"Graph relations: {relation_count}")


if __name__ == "__main__":
    main()
