# K2 Ontology Generator

A hackathon MVP for generating a knowledge graph schema from raw data **and the problem a user is trying to solve**.

The basic idea is simple: the same dataset can support more than one useful ontology. A set of banking tables might be modeled around account ownership, suspicious money movement, or device-linked customer clusters depending on the task. The source data has not changed, but the concepts and relationships that matter have.

This project uses K2 Horizon to infer that task-specific semantic layer, validates the result as a typed intermediate representation, and then uses regular Python code to turn it into an executable Neo4j graph.

## Why

A direct table-to-graph conversion can preserve the structure of the source data, but it does not answer a more important modeling question:

**What should the graph represent for this use case?**

The generator takes two inputs:

- one or more CSV/JSON files
- a natural-language objective describing what the user wants to investigate or understand

The source files are profiled first. K2 then receives the objective together with column metadata, representative values, and basic statistics and proposes an ontology suited to that task.

The model is responsible for the semantic decision-making. The rest of the pipeline is deliberately constrained: Pydantic validates the ontology before deterministic code is allowed to compile or materialize it.

## How it works

```text
CSV / JSON
    |
    v
Source profiling
    |
    | schema + types + examples + basic statistics
    v
K2 Horizon + user objective
    |
    v
Ontology IR
    |
    v
Pydantic validation
    |
    +-------------------+
    |                   |
    v                   v
Ontology view       Cypher / Neo4j
                        |
                        v
                 Instance graph
```

### 1. Profile the source data

The backend reads CSV and JSON files with Pandas and records:

- columns and inferred types
- nullable fields
- representative values
- uniqueness ratios
- numeric min/max values

This gives the model information about both the shape of the source and some of the values behind that shape.

### 2. Generate the ontology

K2 receives the profiles together with the user's objective.

Instead of simply turning every table into a node type, it is prompted to identify useful domain concepts, relationships, and source mappings for the stated task.

The output is a JSON ontology containing:

- entity types and properties
- relationship types
- source-to-entity mappings
- explicit relationship mappings
- the original objective

### 3. Validate the IR

The generated JSON is parsed into a Pydantic `OntologyIR`.

Validation checks, among other things, that:

- entity and relationship names are unique
- relationship endpoints refer to defined entities
- source mappings refer to defined entities
- mappings contain IDs needed for materialization
- every relationship has an executable source-level mapping

If K2 returns structurally invalid output, the backend makes a repair request before accepting it.

### 4. Build the graph

The validated IR can be inspected in the frontend or compiled into Cypher.

When Neo4j is configured, the original source files and the generated mappings are used to create the instance graph. Nodes and relationships are written with `MERGE`, so rebuilding the same graph does not duplicate existing records.

The frontend shows both levels separately:

- **Ontology graph:** the generated semantic model
- **Knowledge graph:** the nodes and relationships actually materialized from the source data

## Testing objective-conditioned ontologies

`Prompts.rtf` contains the objectives used during the hackathon to test the central idea of the project:

> Keep the data fixed, change the objective, and see whether the resulting ontology changes in a meaningful way.

These were qualitative tests rather than a benchmark score. We compared the generated entity types, relationships, and source mappings across objectives to check whether K2 was changing the structure of the model rather than just changing labels or descriptions.

Two datasets were used.

### Banking mock data

The small demo dataset consists of four related CSV files:

```text
customers.csv
accounts.csv
transactions.csv
devices.csv
```

The same files were tested with four different objectives:

1. **Suspicious money movement and shared devices**

   > Investigate suspicious money movement and shared devices.

2. **Compliance and manual risk review**

   > Understand customer compliance workflow and prioritize accounts for manual risk review.

3. **Linked-customer discovery**

   > Identify clusters of customers that may be linked through shared devices, IP addresses, and account activity.

4. **Account ownership and portfolio structure**

   > Summarize customer account ownership and portfolio structure. Ignore transaction monitoring and device linkage unless necessary.

These prompts intentionally emphasize different parts of the same underlying data. For example, a model useful for portfolio structure does not need to organize the domain in the same way as one intended to find shared-device clusters.

### HarmBench

The second test uses a single HarmBench behavior dataset:

```text
harmbench_behaviors_text_all.csv
```

Here the source schema stays exactly the same while the objective changes substantially:

1. **Adversarial threat analysis**

   > Identify adversarial threat patterns across FunctionalCategory and SemanticCategory, cluster actionable attack prompts by risk severity, and link target model vulnerabilities to specific attack types.

2. **Compliance and safety controls**

   > Group behavior test cases according to statutory compliance frameworks (e.g., EU AI Act, NIST AI RMF), map categories (Cybercrime, Bioweapons, Harassment) to safety mitigation policies, and trace context requirements for refusal filters.

3. **Context-dependent and multimodal risk**

   > Isolate behavior test cases that depend on ContextString and external media (multimodal) to evaluate safety filter blind spots where context shifts plain text into malicious execution.

This case was useful because there is only one source table. Any substantial change in the conceptual model therefore comes from interpreting the data for a different objective rather than from choosing different input tables.

## Local fallback

The repository also includes a local heuristic generator so the UI and graph pipeline can run without access to K2.

The fallback infers entities from filenames and relationships from ID-like columns. It is intended as a development and integration fallback, not as a replacement for objective-conditioned semantic induction.

To test how ontology structure changes with the user objective, use the K2 path.

## Run locally

### Backend

```bash
cd backend

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

FastAPI will be available at:

```text
http://localhost:8000
```

API docs:

```text
http://localhost:8000/docs
```

### Frontend

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Then open:

```text
http://localhost:3000
```

You can also use the included script to start both:

```bash
./run-local.sh
```

## Configure K2

Copy the root environment example into the backend:

```bash
cp .env.example backend/.env
```

Then configure an OpenAI-compatible K2 endpoint:

```env
K2_API_KEY=...
K2_BASE_URL=https://your-provider.example/v1
K2_MODEL=K2-Horizon-375B-A23B
```

If the provider gives you a complete chat-completions URL:

```env
K2_CHAT_URL=https://your-provider.example/v1/chat/completions
```

Without these values, the backend uses the local heuristic fallback.

## Optional Neo4j materialization

Ontology generation and Cypher preview do not require Neo4j.

To build and inspect the instance graph, add a Neo4j connection to `backend/.env`:

```env
NEO4J_URI=...
NEO4J_USERNAME=...
NEO4J_PASSWORD=...
```

Once connected, the frontend can materialize the validated ontology against the uploaded source files and read the resulting graph back from Neo4j.

## Stack

- **K2 Horizon** — ontology induction
- **FastAPI** — backend API
- **Pandas** — source profiling and data loading
- **Pydantic** — ontology IR and validation
- **Neo4j** — graph storage
- **Next.js / React** — frontend
- **React Flow / XYFlow** — graph visualization

## Ontology IR

The ontology IR is the boundary between model reasoning and graph execution.

A simplified version looks like:

```json
{
  "entity_types": [],
  "relationship_types": [],
  "source_mappings": [],
  "relationship_mappings": [],
  "objective": "..."
}
```

K2 proposes the semantic model. Code validates whether that model is structurally executable before anything is written to the graph.
