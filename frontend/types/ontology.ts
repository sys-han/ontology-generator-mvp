export type ScalarType =
  | "string"
  | "integer"
  | "float"
  | "boolean"
  | "datetime";

export interface EntityProperty {
  name: string;
  type: ScalarType;
  required: boolean;
  description?: string | null;
}

export interface EntityType {
  name: string;
  description: string;
  properties: EntityProperty[];
}

export interface RelationshipType {
  name: string;
  source: string;
  target: string;
  description: string;
}

export interface SourceMapping {
  source: string;
  entity: string;
  id_column?: string | null;
  field_mappings: Record<string, string>;
}

export interface RelationshipMapping {
  relationship: string;
  source_file: string;
  source_entity: string;
  source_id_column: string;
  target_entity: string;
  target_id_column: string;
}

export interface OntologyIR {
  entity_types: EntityType[];
  relationship_types: RelationshipType[];
  source_mappings: SourceMapping[];
  relationship_mappings: RelationshipMapping[];
  objective?: string | null;
  notes: string[];
}

export interface SourceProfile {
  source: string;
  row_count_profiled: number;
  columns: Record<
    string,
    {
      type: string;
      nullable: boolean;
      unique_ratio: number;
      examples: unknown[];
      min?: unknown;
      max?: unknown;
    }
  >;
}

export interface GenerateResponse {
  ontology: OntologyIR;
  profiles: SourceProfile[];
  provider: "k2" | "heuristic";
  warnings: string[];
}

export interface BuildGraphResponse {
  ok: boolean;
  entity_records_materialized: number;
  relationship_records_materialized: number;
  nodes_created: number;
  relationships_created: number;
  skipped_records: number;
  message: string;
}


export interface GraphPreviewNode {
  id: string;
  labels: string[];
  properties: Record<string, unknown>;
}

export interface GraphPreviewEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  properties: Record<string, unknown>;
}

export interface GraphPreviewResponse {
  nodes: GraphPreviewNode[];
  edges: GraphPreviewEdge[];
  node_count: number;
  relationship_count: number;
}
