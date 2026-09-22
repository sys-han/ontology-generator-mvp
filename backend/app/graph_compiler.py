from __future__ import annotations

from .models import OntologyIR


def _escape_identifier(name: str) -> str:
    return name.replace("`", "``")


def compile_schema_plan(ontology: OntologyIR) -> list[str]:
    statements: list[str] = []

    for entity in ontology.entity_types:
        escaped = _escape_identifier(entity.name)
        statements.append(
            f"// Entity {entity.name}\n"
            f"MERGE (n:`{escaped}` {{id: $id}})\n"
            f"SET n += $properties;"
        )

    for rel in ontology.relationship_types:
        source = _escape_identifier(rel.source)
        target = _escape_identifier(rel.target)
        name = _escape_identifier(rel.name)

        statements.append(
            f"// Relationship {rel.source} -[{rel.name}]-> {rel.target}\n"
            f"MATCH (a:`{source}` {{id: $source_id}}), "
            f"(b:`{target}` {{id: $target_id}})\n"
            f"MERGE (a)-[:`{name}`]->(b);"
        )

    return statements
