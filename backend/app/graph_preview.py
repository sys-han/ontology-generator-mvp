from __future__ import annotations

from .neo4j_client import get_driver


def read_graph_preview(
    node_limit: int = 200,
    relationship_limit: int = 300,
) -> dict:
    node_limit = max(1, min(node_limit, 500))
    relationship_limit = max(1, min(relationship_limit, 1000))

    with get_driver() as driver:
        node_result = driver.execute_query(
            """
            MATCH (n)
            RETURN
              elementId(n) AS id,
              labels(n) AS labels,
              properties(n) AS properties
            LIMIT $limit
            """,
            limit=node_limit,
            database_=None,
        )

        rel_result = driver.execute_query(
            """
            MATCH (a)-[r]->(b)
            RETURN
              elementId(r) AS id,
              elementId(a) AS source,
              elementId(b) AS target,
              type(r) AS type,
              properties(r) AS properties
            LIMIT $limit
            """,
            limit=relationship_limit,
            database_=None,
        )

    nodes = []
    allowed_node_ids = set()

    for record in node_result.records:
        node_id = record["id"]
        allowed_node_ids.add(node_id)
        nodes.append(
            {
                "id": node_id,
                "labels": list(record["labels"] or []),
                "properties": dict(record["properties"] or {}),
            }
        )

    edges = []
    for record in rel_result.records:
        source = record["source"]
        target = record["target"]

        # Keep the preview internally consistent if the node limit is hit.
        if source not in allowed_node_ids or target not in allowed_node_ids:
            continue

        edges.append(
            {
                "id": record["id"],
                "source": source,
                "target": target,
                "type": record["type"],
                "properties": dict(record["properties"] or {}),
            }
        )

    return {
        "nodes": nodes,
        "edges": edges,
        "node_count": len(nodes),
        "relationship_count": len(edges),
    }
