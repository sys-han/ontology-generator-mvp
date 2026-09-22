"use client";

import { useState } from "react";

import KnowledgeGraph from "@/components/KnowledgeGraph";
import {
  buildKnowledgeGraph,
  getKnowledgeGraphPreview,
} from "@/lib/api";
import type {
  BuildGraphResponse,
  GraphPreviewResponse,
  OntologyIR,
} from "@/types/ontology";

export default function BuildGraphPanel({
  ontology,
  files,
}: {
  ontology: OntologyIR;
  files: File[];
}) {
  const [loading, setLoading] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [result, setResult] = useState<BuildGraphResponse | null>(null);
  const [graph, setGraph] = useState<GraphPreviewResponse | null>(null);
  const [error, setError] = useState("");

  async function loadPreview() {
    setPreviewLoading(true);
    setError("");

    try {
      const data = await getKnowledgeGraphPreview();
      setGraph(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not load the Neo4j graph preview."
      );
    } finally {
      setPreviewLoading(false);
    }
  }

  async function onBuild() {
    setLoading(true);
    setError("");
    setResult(null);
    setGraph(null);

    try {
      const data = await buildKnowledgeGraph(ontology, files);
      setResult(data);

      const preview = await getKnowledgeGraphPreview();
      setGraph(preview);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not build the knowledge graph."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="detail-card">
      <div className="detail-card-header">
        <h2>Knowledge graph</h2>
        <span className="detail-count">Neo4j</span>
      </div>

      <div
        style={{
          display: "flex",
          gap: 8,
          flexWrap: "wrap",
        }}
      >
        <button
          className="ghost-button"
          onClick={onBuild}
          disabled={loading}
        >
          {loading ? "BUILDING…" : "BUILD KNOWLEDGE GRAPH"}
        </button>

        {result && (
          <button
            className="ghost-button"
            onClick={loadPreview}
            disabled={previewLoading}
          >
            {previewLoading ? "LOADING…" : "REFRESH GRAPH"}
          </button>
        )}
      </div>

      <p className="helper-text">
        Materializes validated entity and relationship mappings into Neo4j
        using deterministic MERGE queries.
      </p>

      {result && (
        <div className="helper-text">
          ✓ {result.entity_records_materialized} entity records ·{" "}
          {result.relationship_records_materialized} relationship records
          <br />
          New this run: {result.nodes_created} nodes ·{" "}
          {result.relationships_created} relationships
        </div>
      )}

      {graph && (
        <div style={{ marginTop: 20 }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              gap: 12,
              alignItems: "baseline",
            }}
          >
            <div>
              <div className="card-kicker">MATERIALIZED GRAPH</div>
              <h2
                style={{
                  margin: "6px 0 0",
                  fontSize: 18,
                }}
              >
                Live Neo4j instances
              </h2>
            </div>

            <div className="card-meta">
              {graph.node_count} nodes
              <span>·</span>
              {graph.relationship_count} relationships
            </div>
          </div>

          <KnowledgeGraph graph={graph} />
        </div>
      )}

      {error && <div className="error-box">{error}</div>}
    </div>
  );
}
