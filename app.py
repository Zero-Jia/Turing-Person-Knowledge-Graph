from __future__ import annotations

import os

from flask import Flask, jsonify, request
from neo4j import GraphDatabase

from nlp.pipeline import extract_kg_from_text

app = Flask(__name__)

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "12345678")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "turning-kg")


def get_neo4j_driver():
    return GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
    )


@app.post("/extract")
def extract():
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()
    if not text:
        return jsonify({"error": "text is required"}), 400

    result = extract_kg_from_text(text, persist=True, write_neo4j=True)
    response = {
        "entities": result["entities"],
        "triples": result["triples"],
        "neo4j_written": result["neo4j_written"],
    }
    if result["neo4j_error"]:
        response["warning"] = result["neo4j_error"]
    return jsonify(response)


@app.get("/api/graph")
def get_graph():
    try:
        driver = get_neo4j_driver()
        try:
            with driver.session(database=NEO4J_DATABASE) as session:
                nodes_result = session.run(
                    """
                    MATCH (n)
                    RETURN collect({
                        id: toString(coalesce(n.id, elementId(n))),
                        label: coalesce(n.name, head(labels(n)), elementId(n)),
                        type: coalesce(n.type, head(labels(n)), "Unknown"),
                        properties: properties(n)
                    }) AS nodes
                    """
                ).single()

                edges_result = session.run(
                    """
                    MATCH (source)-[r]->(target)
                    RETURN collect({
                        source: toString(coalesce(source.id, elementId(source))),
                        target: toString(coalesce(target.id, elementId(target))),
                        label: type(r)
                    }) AS edges
                    """
                ).single()

                return jsonify(
                    {
                        "nodes": nodes_result["nodes"] if nodes_result else [],
                        "edges": edges_result["edges"] if edges_result else [],
                    }
                )
        finally:
            driver.close()
    except Exception as exc:
        return jsonify({"error": f"Failed to load graph data: {exc}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
