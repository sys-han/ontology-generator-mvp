from __future__ import annotations

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .graph_compiler import compile_schema_plan
from .graph_materializer import materialize_graph
from .graph_preview import read_graph_preview
from .heuristic import generate_heuristic_ontology
from .k2_client import generate_with_k2, is_k2_configured
from .models import (
    BuildGraphResponse,
    CompileRequest,
    CompileResponse,
    GenerateResponse,
    GraphPreviewResponse,
    OntologyIR,
)
from .neo4j_client import is_neo4j_configured, verify_neo4j
from .profiler import profile_file


app = FastAPI(
    title="Ontology Builder API",
    version="0.2.0",
    description=(
        "Profile CSV/JSON sources, infer a typed ontology IR, "
        "and materialize it into Neo4j."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {
        "ok": True,
        "k2_configured": is_k2_configured(),
        "neo4j_configured": is_neo4j_configured(),
    }


@app.get("/neo4j-health")
async def neo4j_health():
    if not is_neo4j_configured():
        return {
            "configured": False,
            "connected": False,
        }

    try:
        verify_neo4j()
        return {
            "configured": True,
            "connected": True,
        }
    except Exception as exc:
        return {
            "configured": True,
            "connected": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


@app.post("/generate-ontology", response_model=GenerateResponse)
async def generate_ontology(
    objective: str = Form(...),
    files: list[UploadFile] = File(...),
):
    if not files:
        raise HTTPException(
            status_code=400,
            detail="Upload at least one CSV or JSON file.",
        )

    profiles: list[dict] = []
    warnings: list[str] = []

    for upload in files:
        raw = await upload.read()

        if not raw:
            raise HTTPException(
                status_code=400,
                detail=f"{upload.filename} is empty.",
            )

        try:
            profile, _ = profile_file(
                upload.filename or "source.csv",
                raw,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Could not profile {upload.filename}: {exc}",
            ) from exc

        profiles.append(profile)

    if is_k2_configured():
        try:
            ontology = await generate_with_k2(objective, profiles)
            provider = "k2"
        except Exception as exc:
            warnings.append(
                "K2 call failed, so the local heuristic fallback was used: "
                f"{type(exc).__name__}: {exc}"
            )
            ontology = generate_heuristic_ontology(objective, profiles)
            provider = "heuristic"
    else:
        ontology = generate_heuristic_ontology(objective, profiles)
        provider = "heuristic"

    return GenerateResponse(
        ontology=ontology,
        profiles=profiles,
        provider=provider,
        warnings=warnings,
    )


@app.post("/compile-cypher", response_model=CompileResponse)
async def compile_cypher(request: CompileRequest):
    return CompileResponse(
        statements=compile_schema_plan(request.ontology)
    )


@app.post("/build-graph", response_model=BuildGraphResponse)
async def build_graph(
    ontology_json: str = Form(...),
    files: list[UploadFile] = File(...),
):
    if not is_neo4j_configured():
        raise HTTPException(
            status_code=503,
            detail=(
                "Neo4j is not configured. Add NEO4J_URI, "
                "NEO4J_USERNAME, and NEO4J_PASSWORD to backend/.env."
            ),
        )

    try:
        ontology = OntologyIR.model_validate_json(ontology_json)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid ontology IR: {exc}",
        ) from exc

    raw_files: dict[str, bytes] = {}

    for upload in files:
        filename = upload.filename or "source.csv"
        raw_files[filename] = await upload.read()

    try:
        return materialize_graph(ontology, raw_files)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Graph materialization failed: {type(exc).__name__}: {exc}",
        ) from exc



@app.get("/graph-preview", response_model=GraphPreviewResponse)
async def graph_preview(
    node_limit: int = 200,
    relationship_limit: int = 300,
):
    if not is_neo4j_configured():
        raise HTTPException(
            status_code=503,
            detail="Neo4j is not configured.",
        )

    try:
        return read_graph_preview(
            node_limit=node_limit,
            relationship_limit=relationship_limit,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not read Neo4j graph: {type(exc).__name__}: {exc}",
        ) from exc
