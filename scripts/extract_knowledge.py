from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw_texts"
OUTPUT_PATH = BASE_DIR / "data" / "extracted_triples.csv"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from nlp.pipeline import extract_kg_from_text


def main() -> None:
    all_rows = []

    for txt_file in RAW_DIR.glob("*.txt"):
        text = txt_file.read_text(encoding="utf-8")
        result = extract_kg_from_text(text, persist=True, write_neo4j=False)
        for triple in result["triple_details"]:
            all_rows.append(
                {
                    "head": triple["head"],
                    "relation": triple["relation"],
                    "tail": triple["tail"],
                    "source_sentence": triple["source_sentence"],
                    "source_file": txt_file.name,
                }
            )

    df = pd.DataFrame(all_rows)
    if df.empty:
        print("No triples were extracted from the raw texts.")
        return

    df = df.drop_duplicates(subset=["head", "relation", "tail"])
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")

    print("Knowledge extraction finished.")
    print(f"Extracted triples: {len(df)}")
    print(f"Output file: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
