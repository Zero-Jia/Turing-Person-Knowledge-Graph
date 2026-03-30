# 🧠 图灵人物知识图谱（轻量级实现）

## 📌 项目简介

本项目为《知识工程》课程作业，旨在构建一个以计算机科学先驱 **阿兰·图灵（Alan Turing）** 为核心的知识图谱系统。

通过对图灵的生平经历、学术成果、相关机构及奖项等信息进行结构化建模，将原始数据转化为知识，并以图结构形式进行组织和展示，实现基础的知识查询与可视化分析。

本项目采用轻量级实现方式，重点在于体现知识图谱的核心流程：
**知识建模 → 数据获取 → 三元组构建 → 图数据库存储 → 查询与应用**

---

## 🎯 项目目标

* 构建一个结构清晰的小型知识图谱
* 掌握知识图谱的基本构建流程
* 实现实体关系的结构化表达（三元组）
* 支持基于图数据库的查询与可视化展示
* 理解知识图谱在人工智能中的应用方式

---

## 🧱 知识图谱设计

### 1️⃣ 实体类型（Entities）

本项目定义了以下几类核心实体：

| 实体类型         | 说明                         |
| ------------ | -------------------------- |
| Person       | 人物（如：Alan Turing）          |
| Organization | 机构（如：Cambridge University） |
| Theory       | 理论/成果（如：Turing Machine）    |
| Award        | 奖项（如：Turing Award）         |
| Place        | 地点（如：London）               |

---

### 2️⃣ 关系类型（Relations）

定义的主要关系如下：

| 关系类型       | 含义  |
| ---------- | --- |
| BORN_IN    | 出生于 |
| STUDIED_AT | 就读于 |
| WORKED_AT  | 工作于 |
| PROPOSED   | 提出  |
| RELATED_TO | 相关  |
| AWARDED    | 获得  |
| LOCATED_IN | 位于  |
| INFLUENCED | 影响  |

---

### 3️⃣ 三元组示例（Triples）

知识图谱采用三元组形式表示：

```
(Alan Turing, BORN_IN, London)
(Alan Turing, STUDIED_AT, Cambridge University)
(Alan Turing, PROPOSED, Turing Machine)
(Turing Award, RELATED_TO, Alan Turing)
```

---

## 📊 数据来源

本项目数据主要来源于公开知识资源：

* Wikipedia（维基百科）
* 百度百科
* 图灵奖相关介绍资料
* 计算机发展史资料

采用人工整理方式构建数据集，保证数据准确性与可控性。

---

## ⚙️ 技术方案

本项目采用轻量级技术实现：

* 🐍 Python：数据整理与处理
* 🗂 CSV：存储实体与关系数据
* 🧠 Neo4j：图数据库构建与查询
* 🔍 Cypher：图查询语言

---

## 🗄 数据结构

项目核心数据包括：

### entities.csv（实体表）

```
id,name,type
1,Alan Turing,Person
2,London,Place
3,Cambridge University,Organization
4,Turing Machine,Theory
```

### relations.csv（关系表）

```
start,end,relation
Alan Turing,London,BORN_IN
Alan Turing,Cambridge University,STUDIED_AT
Alan Turing,Turing Machine,PROPOSED
```

---

## 🚀 知识图谱构建

通过 Neo4j 导入 CSV 数据，构建图结构：

* 节点（Nodes）：表示实体
* 边（Edges）：表示关系

实现从结构化数据到图结构知识表示的转化。

---

## 🔎 查询示例

### 查询1：图灵的所有关系

```cypher
MATCH (a {name:"Alan Turing"})-[r]->(b)
RETURN a,r,b
```

---

### 查询2：图灵提出的理论

```cypher
MATCH (a {name:"Alan Turing"})-[:PROPOSED]->(b)
RETURN b
```

---

### 查询3：图灵相关机构

```cypher
MATCH (a {name:"Alan Turing"})-[:STUDIED_AT|WORKED_AT]->(b)
RETURN b
```

---

### 查询4：图灵影响的对象

```cypher
MATCH (a {name:"Alan Turing"})-[:INFLUENCED]->(b)
RETURN b
```

---

## 📈 项目成果

* 构建了一个小型知识图谱（数十个实体、数百条关系）
* 实现了基于图数据库的查询功能
* 支持图谱可视化展示
* 完成从数据到知识的转化过程

---

## 📚 理论基础

本项目基于知识图谱的核心思想：

* 知识以**三元组（Subject-Predicate-Object）**形式表示
* 实体作为节点，关系作为边构成图结构
* 可映射到 RDF（资源描述框架）模型
* 属于语义网（Semantic Web）的重要应用


