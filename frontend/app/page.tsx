"use client";

import { ChangeEvent, useMemo, useState } from "react";

import BuildGraphPanel from "@/components/BuildGraphPanel";
import MappingPanel from "@/components/MappingPanel";
import OntologyGraph from "@/components/OntologyGraph";
import ProfilePanel from "@/components/ProfilePanel";
import { compileCypher, generateOntology } from "@/lib/api";
import type { GenerateResponse } from "@/types/ontology";

const DEFAULT_OBJECTIVE =
  "Investigate suspicious money movement and shared devices.";

export default function Home() {
  const [objective, setObjective] = useState(DEFAULT_OBJECTIVE);
  const [files, setFiles] = useState<File[]>([]);
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [cypher, setCypher] = useState<string[]>([]);
  const [showCypher, setShowCypher] = useState(false);

  const fileLabel = useMemo(() => {
    if (files.length === 0) return "No files selected";
    if (files.length === 1) return files[0].name;
    return `${files.length} files selected`;
  }, [files]);

  function onFiles(event: ChangeEvent<HTMLInputElement>) {
    setFiles(Array.from(event.target.files || []));
    setResult(null);
    setCypher([]);
    setError("");
  }

  async function onGenerate() {
    if (!objective.trim()) {
      setError("Tell the system what you are trying to understand.");
      return;
    }

    if (files.length === 0) {
      setError("Upload at least one CSV or JSON file.");
      return;
    }

    setLoading(true);
    setError("");
    setCypher([]);

    try {
      const data = await generateOntology(objective.trim(), files);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  async function onCompile() {
    if (!result) return;

    try {
      const statements = await compileCypher(result.ontology);
      setCypher(statements);
      setShowCypher(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not compile Cypher.");
    }
  }

  function downloadOntology() {
    if (!result) return;

    const blob = new Blob([JSON.stringify(result.ontology, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "ontology.json";
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <main className="app-shell">
      <header className="hero">
        <div className="hero-aurora" aria-hidden="true" />

        <div className="hero-copy">
          <div className="eyebrow">ONTOLOGY BUILDER · K2 HORIZON</div>

          <h1>Decide what the graph should mean.</h1>

          <p>
            Turn raw data and a user objective into a typed ontology, source
            mappings, and an executable graph model.
          </p>

          <div className="hero-tags">
            <span>Goal-conditioned</span>
            <span>Typed ontology IR</span>
            <span>K2-powered</span>
          </div>
        </div>
      </header>

      <section className="workspace">
        <aside className="control-rail">
          <div className="control-card">
            <div className="control-block">
              <div className="control-label">Objective</div>
              <label className="field-label" htmlFor="objective">
                What are you trying to understand?
              </label>
              <textarea
                id="objective"
                className="objective-input"
                value={objective}
                onChange={(event) => setObjective(event.target.value)}
                rows={6}
              />
            </div>

            <div className="control-block">
              <div className="control-label">Data</div>
              <label className="file-picker" htmlFor="files">
                <span className="file-picker-title">Choose CSV / JSON</span>
                <span className="file-picker-subtitle">{fileLabel}</span>
              </label>
              <input
                id="files"
                type="file"
                accept=".csv,.json"
                multiple
                onChange={onFiles}
                hidden
              />
            </div>

            <div className="control-block">
              <div className="control-label">Action</div>
              <button
                className="primary-button"
                onClick={onGenerate}
                disabled={loading}
              >
                <span className="button-spark" aria-hidden="true" />
                {loading ? "GENERATING…" : "GENERATE ONTOLOGY"}
              </button>

              <p className="helper-text">
                K2 proposes the semantic model. Pydantic validates the typed IR
                before downstream execution.
              </p>

              {error && <div className="error-box">{error}</div>}
            </div>
          </div>
        </aside>

        <section className="result-area">
          {!result ? (
            <div className="empty-card">
              <div className="empty-kicker">WORKFLOW</div>

              <div className="empty-step">
                <span>01</span>
                <div>
                  <h2>Upload data</h2>
                  <p>
                    Use CSV or JSON sources. The backend profiles schema,
                    representative values, and lightweight statistics.
                  </p>
                </div>
              </div>

              <div className="empty-step">
                <span>02</span>
                <div>
                  <h2>State the objective</h2>
                  <p>
                    The same source data can produce a different ontology when
                    the user&apos;s goal changes.
                  </p>
                </div>
              </div>

              <div className="empty-step">
                <span>03</span>
                <div>
                  <h2>Generate meaning</h2>
                  <p>
                    K2 proposes the ontology. The typed IR is validated before
                    it becomes executable.
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <>
              <div className="result-toolbar">
                <div
                  className={`status-badge ${
                    result.provider === "k2" ? "status-k2" : "status-fallback"
                  }`}
                >
                  <span className="status-dot" />
                  <span>
                    Generated with{" "}
                    <strong>
                      {result.provider === "k2"
                        ? "K2"
                        : "local heuristic fallback"}
                    </strong>
                  </span>
                </div>

                <div className="toolbar-actions">
                  <button className="ghost-button" onClick={downloadOntology}>
                    Download JSON
                  </button>
                  <button className="ghost-button" onClick={onCompile}>
                    Cypher preview
                  </button>
                </div>
              </div>

              {result.warnings.length > 0 && (
                <div className="warning-box">
                  {result.warnings.map((warning) => (
                    <p key={warning}>{warning}</p>
                  ))}
                </div>
              )}

              <div className="graph-card">
                <div className="card-header">
                  <div>
                    <div className="card-kicker">SEMANTIC MODEL</div>
                    <h2>Ontology</h2>
                  </div>

                  <div className="card-meta">
                    {result.ontology.entity_types.length} entities
                    <span>·</span>
                    {result.ontology.relationship_types.length} relationships
                  </div>
                </div>

                <OntologyGraph ontology={result.ontology} />
              </div>

              <div className="detail-grid">
                <MappingPanel mappings={result.ontology.source_mappings} />
                <ProfilePanel profiles={result.profiles} />
              </div>

              <BuildGraphPanel
                ontology={result.ontology}
                files={files}
              />

              {result.ontology.notes.length > 0 && (
                <div className="notes-card">
                  <div className="card-header compact">
                    <div>
                      <div className="card-kicker">MODEL RATIONALE</div>
                      <h2>Notes</h2>
                    </div>
                  </div>

                  <ul>
                    {result.ontology.notes.map((note) => (
                      <li key={note}>{note}</li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}
        </section>
      </section>

      {showCypher && (
        <div className="modal-backdrop" onClick={() => setShowCypher(false)}>
          <div className="modal" onClick={(event) => event.stopPropagation()}>
            <div className="card-header compact">
              <div>
                <div className="card-kicker">DETERMINISTIC OUTPUT</div>
                <h2>Cypher preview</h2>
              </div>

              <button
                className="ghost-button"
                onClick={() => setShowCypher(false)}
              >
                Close
              </button>
            </div>

            <p className="modal-description">
              Preview only. These statements are generated from the validated
              ontology IR and are not executed against Neo4j yet.
            </p>

            <div className="code-stack">
              {cypher.map((statement, index) => (
                <pre key={index}>{statement}</pre>
              ))}
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
