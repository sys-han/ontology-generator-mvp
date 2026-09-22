from __future__ import annotations

import os

from dotenv import load_dotenv
from neo4j import GraphDatabase


load_dotenv()


def is_neo4j_configured() -> bool:
    return bool(
        os.getenv("NEO4J_URI")
        and os.getenv("NEO4J_USERNAME")
        and os.getenv("NEO4J_PASSWORD")
    )


def get_driver():
    if not is_neo4j_configured():
        raise RuntimeError(
            "Neo4j is not configured. Add NEO4J_URI, NEO4J_USERNAME, "
            "and NEO4J_PASSWORD to backend/.env."
        )

    return GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(
            os.environ["NEO4J_USERNAME"],
            os.environ["NEO4J_PASSWORD"],
        ),
    )


def verify_neo4j() -> None:
    with get_driver() as driver:
        driver.verify_connectivity()
