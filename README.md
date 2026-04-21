# Turing Person Knowledge Graph

一个基于 Python + CSV + Neo4j 的课程项目，主题是“图灵人物知识图谱”。  
当前版本在原有手工整理数据的基础上，新增了自动知识抽取、实体类型归一、轻量实体消歧、三元组构建与 Neo4j 写入能力。

## 项目目标

- 保留原有 `CSV -> Neo4j` 图谱构建流程
- 支持从自然语言文本中自动抽取知识
- 对抽取出的实体进行类型映射和语义消歧
- 将结果构建为限定关系集合内的三元组
- 使用 `MERGE` 写入 Neo4j，避免重复数据

## 知识图谱模式

### 实体类型

| 类型 | 说明 | 示例 |
| --- | --- | --- |
| Person | 人物 | Alan Turing |
| Organization | 机构 | University of Cambridge |
| Theory | 理论 / 成果 | Turing Machine |
| Award | 奖项 | Turing Award |
| Place | 地点 | London |

### 关系类型

仅允许以下关系类型：

- `BORN_IN`
- `STUDIED_AT`
- `WORKED_AT`
- `PROPOSED`
- `RELATED_TO`
- `AWARDED`
- `LOCATED_IN`
- `INFLUENCED`

### 三元组示例

```text
(Alan Turing, BORN_IN, London)
(Alan Turing, STUDIED_AT, University of Cambridge)
(Alan Turing, PROPOSED, Turing Machine)
```

## 当前实现的整体流程

输入文本后，系统按以下流程处理：

```text
输入文本
-> 实体识别（NER）
-> 实体类型归一
-> 实体消歧（Entity Linking）
-> 关系抽取（限定关系类型）
-> 三元组构建
-> 追加写入 CSV
-> 写入 Neo4j（可选）
```

## 项目结构

```text
Turing-Person-Knowledge-Graph/
├── app.py
├── README.md
├── requirements.txt
├── config/
│   ├── alias_map.json
│   └── relation_patterns.json
├── data/
│   ├── entities.csv
│   ├── entities_auto.csv
│   ├── relations.csv
│   ├── relations_auto.csv
│   ├── extracted_triples.csv
│   ├── normalized_triples.csv
│   └── raw_texts/
├── docs/
├── nlp/
│   ├── __init__.py
│   ├── ner.py
│   ├── entity_linking.py
│   ├── relation_extraction.py
│   └── pipeline.py
├── queries/
└── scripts/
    ├── clean_data.py
    ├── build_graph_csv.py
    ├── extract_knowledge.py
    ├── normalize_and_disambiguate.py
    └── import_to_neo4j.py
```

## 核心模块说明

### `nlp/ner.py`

负责实体识别与类型映射：

- 优先尝试使用 `spaCy`
- 如果本地没有安装 `spaCy` 或模型，则自动退化为规则识别
- 类型映射规则：
  - `PERSON -> Person`
  - `ORG -> Organization`
  - `GPE/LOC -> Place`
  - 包含 `Machine` / `Theory` / `Test` -> `Theory`
  - 包含 `Award` / `Prize` -> `Award`

### `nlp/entity_linking.py`

负责轻量实体消歧：

- 从 `entities.csv` 和 `entities_auto.csv` 中读取候选实体
- 结合 `config/alias_map.json` 做别名归一
- 使用轻量 TF-IDF 向量 + 余弦相似度选择最优候选
- 若相似度低于阈值，则创建新实体

统一方法：

```python
resolve_entity(mention, context) -> entity_name
```

### `nlp/relation_extraction.py`

负责关系抽取：

- 只抽取预定义关系类型
- 使用规则模板匹配句子中的关系表达
- 支持简单代词回指，例如 `He proposed ...`

### `nlp/pipeline.py`

统一入口：

```python
extract_kg_from_text(text: str)
```

该函数负责：

- 实体识别
- 实体消歧
- 关系抽取
- 三元组去重
- 自动 CSV 追加
- 可选写入 Neo4j

## 数据文件说明

### 手工数据

- `data/entities.csv`
- `data/relations.csv`

这两份文件代表原有人工整理的数据。

### 自动抽取数据

- `data/entities_auto.csv`
- `data/relations_auto.csv`

自动抽取结果会追加到这里，不会破坏原有手工数据。

### 抽取结果

- `data/extracted_triples.csv`

保存最新一次抽取出的三元组。

## Neo4j 写入规则

Neo4j 导入逻辑位于 `scripts/import_to_neo4j.py`，特点如下：

- 同时读取手工 CSV 和自动 CSV
- 节点使用 `MERGE`
- 关系使用真实关系类型，例如 `:BORN_IN`、`:PROPOSED`
- 节点属性包含：
  - `name`
  - `type`
  - `source`
