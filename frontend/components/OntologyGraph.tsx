"use client";

import { useMemo } from "react";
import {
  Background,
  BackgroundVariant,
  Controls,
  Edge,
  MarkerType,
  Node,
  ReactFlow,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import type { OntologyIR } from "@/types/ontology";

export default function OntologyGraph({
  ontology,
}: {
  ontology: OntologyIR;
}) {
  const nodes = useMemo<Node[]>(() => {
    const columns = Math.max(
      2,
      Math.ceil(Math.sqrt(ontology.entity_types.length))
    );

    return ontology.entity_types.map((entity, index) => ({
      id: entity.name,
      position: {
        x: (index % columns) * 310,
        y: Math.floor(index / columns) * 205,
      },
      data: {
        label: (
          <div className="node-card">
            <strong>{entity.name}</strong>
            <span>{entity.description || "Entity"}</span>
          </div>
        ),
      },
      style: {
        width: 250,
        borderRadius: 16,
        border: "1px solid rgba(183,214,204,0.16)",
        padding: 0,
        background:
          "linear-gradient(180deg, rgba(75,154,141,0.08), rgba(255,255,255,0.018)), #0b181e",
        color: "#f1f2ec",
        boxShadow: "0 16px 36px rgba(0,0,0,0.3)",
      },
    }));
  }, [ontology]);

  const edges = useMemo<Edge[]>(() => {
    return ontology.relationship_types.map((rel, index) => ({
      id: `edge-${index}-${rel.source}-${rel.target}-${rel.name}`,
      source: rel.source,
      target: rel.target,
      label: rel.name,
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: "#79a99d",
        width: 15,
        height: 15,
      },
      labelStyle: {
        fill: "#eff3ef",
        fontSize: 10,
        fontWeight: 760,
      },
      labelBgStyle: {
        fill: "#102128",
        fillOpacity: 0.96,
      },
      labelBgPadding: [5, 3],
      labelBgBorderRadius: 7,
      style: {
        stroke: "#79a99d",
        strokeWidth: 1.45,
      },
    }));
  }, [ontology]);

  return (
    <div className="graph-shell">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        fitViewOptions={{ padding: 0.28 }}
        minZoom={0.35}
        maxZoom={1.7}
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={22}
          size={1}
          color="#2c4a50"
        />
        <Controls
          showInteractive={false}
          style={{
            background: "#09161c",
            border: "1px solid rgba(183,214,204,0.12)",
            borderRadius: 10,
            overflow: "hidden",
          }}
        />
      </ReactFlow>
    </div>
  );
}
