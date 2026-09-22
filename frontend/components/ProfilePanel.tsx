import type { SourceProfile } from "@/types/ontology";

export default function ProfilePanel({
  profiles,
}: {
  profiles: SourceProfile[];
}) {
  return (
    <div className="detail-card">
      <div className="detail-card-header">
        <h2>Source profile</h2>
        <span className="detail-count">{profiles.length}</span>
      </div>

      <div className="profile-list">
        {profiles.map((profile) => (
          <details className="profile-card" key={profile.source}>
            <summary>
              <strong>{profile.source}</strong>
              <small>
                {profile.row_count_profiled.toLocaleString()} rows profiled
              </small>
            </summary>

            <div className="profile-columns">
              {Object.entries(profile.columns).map(([name, meta]) => (
                <div className="profile-column" key={name}>
                  <code>{name}</code>
                  <span>{meta.type}</span>
                  <small>
                    examples:{" "}
                    {meta.examples
                      .slice(0, 3)
                      .map((value) => String(value))
                      .join(", ") || "—"}
                  </small>
                </div>
              ))}
            </div>
          </details>
        ))}
      </div>
    </div>
  );
}
