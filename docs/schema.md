# 图灵人物知识图谱模式设计

## 1. 项目主题
本项目为《知识工程》课程作业，围绕阿兰·图灵（Alan Turing）构建一个轻量级人物知识图谱，用于展示图灵的生平经历、教育背景、工作机构、学术成果、相关奖项及其影响。

## 2. 项目目标
- 将图灵相关信息进行结构化表示
- 使用三元组形式组织实体与关系
- 为后续图数据库导入和查询打下基础
- 实现一个小型、清晰、可展示的知识图谱课程作业

## 3. 实体类型设计
本项目定义以下实体类型：

### 3.1 Person（人物）
表示与图灵相关的重要人物。
示例：
- Alan Turing
- Alonzo Church
- John von Neumann
- Claude Shannon
- Marvin Minsky

### 3.2 Organization（机构）
表示学校、研究机构、工作单位等。
示例：
- University of Cambridge
- Princeton University
- University of Manchester
- Bletchley Park

### 3.3 Theory（理论/成果）
表示图灵提出或相关的重要理论成果。
示例：
- Turing Machine
- Turing Test
- Computability Theory
- Artificial Intelligence

### 3.4 Award（奖项）
表示与图灵相关的奖项。
示例：
- Turing Award

### 3.5 Place（地点）
表示人物出生地、机构所在地等。
示例：
- London
- Maida Vale
- Cambridge
- Manchester

## 4. 关系类型设计
本项目定义以下关系类型：

### 4.1 BORN_IN
表示人物出生于某地点。
示例：
- (Alan Turing, BORN_IN, London)

### 4.2 STUDIED_AT
表示人物曾在某机构学习。
示例：
- (Alan Turing, STUDIED_AT, University of Cambridge)

### 4.3 WORKED_AT
表示人物曾在某机构工作。
示例：
- (Alan Turing, WORKED_AT, University of Manchester)

### 4.4 PROPOSED
表示人物提出了某个理论或成果。
示例：
- (Alan Turing, PROPOSED, Turing Machine)

### 4.5 RELATED_TO
表示两个实体之间存在关联。
示例：
- (Turing Award, RELATED_TO, Alan Turing)

### 4.6 INFLUENCED
表示某人物影响了某个理论、领域或对象。
示例：
- (Alan Turing, INFLUENCED, Artificial Intelligence)

### 4.7 LOCATED_IN
表示某机构位于某地点。
示例：
- (University of Cambridge, LOCATED_IN, Cambridge)

### 4.8 AWARDED
表示某人物获得某奖项。
说明：本项目中可以预留该关系，但未必第一版立即使用。

## 5. 三元组表示示例
知识图谱中的知识采用三元组形式表示：

- (Alan Turing, BORN_IN, London)
- (Alan Turing, STUDIED_AT, University of Cambridge)
- (Alan Turing, WORKED_AT, Bletchley Park)
- (Alan Turing, PROPOSED, Turing Test)
- (Turing Award, RELATED_TO, Alan Turing)

## 6. 项目范围说明
本项目为课程作业，采用轻量级实现方案，不追求大规模自动化抽取，而采用“人工整理 + Python清洗 + Neo4j导入”的方式完成一个小型知识图谱系统。

## 7. 后续开发计划
后续将依次完成以下内容：
1. 整理实体数据和关系数据
2. 使用 Python 脚本进行数据清洗
3. 将数据导入 Neo4j
4. 实现基础查询与图谱展示
5. 完成项目报告与结果整理