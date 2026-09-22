import type { SourceMapping } from "@/types/ontology";

export default function MappingPanel({
  mappings,
}: {
  mappings: SourceMapping[];
}) {
  return (
    <div className="detail-card">
      <div className="detail-card-header">
        <h2>Source mappings</h2>
        <span className="detail-count">{mappings.length}</span>
      </div>

      <div className="mapping-list">
        {mappings.map((mapping, index) => (
          <div className="mapping-card" key={`${mapping.source}-${index}`}>
            <code>{mapping.source}</code>

            <div className="mapping-arrow">↓</div>

            <strong>{mapping.entity}</strong>

            <small>ID: {mapping.id_column || "not inferred"}</small>

            {Object.keys(mapping.field_mappings || {}).length > 0 && (
              <details>
                <summary>Field mappings</summary>
                <ul>
                  {Object.entries(mapping.field_mappings).map(
                    ([source, target]) => (
                      <li key={source}>
                        <code>{source}</code> → <code>{target}</code>
                      </li>
                    )
                  )}
                </ul>
              </details>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
