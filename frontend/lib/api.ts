import type {
  BuildGraphResponse,
  GenerateResponse,
  GraphPreviewResponse,
  OntologyIR,
} from "@/types/ontology";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function generateOntology(
  objective: string,
  files: File[]
): Promise<GenerateResponse> {
  const body = new FormData();
  body.append("objective", objective);

  for (const file of files) {
    body.append("files", file);
  }

  const response = await fetch(`${API_BASE}/generate-ontology`, {
    method: "POST",
    body,
  });

  if (!response.ok) {
    let message = "Generation failed.";

    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {
      // Keep default error.
    }

    throw new Error(message);
  }

  return response.json();
}

export async function compileCypher(
  ontology: OntologyIR
): Promise<string[]> {
  const response = await fetch(`${API_BASE}/compile-cypher`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ ontology }),
  });

  if (!response.ok) {
    throw new Error("Could not compile Cypher preview.");
  }

  const data = await response.json();
  return data.statements;
}

export async function buildKnowledgeGraph(
  ontology: OntologyIR,
  files: File[]
): Promise<BuildGraphResponse> {
  const body = new FormData();

  body.append("ontology_json", JSON.stringify(ontology));

  for (const file of files) {
    body.append("files", file);
  }

  const response = await fetch(`${API_BASE}/build-graph`, {
    method: "POST",
    body,
  });

  if (!response.ok) {
    let message = "Could not build the knowledge graph.";

    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {
      // Keep default error.
    }

    throw new Error(message);
  }

  return response.json();
}


export async function getKnowledgeGraphPreview(): Promise<GraphPreviewResponse> {
  const response = await fetch(`${API_BASE}/graph-preview`, {
    method: "GET",
    cache: "no-store",
  });

  if (!response.ok) {
    let message = "Could not load the Neo4j graph preview.";

    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {
      // Keep default error.
    }

    throw new Error(message);
  }

  return response.json();
}
