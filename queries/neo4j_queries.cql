// =====================================
// 图灵人物知识图谱查询语句
// Day 5: 查询与展示
// =====================================


// 1. 查看图谱中的所有节点和关系（总览）
MATCH (a)-[r]->(b)
RETURN a, r, b
LIMIT 50;


// 2. 查询 Alan Turing 的所有直接关系
MATCH (a:Entity {name: "Alan Turing"})-[r]->(b)
RETURN a, r, b;


// 3. 查询 Alan Turing 提出的成果
MATCH (a:Entity {name: "Alan Turing"})-[r:RELATION]->(b)
WHERE r.type = "PROPOSED"
RETURN a, r, b;


// 4. 查询 Alan Turing 的学习和工作机构
MATCH (a:Entity {name: "Alan Turing"})-[r:RELATION]->(b)
WHERE r.type IN ["STUDIED_AT", "WORKED_AT"]
RETURN a, r, b;


// 5. 查询 Alan Turing 影响到的领域/理论
MATCH (a:Entity {name: "Alan Turing"})-[r:RELATION]->(b)
WHERE r.type = "INFLUENCED"
RETURN a, r, b;


// 6. 查询所有机构所在地点
MATCH (a:Entity)-[r:RELATION]->(b:Entity)
WHERE r.type = "LOCATED_IN"
RETURN a, r, b;


// 7. 查询与 Artificial Intelligence 相关的人物或实体
MATCH (a)-[r]->(b:Entity {name: "Artificial Intelligence"})
RETURN a, r, b;