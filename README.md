# Turing Person Knowledge Graph

一个围绕 Alan Turing（阿兰·图灵）人物知识构建的轻量级知识图谱项目。项目包含 Python 后端、NLP 抽取流程、CSV 数据层、Neo4j 图数据库导入，以及基于 Vue + Cytoscape 的前端可视化页面。

## 项目简介

本项目的目标是把图灵相关的人物、机构、地点、理论成果和奖项整理成结构化知识，并以三元组形式写入 Neo4j，最后通过 Web 页面展示知识图谱。

当前实现同时支持两类数据来源：

- 手工整理的 CSV 数据：`data/entities.csv`、`data/relations.csv`
- 从原始文本自动抽取的数据：`data/raw_texts/*.txt` -> `data/entities_auto.csv`、`data/relations_auto.csv`

## 功能特性

- 使用 CSV 管理实体和关系数据。
- 从英文自然语言文本中识别实体并抽取关系。
- 支持实体别名归一和轻量级实体消歧。
- 将手工数据和自动抽取数据合并导入 Neo4j。
- 使用 `MERGE` 写入节点和关系，减少重复数据。
- 提供 Flask API：
  - `POST /extract`：从输入文本抽取知识并可写入 Neo4j。
  - `GET /api/graph`：从 Neo4j 读取图谱数据。
- 提供 Vue 前端，用 Cytoscape 展示节点、关系、图例和节点详情。

## 技术栈

后端与数据处理：

- Python 3.10+
- Flask
- pandas
- neo4j Python Driver
- spaCy（可选，用于增强 NER；未安装模型时会退化为规则识别）

前端：

- Vue 3
- Vue Router
- Vite
- Axios
- Cytoscape

图数据库：

- Neo4j 5.x

## 知识图谱模式

### 实体类型

| 类型 | 说明 | 示例 |
| --- | --- | --- |
| `Person` | 人物 | Alan Turing |
| `Organization` | 学校、研究机构、工作单位 | University of Cambridge |
| `Theory` | 理论、成果、领域 | Turing Machine |
| `Award` | 奖项 | Turing Award |
| `Place` | 地点 | London |

### 关系类型

| 关系 | 说明 | 示例 |
| --- | --- | --- |
| `BORN_IN` | 出生于 | `(Alan Turing, BORN_IN, London)` |
| `STUDIED_AT` | 就读于 | `(Alan Turing, STUDIED_AT, University of Cambridge)` |
| `WORKED_AT` | 工作于 | `(Alan Turing, WORKED_AT, Bletchley Park)` |
| `PROPOSED` | 提出理论或成果 | `(Alan Turing, PROPOSED, Turing Machine)` |
| `RELATED_TO` | 相关 | `(Turing Award, RELATED_TO, Alan Turing)` |
| `AWARDED` | 获得奖项 | `(Person, AWARDED, Award)` |
| `LOCATED_IN` | 位于 | `(University of Cambridge, LOCATED_IN, Cambridge)` |
| `INFLUENCED` | 影响 | `(Alan Turing, INFLUENCED, Artificial Intelligence)` |

## 项目结构

```text
Turing-Person-Knowledge-Graph/
├── app.py                         # Flask API 服务
├── requirements.txt               # Python 依赖
├── README.md
├── config/
│   ├── alias_map.json             # 实体别名映射
│   └── relation_patterns.json     # 关系抽取规则配置
├── data/
│   ├── entities.csv               # 手工实体数据
│   ├── relations.csv              # 手工关系数据
│   ├── entities_auto.csv          # 自动抽取实体数据
│   ├── relations_auto.csv         # 自动抽取关系数据
│   ├── extracted_triples.csv      # 最近抽取出的三元组
│   ├── normalized_triples.csv     # 归一化三元组
│   └── raw_texts/                 # 原始文本语料
├── docs/
│   └── schema.md                  # 图谱模式说明
├── nlp/
│   ├── ner.py                     # 实体识别
│   ├── entity_linking.py          # 实体链接与消歧
│   ├── relation_extraction.py     # 关系抽取
│   └── pipeline.py                # 抽取流程入口
├── queries/
│   └── neo4j_queries.cql          # 示例 Cypher 查询
├── scripts/
│   ├── clean_data.py              # CSV 清洗脚本
│   ├── build_graph_csv.py         # 从三元组构建图谱 CSV
│   ├── extract_knowledge.py       # 批量文本抽取脚本
│   ├── normalize_and_disambiguate.py
│   └── import_to_neo4j.py         # Neo4j 导入脚本
└── frontend/
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── api/graph.js
        ├── views/KnowledgeGraphView.vue
        └── components/KnowledgeGraph.vue
```

## 处理流程

自动抽取流程位于 `nlp/pipeline.py`，主入口为：

```python
extract_kg_from_text(text: str, persist: bool = True, write_neo4j: bool = True)
```

整体流程：

