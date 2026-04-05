# 知识抽取脚本
import json
import re
from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw_texts"
CONFIG_DIR = BASE_DIR / "config"
OUTPUT_PATH = BASE_DIR / "data" / "extracted_triples.csv"


def split_sentences(text: str):
    # 简单中英文分句
    parts = re.split(r"[。\n]+|(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def load_patterns():
    pattern_path = CONFIG_DIR / "relation_patterns.json"
    with open(pattern_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    compiled = []
    for item in data["patterns"]:
        compiled.append({
            "relation": item["relation"],
            "regex": re.compile(item["regex"], re.IGNORECASE)
        })
    return compiled


def extract_from_sentence(sentence, patterns, source_file):
    triples = []
    cleaned = sentence.strip().rstrip(".")

    for item in patterns:
        match = item["regex"].match(cleaned)
        if match:
            head = match.group("head").strip()
            tail = match.group("tail").strip()
            triples.append({
                "head": head,
                "relation": item["relation"],
                "tail": tail,
                "source_sentence": sentence,
                "source_file": source_file
            })

    return triples


def main():
    patterns = load_patterns()
    all_triples = []

    for txt_file in RAW_DIR.glob("*.txt"):
        text = txt_file.read_text(encoding="utf-8")
        sentences = split_sentences(text)

        for sentence in sentences:
            triples = extract_from_sentence(sentence, patterns, txt_file.name)
            all_triples.extend(triples)

    df = pd.DataFrame(all_triples)

    if df.empty:
        print("没有抽取到任何三元组，请检查文本或模式。")
        return

    df = df.drop_duplicates()
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")

    print("知识抽取完成！")
    print(f"抽取到三元组数量: {len(df)}")
    print(f"输出文件: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()