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

import type { GraphPreviewResponse } from "@/types/ontology";

const LABEL_ACCENTS = [
  "#66b4a3",
  "#c4d96b",
  "#83b7d1",
  "#b8a6d9",
  "#e0b36f",
  "#8fc8a4",
];

function hashLabel(label: string) {
  let hash = 0;
  for (let i = 0; i < label.length; i += 1) {
    hash = (hash * 31 + label.charCodeAt(i)) >>> 0;
  }
  return hash;
}

function displayName(
  labels: string[],
  properties: Record<string, unknown>
) {
  const preferredKeys = [
    "name",
    "id",
    "account_id",
    "customer_id",
    "device_id",
    "transaction_id",
  ];

  for (const key of preferredKeys) {
    const value = properties[key];
    if (value !== undefined && value !== null && String(value).trim()) {
      return String(value);
    }
  }

  return labels[0] || "Node";
}

function propertyPreview(properties: Record<string, unknown>) {
  return Object.entries(properties)
    .filter(([key]) => key !== "id")
    .slice(0, 3);
}

export default function KnowledgeGraph({
  graph,
}: {
  graph: GraphPreviewResponse;
}) {
  const labelGroups = useMemo(() => {
    const groups = new Map<string, number>();

    for (const node of graph.nodes) {
      const label = node.labels[0] || "Node";
      if (!groups.has(label)) {
        groups.set(label, groups.size);
      }
    }

    return groups;
  }, [graph]);

  const nodes = useMemo<Node[]>(() => {
    const grouped = new Map<string, typeof graph.nodes>();

    for (const node of graph.nodes) {
      const label = node.labels[0] || "Node";
      const bucket = grouped.get(label) || [];
      bucket.push(node);
      grouped.set(label, bucket);
    }

    const result: Node[] = [];
    const groupEntries = Array.from(grouped.entries());
    const groupCount = Math.max(groupEntries.length, 1);
    const centerX = 520;
    const centerY = 330;
    const groupRadius = Math.min(290, 175 + groupCount * 20);

    groupEntries.forEach(([label, members], groupIndex) => {
      const groupAngle =
        (Math.PI * 2 * groupIndex) / groupCount - Math.PI / 2;

      const gx = centerX + Math.cos(groupAngle) * groupRadius;
      const gy = centerY + Math.sin(groupAngle) * groupRadius;

      const memberRadius = members.length <= 1 ? 0 : Math.min(115, 45 + members.length * 8);

      members.forEach((node, memberIndex) => {
        const memberAngle =
          (Math.PI * 2 * memberIndex) / Math.max(members.length, 1);

        const x = gx + Math.cos(memberAngle) * memberRadius;
        const y = gy + Math.sin(memberAngle) * memberRadius;

        const accent =
          LABEL_ACCENTS[hashLabel(label) % LABEL_ACCENTS.length];
        const name = displayName(node.labels, node.properties);
        const preview = propertyPreview(node.properties);

        result.push({
          id: node.id,
          position: { x, y },
          data: {
            label: (
              <div
                style={{
                  display: "grid",
                  gap: 5,
                  minWidth: 150,
                  textAlign: "left",
                }}
              >
                <div
                  style={{
                    color: accent,
                    fontSize: 10,
                    fontWeight: 850,
                    letterSpacing: "0.12em",
                    textTransform: "uppercase",
                  }}
                >
                  {label}
                </div>

                <strong
                  style={{
                    color: "#f1f2ec",
                    fontSize: 13,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {name}
                </strong>

                {preview.map(([key, value]) => (
                  <div
                    key={key}
                    style={{
                      color: "#90a29c",
                      fontSize: 9,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {key}: {String(value)}
                  </div>
                ))}
              </div>
            ),
          },
          style: {
            width: 180,
            padding: 12,
            borderRadius: 14,
            border: `1px solid ${accent}44`,
            background:
              "linear-gradient(180deg, rgba(75,154,141,0.055), rgba(255,255,255,0.01)), #0a171d",
            boxShadow: "0 12px 30px rgba(0,0,0,0.28)",
          },
        });
      });
    });

    return result;
  }, [graph]);

  const edges = useMemo<Edge[]>(() => {
    return graph.edges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      label: edge.type,
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: "#9fbf78",
        width: 15,
        height: 15,
      },
      style: {
        stroke: "#9fbf78",
        strokeWidth: 1.35,
      },
      labelStyle: {
        fill: "#e8eee9",
        fontSize: 9,
        fontWeight: 760,
      },
      labelBgStyle: {
        fill: "#0d1d23",
        fillOpacity: 0.94,
      },
      labelBgPadding: [4, 2],
      labelBgBorderRadius: 6,
    }));
  }, [graph]);

  return (
    <div
      style={{
        height: 620,
        marginTop: 14,
        overflow: "hidden",
        border: "1px solid rgba(215,232,226,0.085)",
        borderRadius: 14,
        background:
          "radial-gradient(circle at 72% 14%, rgba(75,154,141,0.10), transparent 20rem), #061117",
      }}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        fitViewOptions={{ padding: 0.22 }}
        minZoom={0.18}
        maxZoom={1.8}
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={22}
          size={1}
          color="#2c4a50"
        />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}
