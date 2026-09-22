from __future__ import annotations

from io import BytesIO
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from .models import BuildGraphResponse, OntologyIR
from .neo4j_client import get_driver


def _read_dataframe(filename: str, raw: bytes) -> pd.DataFrame:
    suffix = Path(filename).suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(BytesIO(raw))

    if suffix == ".json":
        data = json.loads(raw.decode("utf-8"))

        if isinstance(data, list):
            return pd.DataFrame(data)

        if isinstance(data, dict):
            for key in ("records", "data", "items", "rows"):
                if isinstance(data.get(key), list):
                    return pd.DataFrame(data[key])
            return pd.DataFrame([data])

        raise ValueError("JSON must contain an object or an array of objects.")

    raise ValueError(f"Unsupported file type for {filename}. Use CSV or JSON.")


def _clean(value: Any) -> Any:
    if value is None:
        return None

    if hasattr(value, "item"):
        try:
            value = value.item()
        except Exception:
            pass

    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    return value


def _identifier(name: str) -> str:
    # Dynamic labels/types cannot be query parameters in Cypher.
    # Backtick escaping keeps the value data, not executable syntax.
    return name.replace("`", "``")


def _require_columns(
    df: pd.DataFrame,
    filename: str,
    columns: list[str],
) -> None:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ValueError(
            f"{filename} is missing columns required by the ontology: {missing}"
        )


def materialize_graph(
    ontology: OntologyIR,
    files: dict[str, bytes],
) -> BuildGraphResponse:
    frames = {
        filename: _read_dataframe(filename, raw)
        for filename, raw in files.items()
    }

    entity_records = 0
    relationship_records = 0
    nodes_created = 0
    relationships_created = 0
    skipped = 0

    with get_driver() as driver:
        # 1) Materialize entity nodes.
        for mapping in ontology.source_mappings:
            if mapping.source not in frames:
                raise ValueError(
                    f"Uploaded files do not include {mapping.source!r}, "
                    f"which is required for entity {mapping.entity!r}."
                )

            df = frames[mapping.source]
            id_column = mapping.id_column

            if not id_column:
                raise ValueError(
                    f"Entity {mapping.entity!r} has no id_column."
                )

            needed_columns = [id_column] + list(mapping.field_mappings.keys())
            _require_columns(df, mapping.source, needed_columns)

            rows = []

            for _, row in df.iterrows():
                entity_id = _clean(row[id_column])

                if entity_id is None or str(entity_id).strip() == "":
                    skipped += 1
                    continue

                properties = {}

                for raw_column, ontology_property in mapping.field_mappings.items():
                    value = _clean(row[raw_column])
                    if value is not None:
                        properties[ontology_property] = value

                # Always store canonical id.
                properties["id"] = entity_id

                rows.append(
                    {
                        "id": entity_id,
                        "properties": properties,
                    }
                )

            if not rows:
                continue

            label = _identifier(mapping.entity)

            query = f"""
            UNWIND $rows AS row
            MERGE (n:`{label}` {{id: row.id}})
            SET n += row.properties
            """

            result = driver.execute_query(
                query,
                rows=rows,
                database_=None,
            )

            entity_records += len(rows)
            nodes_created += result.summary.counters.nodes_created

        # 2) Materialize relationships only after all nodes exist.
        for mapping in ontology.relationship_mappings:
            if mapping.source_file not in frames:
                raise ValueError(
                    f"Uploaded files do not include {mapping.source_file!r}, "
                    f"which is required for relationship {mapping.relationship!r}."
                )

            df = frames[mapping.source_file]
            _require_columns(
                df,
                mapping.source_file,
                [mapping.source_id_column, mapping.target_id_column],
            )

            rows = []

            for _, row in df.iterrows():
                source_id = _clean(row[mapping.source_id_column])
                target_id = _clean(row[mapping.target_id_column])

                if (
                    source_id is None
                    or target_id is None
                    or str(source_id).strip() == ""
                    or str(target_id).strip() == ""
                ):
                    skipped += 1
                    continue

                rows.append(
                    {
                        "source_id": source_id,
                        "target_id": target_id,
                    }
                )

            if not rows:
                continue

            source_label = _identifier(mapping.source_entity)
            target_label = _identifier(mapping.target_entity)
            rel_type = _identifier(mapping.relationship)

            query = f"""
            UNWIND $rows AS row
            MATCH (source:`{source_label}` {{id: row.source_id}})
            MATCH (target:`{target_label}` {{id: row.target_id}})
            MERGE (source)-[:`{rel_type}`]->(target)
            """

            result = driver.execute_query(
                query,
                rows=rows,
                database_=None,
            )

            relationship_records += len(rows)
            relationships_created += (
                result.summary.counters.relationships_created
            )

    return BuildGraphResponse(
        ok=True,
        entity_records_materialized=entity_records,
        relationship_records_materialized=relationship_records,
        nodes_created=nodes_created,
        relationships_created=relationships_created,
        skipped_records=skipped,
        message=(
            "Knowledge graph materialized successfully. "
            "MERGE makes repeated builds idempotent."
        ),
    )
