from __future__ import annotations

import json
import os
import re

import httpx
from dotenv import load_dotenv
from pydantic import ValidationError

from .models import OntologyIR


load_dotenv()


SYSTEM_PROMPT = """You are an ontology induction agent.

Infer a useful domain ontology from heterogeneous data sources.

You will receive:
1. The user's objective.
2. Dataset schemas.
3. Column metadata.
4. Representative values.
5. Basic statistics.

Identify:
- canonical entity types
- useful properties
- relationship types
- source-to-ontology mappings
- explicit source-level relationship mappings

Optimize the ontology for the user's objective.
Do not simply reproduce source table names when a better canonical concept is justified.
Merge source concepts when they represent the same semantic entity.
Separate concepts when the distinction matters for the task.
Do not invent unsupported concepts.

IMPORTANT:
The ontology must be executable without reading prose descriptions.
For EVERY relationship type, provide one explicit relationship_mapping that identifies:
- relationship
- source_file
- source_entity
- source_id_column
- target_entity
- target_id_column

A relationship_mapping means:
"For each row in source_file, use source_id_column to identify the source node
and target_id_column to identify the target node, then create the relationship."

Return ONLY valid JSON with exactly these top-level keys:
entity_types, relationship_types, source_mappings, relationship_mappings, objective, notes.

Entity shape:
{
  "name": "Customer",
  "description": "...",
  "properties": [
    {
      "name": "id",
      "type": "string|integer|float|boolean|datetime",
      "required": true,
      "description": "..."
    }
  ]
}

Relationship shape:
{
  "name": "OWNS",
  "source": "Customer",
  "target": "Account",
  "description": "..."
}

Source mapping shape:
{
  "source": "customers.csv",
  "entity": "Customer",
  "id_column": "customer_id",
  "field_mappings": {
    "customer_id": "id"
  }
}

Relationship mapping shape:
{
  "relationship": "OWNS",
  "source_file": "accounts.csv",
  "source_entity": "Customer",
  "source_id_column": "customer_id",
  "target_entity": "Account",
  "target_id_column": "account_id"
}
"""


def is_k2_configured() -> bool:
    return bool(
        os.getenv("K2_API_KEY")
        and (os.getenv("K2_CHAT_URL") or os.getenv("K2_BASE_URL"))
    )


def _chat_url() -> str:
    explicit = os.getenv("K2_CHAT_URL")
    if explicit:
        return explicit.rstrip("/")

    base = os.environ["K2_BASE_URL"].rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions"


def _extract_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise


async def _post_chat(messages: list[dict], temperature: float) -> str:
    api_key = os.environ["K2_API_KEY"]
    model = os.getenv("K2_MODEL", "IFM/K2-Horizon-375B-A23B")
    url = _chat_url()

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(url, headers=headers, json=payload)

    if response.status_code >= 400:
        raise RuntimeError(
            f"K2 API error {response.status_code}: {response.text}"
        )

    data = response.json()
    return data["choices"][0]["message"]["content"]


async def generate_with_k2(objective: str, profiles: list[dict]) -> OntologyIR:
    user_prompt = f"""OBJECTIVE
{objective}

AVAILABLE DATA
{json.dumps(profiles, indent=2, ensure_ascii=False)}

TASK
Infer the smallest useful ontology that allows the user to reason about this
domain for the stated objective.

For each proposed entity and relationship:
1. Define what it represents.
2. Map entities to source fields that support them.
3. Avoid duplicate concepts caused only by inconsistent naming.
4. Prefer meaningful domain concepts over raw table names.
5. Do not create relationships without evidence in the source schemas,
   representative values, or objective.
6. For every relationship, provide an explicit relationship_mapping using
   actual source columns. Do not rely on the relationship description for
   materialization.

Return the result using the required ontology JSON schema.
"""

    content = await _post_chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )

    parsed = _extract_json(content)

    try:
        return OntologyIR.model_validate(parsed)
    except ValidationError as exc:
        repair_prompt = f"""The JSON you returned failed validation.

Validation errors:
{exc}

Original JSON:
{json.dumps(parsed, ensure_ascii=False)}

Correct the JSON only.

Rules:
- Keep the same intended ontology.
- Every relationship type must have exactly one executable
  relationship_mapping using actual source columns.
- relationship_mapping source_entity/target_entity must exactly match the
  corresponding relationship type.
- Return JSON only.
"""

        repaired_text = await _post_chat(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": repair_prompt},
            ],
            temperature=0,
        )

        repaired = _extract_json(repaired_text)
        return OntologyIR.model_validate(repaired)
