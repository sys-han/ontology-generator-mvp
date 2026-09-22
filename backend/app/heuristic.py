from __future__ import annotations

import re
from pathlib import Path

from .models import (
    EntityProperty,
    EntityType,
    OntologyIR,
    RelationshipMapping,
    RelationshipType,
    SourceMapping,
)


def _singular(word: str) -> str:
    lower = word.lower()
    if lower.endswith("ies") and len(word) > 3:
        return word[:-3] + "y"
    if lower.endswith("sses"):
        return word[:-2]
    if lower.endswith("s") and not lower.endswith("ss"):
        return word[:-1]
    return word


def _pascal(text: str) -> str:
    parts = re.split(r"[^A-Za-z0-9]+", text)
    return "".join(p[:1].upper() + p[1:] for p in parts if p) or "Entity"


def _entity_name_from_source(source: str) -> str:
    stem = Path(source).stem
    return _pascal(_singular(stem))


def _property_type(profile_type: str) -> str:
    return (
        profile_type
        if profile_type in {"string", "integer", "float", "boolean", "datetime"}
        else "string"
    )


def _guess_id_column(entity_name: str, columns: list[str]) -> str | None:
    lower_map = {c.lower(): c for c in columns}
    candidates = [
        "id",
        f"{entity_name.lower()}_id",
        f"{_singular(entity_name).lower()}_id",
    ]
    for candidate in candidates:
        if candidate in lower_map:
            return lower_map[candidate]

    for column in columns:
        if column.lower().endswith("_id"):
            return column
    return None


def generate_heuristic_ontology(objective: str, profiles: list[dict]) -> OntologyIR:
    entities: list[EntityType] = []
    mappings: list[SourceMapping] = []
    relationships: list[RelationshipType] = []
    relationship_mappings: list[RelationshipMapping] = []

    source_to_entity: dict[str, str] = {}
    entity_to_id: dict[str, str | None] = {}
    token_to_entity: dict[str, str] = {}

    for profile in profiles:
        source = profile["source"]
        entity_name = _entity_name_from_source(source)
        source_to_entity[source] = entity_name

        columns = list(profile["columns"].keys())
        id_column = _guess_id_column(entity_name, columns)
        entity_to_id[entity_name] = id_column

        properties = []
        for column, meta in profile["columns"].items():
            properties.append(
                EntityProperty(
                    name=column,
                    type=_property_type(meta.get("type", "string")),
                    required=not meta.get("nullable", True),
                )
            )

        entities.append(
            EntityType(
                name=entity_name,
                description=f"Canonical concept inferred from {source}.",
                properties=properties,
            )
        )

        field_mappings = {column: column for column in columns}
        mappings.append(
            SourceMapping(
                source=source,
                entity=entity_name,
                id_column=id_column,
                field_mappings=field_mappings,
            )
        )

        stem = Path(source).stem.lower()
        variants = {
            stem,
            _singular(stem),
            entity_name.lower(),
            _singular(entity_name.lower()),
        }
        for token in variants:
            token_to_entity[token] = entity_name

    seen = set()

    for profile in profiles:
        source = profile["source"]
        source_entity = source_to_entity[source]
        source_entity_id = entity_to_id[source_entity]

        if not source_entity_id:
            continue

        for column in profile["columns"].keys():
            low = column.lower()
            if not low.endswith("_id"):
                continue

            token = low[:-3]
            target = token_to_entity.get(token)

            if target is None:
                for candidate_token, candidate_entity in sorted(
                    token_to_entity.items(),
                    key=lambda item: len(item[0]),
                    reverse=True,
                ):
                    if token.endswith(candidate_token):
                        target = candidate_entity
                        break

            if target is None or target == source_entity:
                continue

            target_id = entity_to_id.get(target)
            if not target_id:
                continue

            # A foreign key on the current row points FROM the current entity
            # TO the referenced target entity.
            role = re.sub(r"[^A-Za-z0-9]+", "_", token).upper()
            rel_name = role if role else "REFERENCES"
            key = (rel_name, source_entity, target)

            if key in seen:
                continue
            seen.add(key)

            relationships.append(
                RelationshipType(
                    name=rel_name,
                    source=source_entity,
                    target=target,
                    description=f"Inferred from {source}.{column}.",
                )
            )

            relationship_mappings.append(
                RelationshipMapping(
                    relationship=rel_name,
                    source_file=source,
                    source_entity=source_entity,
                    source_id_column=source_entity_id,
                    target_entity=target,
                    target_id_column=column,
                )
            )

    notes = [
        "Generated by the local heuristic fallback.",
        "Configure K2 to use semantic ontology induction.",
    ]

    return OntologyIR(
        entity_types=entities,
        relationship_types=relationships,
        source_mappings=mappings,
        relationship_mappings=relationship_mappings,
        objective=objective,
        notes=notes,
    )
