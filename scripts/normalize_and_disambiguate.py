# 归一化 / 消歧脚本
import json
from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"

INPUT_PATH = DATA_DIR / "extracted_triples.csv"
OUTPUT_PATH = DATA_DIR / "normalized_triples.csv"


def normalize_name(name: str, alias_map: dict) -> str:
    name = str(name).strip()
    return alias_map.get(name, name)


def main():
    alias_path = CONFIG_DIR / "alias_map.json"
    with open(alias_path, "r", encoding="utf-8") as f:
        alias_map = json.load(f)

    df = pd.read_csv(INPUT_PATH)

    print("=== 归一化前 ===")
    print(df[["head", "relation", "tail"]])

    df["head"] = df["head"].apply(lambda x: normalize_name(x, alias_map))
    df["tail"] = df["tail"].apply(lambda x: normalize_name(x, alias_map))

    # 按三元组去重
    df = df.drop_duplicates(subset=["head", "relation", "tail"])

    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")

    print("\n=== 归一化后 ===")
    print(df[["head", "relation", "tail"]])

    print("\n归一化 / 基础消歧完成！")
    print(f"输出文件: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()