```text
输入文本
-> 句子切分
-> 实体识别
-> 实体类型推断
-> 实体链接与别名归一
-> 规则关系抽取
-> 三元组去重
-> 写入自动 CSV
-> 可选写入 Neo4j
```

## 安装依赖

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

如果希望启用 spaCy 模型增强实体识别，可以额外安装英文模型：

```bash
python -m spacy download en_core_web_sm
```

### 2. 安装前端依赖

```bash
cd frontend
npm install
```

## Neo4j 配置

后端和导入脚本默认使用以下环境变量：

```text
NEO4J_URI=bolt://127.0.0.1:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=12345678
NEO4J_DATABASE=turning-kg
```

可以根据本地 Neo4j 实例修改环境变量。

Windows PowerShell 示例：

```powershell
$env:NEO4J_URI="bolt://127.0.0.1:7687"
$env:NEO4J_USERNAME="neo4j"
$env:NEO4J_PASSWORD="your_password"
$env:NEO4J_DATABASE="neo4j"
```

macOS / Linux 示例：

```bash
export NEO4J_URI=bolt://127.0.0.1:7687
export NEO4J_USERNAME=neo4j
export NEO4J_PASSWORD=your_password
export NEO4J_DATABASE=neo4j
```

## 运行项目

### 1. 从原始文本批量抽取知识

脚本会读取 `data/raw_texts/` 下的 `.txt` 文件：

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

脚本会读取手工 CSV 和自动 CSV，并询问是否清空已有图数据后再导入。

默认导入文件：

- 实体：`data/entities.csv`、`data/entities_auto.csv`
- 关系：`data/relations.csv`、`data/relations_auto.csv`

也可以通过环境变量覆盖：

```bash
ENTITY_CSV_FILES=data/entities.csv,data/entities_auto.csv
RELATION_CSV_FILES=data/relations.csv,data/relations_auto.csv
```

### 3. 启动后端 API

```bash
python app.py
```

默认地址：

```text
http://127.0.0.1:5000
```

### 4. 启动前端页面

```bash
cd frontend
npm run dev
```

默认地址：

```text
http://127.0.0.1:5173
```

如果前端和后端不在同一地址，可以设置：

```bash
VITE_API_BASE_URL=http://127.0.0.1:5000
```

## API 说明

### `POST /extract`

从请求文本中抽取实体和三元组，并尝试写入 Neo4j。

请求示例：

```bash
curl -X POST http://127.0.0.1:5000/extract \
  -H "Content-Type: application/json" \
  -d "{\"text\":\"Alan Turing was born in London. He proposed the Turing Machine.\"}"
```

响应字段：

- `entities`：抽取和归一后的实体列表。
- `triples`：三元组列表。
- `neo4j_written`：是否成功写入 Neo4j。
- `warning`：Neo4j 写入失败时的错误信息。

### `GET /api/graph`

从 Neo4j 读取前端可视化所需的节点和边。

响应示例：

```json
{
  "nodes": [
    {
      "id": "1",
      "label": "Alan Turing",
      "type": "Person",
      "properties": {
        "name": "Alan Turing",
        "type": "Person"
      }
    }
  ],
  "edges": [
    {
      "source": "1",
      "target": "2",
      "label": "BORN_IN"
    }
  ]
}
```

## 数据文件说明

| 文件 | 说明 |
| --- | --- |
| `data/entities.csv` | 手工维护的实体表 |
| `data/relations.csv` | 手工维护的关系表 |
| `data/entities_auto.csv` | 自动抽取生成的实体表 |
| `data/relations_auto.csv` | 自动抽取生成的关系表 |
| `data/extracted_triples.csv` | 最近一次抽取结果 |
| `data/normalized_triples.csv` | 归一化后的三元组数据 |
| `data/raw_texts/*.txt` | 用于抽取的原始文本 |

## 示例 Cypher 查询

查看所有关系：

```cypher
MATCH (a)-[r]->(b)
RETURN a, r, b
LIMIT 50;
```

查看 Alan Turing 的直接关系：

```cypher
MATCH (a:Entity {name: "Alan Turing"})-[r]->(b)
RETURN a, r, b;
```

查看 Alan Turing 提出的理论或成果：

```cypher
MATCH (a:Entity {name: "Alan Turing"})-[r:PROPOSED]->(b)
RETURN a, r, b;
```

## 开发备注

- `nlp/ner.py` 会优先尝试加载 spaCy 模型；如果不可用，会使用规则识别。
- `nlp/entity_linking.py` 会读取 `config/alias_map.json` 做别名归一，并用轻量 TF-IDF 相似度选择候选实体。
- `scripts/import_to_neo4j.py` 会创建 `Entity.name` 唯一约束，并按真实关系类型写入 Neo4j，例如 `:BORN_IN`、`:PROPOSED`。
- 前端图谱数据来自 `/api/graph`，节点颜色按 `type` 区分，点击节点可查看属性详情。
- 仓库中部分旧脚本和文档曾出现中文编码乱码；README 已整理为 UTF-8 中文版本。