- 若同名实体同时存在于手工数据和自动数据中，优先保留手工实体信息

## 安装依赖

推荐 Python 版本：`3.10+`

安装依赖：

```bash
pip install -r requirements.txt
```

如果你希望启用 `spaCy` NER，还需要下载模型：

```bash
python -m spacy download en_core_web_sm
```

## 如何运行

### 1. 从原始文本批量抽取知识

项目会读取 `data/raw_texts/` 下的 `.txt` 文件：

```bash
python scripts/extract_knowledge.py
```

执行后会更新：

- `data/extracted_triples.csv`
- `data/entities_auto.csv`
- `data/relations_auto.csv`

### 2. 导入 Neo4j

```bash
python scripts/import_to_neo4j.py
```

默认环境变量：

```text
NEO4J_URI=bolt://127.0.0.1:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=12345678
NEO4J_DATABASE=turning-kg
```

也可以通过环境变量覆盖：

```bash
set NEO4J_URI=bolt://127.0.0.1:7687
set NEO4J_USERNAME=neo4j
set NEO4J_PASSWORD=your_password
set NEO4J_DATABASE=neo4j
```

### 3. 启动 API

```bash
python app.py
```

服务启动后可访问：

```text
POST http://127.0.0.1:5000/extract
```

## API 说明

### `POST /extract`

请求体：

```json
{
  "text": "Alan Turing was born in London and studied at Cambridge University. He proposed the Turing Machine."
}
```

返回示例：

```json
{
  "entities": [
    {
      "name": "Alan Turing",
      "type": "Person",
      "source": "manual"
    },
    {
      "name": "London",
      "type": "Place",
      "source": "manual"
    },
    {
      "name": "University of Cambridge",
      "type": "Organization",
      "source": "manual"
    },
    {
      "name": "Turing Machine",
      "type": "Theory",
      "source": "manual"
    }
  ],
  "triples": [
    ["Alan Turing", "BORN_IN", "London"],
    ["Alan Turing", "PROPOSED", "Turing Machine"],
    ["Alan Turing", "STUDIED_AT", "University of Cambridge"]
  ],
  "neo4j_written": true
}
```

## Python 调用示例

```python
from nlp.pipeline import extract_kg_from_text

text = (
    "Alan Turing was born in London and studied at Cambridge University. "
    "He proposed the Turing Machine."
)

result = extract_kg_from_text(text, persist=True, write_neo4j=False)

print(result["entities"])
print(result["triples"])
```

## 测试示例文本

你可以直接使用下面这段文本测试：

```text
Alan Turing was born in London and studied at Cambridge University.
He proposed the Turing Machine.
```

预期抽取结果：

实体：

- `Alan Turing` -> `Person`
- `London` -> `Place`
- `University of Cambridge` -> `Organization`
- `Turing Machine` -> `Theory`

三元组：

- `(Alan Turing, BORN_IN, London)`
- `(Alan Turing, STUDIED_AT, University of Cambridge)`
- `(Alan Turing, PROPOSED, Turing Machine)`

## 常用 Cypher 查询

查询 Alan Turing 的全部关系：

```cypher
MATCH (a:Entity {name: "Alan Turing"})-[r]->(b)
RETURN a, r, b
```

查询 Alan Turing 提出的理论：

```cypher
MATCH (:Entity {name: "Alan Turing"})-[:PROPOSED]->(b)
RETURN b
```

查询 Alan Turing 的教育和工作机构：

```cypher
MATCH (:Entity {name: "Alan Turing"})-[:STUDIED_AT|WORKED_AT]->(b)
RETURN b
```

查询机构所在地点：

```cypher
MATCH (a:Entity)-[:LOCATED_IN]->(b:Entity)
RETURN a.name, b.name
```

## 已完成的增强点

- 保留原有 CSV 与 Neo4j 项目结构
- 新增自动知识抽取流水线
- 新增轻量实体消歧
- 新增自动 CSV 追加逻辑
- Neo4j 导入改为 `MERGE` 去重
- Neo4j 节点新增 `source` 属性
- 新增 `POST /extract` API

## 注意事项

- 当前关系抽取基于规则模板，不是深度学习关系抽取模型
- 当前实体消歧为轻量实现，适合课程项目和中小规模示例
- 若未安装 `spaCy`，项目仍可运行，但 NER 会退化为规则识别
- 若未安装 `neo4j` Python 驱动，文本抽取和 CSV 生成仍可运行，但不会写入 Neo4j

## 后续可扩展方向

- 接入 `sentence-transformers` 做更强的实体链接
- 增加中文 NER 模型
- 增加更多关系模板
- 支持批量 API 调用
- 增加前端图谱可视化页面
