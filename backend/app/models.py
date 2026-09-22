from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field, model_validator


ScalarType = Literal["string", "integer", "float", "boolean", "datetime"]


class EntityProperty(BaseModel):
    name: str = Field(min_length=1)
    type: ScalarType = "string"
    required: bool = False
    description: str | None = None


class EntityType(BaseModel):
    name: str = Field(min_length=1)
    description: str = ""
    properties: list[EntityProperty] = Field(default_factory=list)


class RelationshipType(BaseModel):
    name: str = Field(min_length=1)
    source: str = Field(min_length=1)
    target: str = Field(min_length=1)
    description: str = ""


class SourceMapping(BaseModel):
    source: str = Field(min_length=1)
    entity: str = Field(min_length=1)
    id_column: str | None = None
    field_mappings: dict[str, str] = Field(default_factory=dict)


class RelationshipMapping(BaseModel):
    relationship: str = Field(min_length=1)
    source_file: str = Field(min_length=1)
    source_entity: str = Field(min_length=1)
    source_id_column: str = Field(min_length=1)
    target_entity: str = Field(min_length=1)
    target_id_column: str = Field(min_length=1)


class OntologyIR(BaseModel):
    entity_types: list[EntityType]
    relationship_types: list[RelationshipType]
    source_mappings: list[SourceMapping]
    relationship_mappings: list[RelationshipMapping] = Field(default_factory=list)
    objective: str | None = None
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_references(self):
        entity_names = [e.name for e in self.entity_types]
        entity_set = set(entity_names)

        if len(entity_names) != len(entity_set):
            raise ValueError("Entity names must be unique.")

        relationship_names = [r.name for r in self.relationship_types]
        relationship_set = set(relationship_names)

        if len(relationship_names) != len(relationship_set):
            raise ValueError(
                "Relationship names must be unique so materialization is unambiguous."
            )

        relationship_lookup = {r.name: r for r in self.relationship_types}
        source_files = {m.source for m in self.source_mappings}

        for rel in self.relationship_types:
            if rel.source not in entity_set:
                raise ValueError(
                    f"Relationship {rel.name} references unknown source entity {rel.source!r}."
                )
            if rel.target not in entity_set:
                raise ValueError(
                    f"Relationship {rel.name} references unknown target entity {rel.target!r}."
                )

        for mapping in self.source_mappings:
            if mapping.entity not in entity_set:
                raise ValueError(
                    f"Source mapping references unknown entity {mapping.entity!r}."
                )
            if not mapping.id_column:
                raise ValueError(
                    f"Source mapping for {mapping.entity!r} must provide id_column."
                )

        for mapping in self.relationship_mappings:
            if mapping.relationship not in relationship_set:
                raise ValueError(
                    f"Relationship mapping references unknown relationship {mapping.relationship!r}."
                )

            rel = relationship_lookup[mapping.relationship]

            if mapping.source_entity != rel.source:
                raise ValueError(
                    f"Relationship mapping {mapping.relationship!r} source_entity "
                    f"{mapping.source_entity!r} does not match relationship source {rel.source!r}."
                )

            if mapping.target_entity != rel.target:
                raise ValueError(
                    f"Relationship mapping {mapping.relationship!r} target_entity "
                    f"{mapping.target_entity!r} does not match relationship target {rel.target!r}."
                )

            if mapping.source_file not in source_files:
                raise ValueError(
                    f"Relationship mapping {mapping.relationship!r} uses source file "
                    f"{mapping.source_file!r}, but that file does not appear in source_mappings."
                )

        # Every relationship must be executable, not merely described in prose.
        mapped_relationships = {m.relationship for m in self.relationship_mappings}
        missing = relationship_set - mapped_relationships
        if missing:
            raise ValueError(
                "Every relationship type needs a relationship_mapping. "
                f"Missing mappings for: {sorted(missing)}"
            )

        return self


class GenerateResponse(BaseModel):
    ontology: OntologyIR
    profiles: list[dict]
    provider: Literal["k2", "heuristic"]
    warnings: list[str] = Field(default_factory=list)


class CompileRequest(BaseModel):
    ontology: OntologyIR


class CompileResponse(BaseModel):
    statements: list[str]


class BuildGraphResponse(BaseModel):
    ok: bool
    entity_records_materialized: int
    relationship_records_materialized: int
    nodes_created: int
    relationships_created: int
    skipped_records: int
    message: str


class GraphPreviewNode(BaseModel):
    id: str
    labels: list[str]
    properties: dict = Field(default_factory=dict)


class GraphPreviewEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str
    properties: dict = Field(default_factory=dict)


class GraphPreviewResponse(BaseModel):
    nodes: list[GraphPreviewNode]
    edges: list[GraphPreviewEdge]
    node_count: int
    relationship_count: int
