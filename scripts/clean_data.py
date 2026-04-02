import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

entities_path = DATA_DIR / "entities.csv"
relations_path = DATA_DIR / "relations.csv"

entities_clean_path = DATA_DIR / "entities_clean.csv"
relations_clean_path = DATA_DIR / "relations_clean.csv"

entities = pd.read_csv(entities_path)
relations = pd.read_csv(relations_path)

print("=== 原始数据统计 ===")
print(f"原始实体数: {len(entities)}")
print(f"原始关系数: {len(relations)}")
print()

# 去重
entities = entities.drop_duplicates()
relations = relations.drop_duplicates()
# 去空值
entities = entities.dropna()
relations = relations.dropna()

# 去掉字段前后空格
entities["name"] = entities["name"].astype(str).str.strip()
entities["type"] = entities["type"].astype(str).str.strip()

relations["start"] = relations["start"].astype(str).str.strip()
relations["end"] = relations["end"].astype(str).str.strip()
relations["relation"] = relations["relation"].astype(str).str.strip()

# 再次去重（防止 strip 后重复）
entities = entities.drop_duplicates()
relations = relations.drop_duplicates()

entities.to_csv(entities_clean_path, index=False, encoding="utf-8")
relations.to_csv(relations_clean_path, index=False, encoding="utf-8")

print("=== 清洗后数据统计 ===")
print(f"清洗后实体数: {len(entities)}")
print(f"清洗后关系数: {len(relations)}")
print()
print("数据清洗完成！")