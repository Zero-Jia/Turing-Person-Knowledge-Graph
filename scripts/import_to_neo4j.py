from __future__ import annotations

import csv
import os
from pathlib import Path
from neo4j import GraphDatabase

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = BASE_DIR / "data"

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "12345678")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "turning-kg")

ENTITIES_CSV = Path(os.getenv("ENTITIES_CSV", str(DEFAULT_DATA_DIR / "entities_auto.csv")))
RELATIONS_CSV = Path(os.getenv("RELATIONS_CSV", str(DEFAULT_DATA_DIR / "relations_auto.csv")))


def read_csv_rows(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"CSV 文件不存在: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def create_constraints(tx):
    tx.run("CREATE CONSTRAINT entity_name_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE")


def clear_graph(tx):
    tx.run("MATCH (n) DETACH DELETE n")


def import_entities(tx, rows: list[dict]):
    query = """
    UNWIND $rows AS row
    MERGE (e:Entity {name: row.name})
    SET e.id = toInteger(row.id),
        e.type = row.type
    """
    tx.run(query, rows=rows)


def import_relations(tx, rows: list[dict]):
    query = """
    UNWIND $rows AS row
    MATCH (a:Entity {name: row.start})
    MATCH (b:Entity {name: row.end})
    MERGE (a)-[r:RELATION {type: row.relation}]->(b)
    """
    tx.run(query, rows=rows)


def main() -> None:
    if NEO4J_PASSWORD == "please_set_password":
        raise ValueError(
            "请先设置环境变量 NEO4J_PASSWORD，例如：\n"
            "export NEO4J_PASSWORD='你的密码'"
        )

    print("=== 开始导入 Neo4j ===")
    print(f"NEO4J_URI      = {NEO4J_URI}")
    print(f"NEO4J_DATABASE = {NEO4J_DATABASE}")
    print(f"ENTITIES_CSV   = {ENTITIES_CSV}")
    print(f"RELATIONS_CSV  = {RELATIONS_CSV}")

    entity_rows = read_csv_rows(ENTITIES_CSV)
    relation_rows = read_csv_rows(RELATIONS_CSV)

    print(f"读取到实体数: {len(entity_rows)}")
    print(f"读取到关系数: {len(relation_rows)}")

    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
    )

    try:
        with driver.session(database=NEO4J_DATABASE) as session:
            session.execute_write(create_constraints)

            answer = input("是否先清空当前数据库中的所有节点和关系？(yes/no): ").strip().lower()
            if answer == "yes":
                session.execute_write(clear_graph)
                print("已清空旧图谱。")

            session.execute_write(import_entities, entity_rows)
            print("实体导入完成。")

            session.execute_write(import_relations, relation_rows)
            print("关系导入完成。")

            result = session.run(
                "MATCH (n:Entity) RETURN count(n) AS entity_count"
            )
            entity_count = result.single()["entity_count"]

            result = session.run(
                "MATCH ()-[r:RELATION]->() RETURN count(r) AS relation_count"
            )
            relation_count = result.single()["relation_count"]

            print("=== 导入完成 ===")
            print(f"图谱实体数量: {entity_count}")
            print(f"图谱关系数量: {relation_count}")

    finally:
        driver.close()


if __name__ == "__main__":
    main()
