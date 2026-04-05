# 把三元组转换成 Neo4j 图谱 CSV
from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

INPUT_PATH = DATA_DIR / "normalized_triples.csv"
ENTITIES_OUTPUT = DATA_DIR / "entities_auto.csv"
RELATIONS_OUTPUT = DATA_DIR / "relations_auto.csv"


def infer_type(name: str, relation: str, position: str) -> str:
    # 非常轻量的类型推断
    if name in ["Alan Turing", "Alonzo Church", "Claude Shannon", "Marvin Minsky", "John von Neumann"]:
        return "Person"

    if "University" in name or "Park" in name:
        return "Organization"

    if name in ["Turing Machine", "Turing Test", "Artificial Intelligence", "Computability Theory"]:
        return "Theory"

    if "Award" in name:
        return "Award"

    return "Place"


def main():
    df = pd.read_csv(INPUT_PATH)

    entity_names = set(df["head"].tolist()) | set(df["tail"].tolist())
    entity_names = sorted(entity_names)

    entity_rows = []

    for idx, name in enumerate(entity_names, start=1):
        sub = df[(df["head"] == name) | (df["tail"] == name)].iloc[0]
        relation = sub["relation"]

        if sub["head"] == name:
            entity_type = infer_type(name, relation, "head")
        else:
            entity_type = infer_type(name, relation, "tail")

        entity_rows.append({
            "id": idx,
            "name": name,
            "type": entity_type
        })

    entities_df = pd.DataFrame(entity_rows)

    relations_df = df[["head", "tail", "relation"]].rename(
        columns={"head": "start", "tail": "end"}
    )

    entities_df.to_csv(ENTITIES_OUTPUT, index=False, encoding="utf-8")
    relations_df.to_csv(RELATIONS_OUTPUT, index=False, encoding="utf-8")

    print("图谱 CSV 构建完成！")
    print(f"实体文件: {ENTITIES_OUTPUT}")
    print(f"关系文件: {RELATIONS_OUTPUT}")


if __name__ == "__main__":
    main()