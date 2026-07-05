"use client";
// =============================================================================
// === frontend/components/project/IntelligencePanels.tsx ===
// Sprint 19 extraction: DependencyGraphPanel, DecisionEnginePanel, and
// RiskForecastPanel were previously defined locally inside
// app/dashboard/projects/[id]/page.tsx (Sprints 11, 13, 14). Moved here,
// unchanged, so they can be shared between the project detail page AND
// the new Command Center (Sprint 19) without duplicating ~850 lines of
// already-tested logic. All three are self-contained: given a projectId,
// each fetches its own data independently.
// =============================================================================

import { useEffect, useState } from "react";
import {
  projectsApi,
  DependencyGraph,
  DependencyNode,
  DecisionEngine,
  RiskForecast,
} from "@/lib/api/projects";

export function DependencyGraphPanel({ projectId }: { projectId: string }) {
  const [graph,          setGraph]          = useState<DependencyGraph | null>(null);
  const [loading,        setLoading]        = useState(true);
  const [expanded,       setExpanded]       = useState(false);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  useEffect(() => {
    projectsApi.getDependencyGraph(projectId)
      .then(setGraph)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [projectId]);

  // ── Status colour helpers (unchanged from Sprint 11) ─────
  const nodeColor = (node: DependencyNode): string => {
    if (node.status === "completed")           return "var(--color-success)";
    if (node.status === "menunggu_verifikasi") return "var(--color-accent)";
    if (node.is_blocking)                      return "var(--color-danger)";
    if (node.is_dependency_blocked)            return "var(--color-ink-3)";
    if (node.status === "in_progress")         return "var(--color-warning)";
    return "rgba(14,13,11,0.3)";
  };

  const nodeBg = (node: DependencyNode): string => {
    if (node.status === "completed")           return "var(--color-success-light)";
    if (node.status === "menunggu_verifikasi") return "var(--color-accent-light)";
    if (node.is_blocking)                      return "var(--color-danger-light)";
    if (node.is_dependency_blocked)            return "rgba(14,13,11,0.04)";
    if (node.status === "in_progress")         return "var(--color-warning-light)";
    return "var(--color-paper-2)";
  };

  const nodeIcon = (node: DependencyNode): string => {
    if (node.status === "completed")           return "✅";
    if (node.status === "menunggu_verifikasi") return "⏳";
    if (node.is_blocking)                      return "⚡";
    if (node.is_dependency_blocked)            return "🔒";
    if (node.status === "in_progress")         return "●";
    return "○";
  };

  if (loading) return (
    <div className="card" style={{ marginBottom: 16, textAlign: "center", padding: 16, color: "var(--color-ink-3)", fontSize: 12 }}>
      Memuat dependency graph...
    </div>
  );

  if (!graph || graph.nodes.length === 0) return null;

  // ── Topological sort (unchanged from Sprint 11) ────────────────
  const incomingEdges = new Map<string, string[]>();
  graph.nodes.forEach(n => incomingEdges.set(n.id, []));
  graph.edges.forEach(e => {
    const arr = incomingEdges.get(e.to) ?? [];
    arr.push(e.from);
    incomingEdges.set(e.to, arr);
  });

  const columns = new Map<string, number>();
  const assignCol = (nodeId: string, visited = new Set<string>()): number => {
    if (columns.has(nodeId)) return columns.get(nodeId)!;
    if (visited.has(nodeId)) return 0;
    visited.add(nodeId);
    const prereqs = incomingEdges.get(nodeId) ?? [];
    const col = prereqs.length === 0
      ? 0
      : Math.max(...prereqs.map(p => assignCol(p, new Set(visited)))) + 1;
    columns.set(nodeId, col);
    return col;
  };
  graph.nodes.forEach(n => assignCol(n.id));

  const colGroups = new Map<number, string[]>();
  graph.nodes.forEach(n => {
    const col = columns.get(n.id) ?? 0;
    if (!colGroups.has(col)) colGroups.set(col, []);
    colGroups.get(col)!.push(n.id);
  });
  const numCols = Math.max(...Array.from(columns.values())) + 1;

  const NODE_W  = 152;
  const NODE_H  = 58;
  const COL_GAP = 56;
  const ROW_GAP = 14;

  const nodeMap   = new Map(graph.nodes.map(n => [n.id, n]));
  const positions = new Map<string, { x: number; y: number }>();

  for (let col = 0; col < numCols; col++) {
    const nodesInCol = colGroups.get(col) ?? [];
    nodesInCol.forEach((nodeId, rowIdx) => {
      positions.set(nodeId, {
        x: col * (NODE_W + COL_GAP),
        y: rowIdx * (NODE_H + ROW_GAP),
      });
    });
  }

  const maxRows = Math.max(...Array.from(colGroups.values()).map(g => g.length));
  const svgW    = numCols * (NODE_W + COL_GAP) - COL_GAP + 24;
  const svgH    = maxRows * (NODE_H + ROW_GAP) - ROW_GAP + 16;

  // Sprint 16: selected node for detail panel
  const selectedNode = selectedNodeId ? nodeMap.get(selectedNodeId) : null;

  const handleNodeClick = (nodeId: string) => {
    setSelectedNodeId(prev => prev === nodeId ? null : nodeId);
  };

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      {/* ── Header (unchanged) ── */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)" }}>
            Dependency Graph
          </div>
          <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginTop: 2 }}>
            Apa yang bergantung pada apa — tahap {graph.stage_display}
            {/* Sprint 16 hint */}
            <span style={{ marginLeft: 8, opacity: 0.6 }}>· Klik node untuk detail</span>
          </div>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          style={{ fontSize: 11, color: "var(--color-accent)", background: "none", border: "none", cursor: "pointer", fontWeight: 600 }}>
          {expanded ? "Sembunyikan ↑" : "Lihat graf ↓"}
        </button>
      </div>

      {/* ── Legend (unchanged) ── */}
      <div style={{ display: "flex", gap: 14, flexWrap: "wrap", marginBottom: 12 }}>
        {[
          { color: "var(--color-success)", label: "Selesai"   },
          { color: "var(--color-warning)", label: "Diproses"  },
          { color: "var(--color-accent)",  label: "Review"    },
          { color: "var(--color-danger)",  label: "Memblokir" },
          { color: "var(--color-ink-3)",   label: "Terkunci"  },
        ].map(({ color, label }) => (
          <div key={label} style={{ display: "flex", alignItems: "center", gap: 5 }}>
            <div style={{ width: 9, height: 9, borderRadius: 2, backgroundColor: color }} />
            <span style={{ fontSize: 10, color: "var(--color-ink-3)" }}>{label}</span>
          </div>
        ))}
      </div>

      {/* ── Collapsed: pill chain — NOW CLICKABLE ── */}
      {!expanded && (
        <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
          {graph.nodes.map((node) => {
            const color    = nodeColor(node);
            const bg       = nodeBg(node);
            const icon     = nodeIcon(node);
            const isSelected = selectedNodeId === node.id;
            return (
              <div key={node.id} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                {/* Sprint 16: clickable pill */}
                <div
                  onClick={() => handleNodeClick(node.id)}
                  style={{
                    padding: "5px 11px", borderRadius: 999,
                    backgroundColor: bg,
                    border: isSelected
                      ? `2px solid ${color}`
                      : `1.5px solid ${color}44`,
                    fontSize: 11, fontWeight: 600, color,
                    display: "flex", alignItems: "center", gap: 5,
                    cursor: "pointer",
                    transform: isSelected ? "scale(1.04)" : "scale(1)",
                    transition: "all 0.15s",
                    boxShadow: isSelected ? `0 0 0 3px ${color}22` : "none",
                  }}>
                  <span style={{ fontSize: 12 }}>{icon}</span>
                  {node.name}
                  {node.is_mandatory && (
                    <span style={{ fontSize: 9, opacity: 0.7 }}>{node.weight_pct}%</span>
                  )}
                </div>
                {graph.edges.some(e => e.from === node.id) && (
                  <span style={{ color: "var(--color-ink-3)", fontSize: 14, lineHeight: 1 }}>→</span>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* ── Expanded: SVG graph — nodes NOW CLICKABLE ── */}
      {expanded && (
        <div style={{ overflowX: "auto", paddingBottom: 4 }}>
          <svg width={svgW} height={svgH + 8} style={{ display: "block", minWidth: svgW }}>
            {/* Edges (unchanged) */}
            {graph.edges.map((edge, i) => {
              const from = positions.get(edge.from);
              const to   = positions.get(edge.to);
              if (!from || !to) return null;
              const x1 = from.x + NODE_W + 10;
              const y1 = from.y + NODE_H / 2 + 5;
              const x2 = to.x + 10;
              const y2 = to.y + NODE_H / 2 + 5;
              const cx  = x1 + (x2 - x1) * 0.55;
              const toNode   = nodeMap.get(edge.to);
              const fromNode = nodeMap.get(edge.from);
              const edgeColor =
                toNode?.is_dependency_blocked  ? "rgba(14,13,11,0.12)" :
                toNode?.is_blocking            ? "var(--color-danger)"  :
                fromNode?.status === "completed" ? "var(--color-success)" :
                                                  "rgba(14,13,11,0.18)";
              const isDashed = !!toNode?.is_dependency_blocked;
              return (
                <g key={`edge-${i}`}>
                  <path
                    d={`M${x1},${y1} C${cx},${y1} ${cx},${y2} ${x2},${y2}`}
                    fill="none" stroke={edgeColor} strokeWidth={1.5}
                    strokeDasharray={isDashed ? "4 3" : undefined}
                  />
                  <polygon
                    points={`${x2},${y2} ${x2 - 7},${y2 - 4} ${x2 - 7},${y2 + 4}`}
                    fill={edgeColor}
                  />
                </g>
              );
            })}

            {/* Nodes — Sprint 16: clickable via onClick on <g> */}
            {graph.nodes.map((node) => {
              const pos  = positions.get(node.id);
              if (!pos) return null;
              const color      = nodeColor(node);
              const bg         = nodeBg(node);
              const icon       = nodeIcon(node);
              const isSelected = selectedNodeId === node.id;
              const px         = pos.x + 10;
              const py         = pos.y + 5;
              const displayName = node.name.length > 17
                ? node.name.slice(0, 15) + "…" : node.name;

              return (
                <g
                  key={`node-${node.id}`}
                  transform={`translate(${px}, ${py})`}
                  onClick={() => handleNodeClick(node.id)}
                  style={{ cursor: "pointer" }}
                >
                  <rect
                    width={NODE_W} height={NODE_H} rx={8}
                    fill={bg}
                    stroke={isSelected ? color : `${color}99`}
                    strokeWidth={isSelected ? 2.5 : 1.5}
                  />
                  {/* Selection glow */}
                  {isSelected && (
                    <rect width={NODE_W} height={NODE_H} rx={8}
                      fill="none" stroke={color} strokeWidth={4} opacity={0.15}
                    />
                  )}
                  <text x={12} y={NODE_H / 2} fontSize={15} dominantBaseline="middle">
                    {icon}
                  </text>
                  <text x={32} y={NODE_H / 2 - (node.is_mandatory ? 7 : 0)}
                    fontSize={11} fontWeight={600} fill={color} dominantBaseline="middle">
                    {displayName}
                  </text>
                  {node.is_mandatory && (
                    <text x={32} y={NODE_H / 2 + 9}
                      fontSize={9} fill={color} dominantBaseline="middle" opacity={0.65}>
                      bobot {node.weight_pct}%
                      {node.is_blocking ? " · ⚡ memblokir" :
                       node.status === "completed" ? " · selesai" : ""}
                    </text>
                  )}
                  {!node.is_mandatory && (
                    <text x={32} y={NODE_H / 2 + 9}
                      fontSize={9} fill="var(--color-ink-3)" dominantBaseline="middle">
                      opsional
                    </text>
                  )}
                </g>
              );
            })}
          </svg>
        </div>
      )}

      {/* ── Sprint 16: Node detail panel ── */}
      {selectedNode && (
        <div style={{
          marginTop: 12, padding: "12px 14px", borderRadius: 10,
          backgroundColor: nodeBg(selectedNode),
          border: `1.5px solid ${nodeColor(selectedNode)}44`,
          position: "relative",
        }}>
          {/* Close button */}
          <button
            onClick={() => setSelectedNodeId(null)}
            style={{
              position: "absolute", top: 8, right: 8,
              background: "none", border: "none", cursor: "pointer",
              fontSize: 14, color: "var(--color-ink-3)", lineHeight: 1,
            }}>
            ✕
          </button>

          {/* Node title */}
          <div style={{
            fontSize: 13, fontWeight: 700,
            color: nodeColor(selectedNode), marginBottom: 8,
          }}>
            {nodeIcon(selectedNode)} {selectedNode.name}
            <span style={{
              marginLeft: 8, fontSize: 9, fontWeight: 600,
              padding: "2px 7px", borderRadius: 999,
              backgroundColor: `${nodeColor(selectedNode)}22`,
              color: nodeColor(selectedNode),
            }}>
              {selectedNode.status_display}
            </span>
          </div>

          {/* Detail rows */}
          <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
            {/* Block reason */}
            {selectedNode.block_reason && (
              <div style={{ display: "flex", gap: 8, fontSize: 11, color: "var(--color-ink)" }}>
                <span style={{ color: "var(--color-ink-3)", minWidth: 60, flexShrink: 0 }}>Alasan</span>
                <span style={{ fontWeight: 600, color: "var(--color-danger)" }}>
                  {selectedNode.block_reason}
                </span>
              </div>
            )}
            {/* Owner */}
            <div style={{ display: "flex", gap: 8, fontSize: 11, color: "var(--color-ink)" }}>
              <span style={{ color: "var(--color-ink-3)", minWidth: 60, flexShrink: 0 }}>Pemilik</span>
              <span>
                {selectedNode.assigned_to_name
                  ? `👤 ${selectedNode.assigned_to_name}`
                  : <span style={{ color: "var(--color-ink-3)", fontStyle: "italic" }}>Belum ditugaskan</span>
                }
              </span>
            </div>
            {/* ETA */}
            <div style={{ display: "flex", gap: 8, fontSize: 11, color: "var(--color-ink)" }}>
              <span style={{ color: "var(--color-ink-3)", minWidth: 60, flexShrink: 0 }}>ETA</span>
              <span>~{selectedNode.est_minutes} menit</span>
            </div>
            {/* Impact */}
            {selectedNode.is_mandatory && selectedNode.status !== "completed" && (
              <div style={{ display: "flex", gap: 8, fontSize: 11, color: "var(--color-ink)" }}>
                <span style={{ color: "var(--color-ink-3)", minWidth: 60, flexShrink: 0 }}>Dampak</span>
                <span style={{ fontWeight: 700, color: "var(--color-success)" }}>
                  +{selectedNode.weight_pct}% kesiapan jika selesai
                </span>
              </div>
            )}
          </div>

          {/* CTA button */}
          {selectedNode.status !== "completed" && (
            <button
              onClick={() => {
                document
                  .getElementById("requirements-card")
                  ?.scrollIntoView({ behavior: "smooth", block: "start" });
                setSelectedNodeId(null);
              }}
              style={{
                marginTop: 10, width: "100%",
                padding: "8px", borderRadius: 7, border: "none",
                backgroundColor: nodeColor(selectedNode), color: "white",
                fontSize: 11, fontWeight: 700, cursor: "pointer",
                transition: "opacity 0.15s",
              }}
              onMouseEnter={e => (e.currentTarget.style.opacity = "0.88")}
              onMouseLeave={e => (e.currentTarget.style.opacity = "1")}
            >
              Ambil Tindakan →
            </button>
          )}
        </div>
      )}
    </div>
  );
}

// ── Sprint 13: Decision Engine Panel ─────────────────────────
// Shows the single best action with quantified readiness impact,
// 3 bullet reasons, and ranked alternatives 2-3.
// Fetches independently from GET /api/projects/<id>/decision/
// so the panel loads without blocking the rest of the page.
export function DecisionEnginePanel({ projectId }: { projectId: string }) {
  const [engine,  setEngine]  = useState<DecisionEngine | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    projectsApi.getDecisionEngine(projectId)
      .then(setEngine)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [projectId]);

  // Priority → colour + label mapping
  const priorityMeta: Record<string, { color: string; bg: string; label: string }> = {
    high:   { color: "var(--color-danger)",  bg: "var(--color-danger-light)",  label: "Prioritas Tinggi"  },
    medium: { color: "var(--color-warning)", bg: "var(--color-warning-light)", label: "Prioritas Sedang"  },
    low:    { color: "var(--color-ink-3)",   bg: "var(--color-paper-2)",       label: "Prioritas Rendah"  },
  };

  if (loading) {
    return (
      <div className="card" style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)", marginBottom: 8 }}>
          🎯 Decision Engine
        </div>
        <div style={{ fontSize: 11, color: "var(--color-ink-3)", padding: "12px 0" }}>
          Menganalisis data proyek...
        </div>
      </div>
    );
  }

  if (!engine) return null;

  // ── All clear — nothing to do ─────────────────────────────
  if (!engine.has_recommendations) {
    return (
      <div className="card" style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)", marginBottom: 12 }}>
          🎯 Decision Engine
        </div>
        <div style={{
          padding: "16px",
          backgroundColor: "var(--color-success-light)",
          borderRadius: 10,
          textAlign: "center",
        }}>
          <div style={{ fontSize: 22, marginBottom: 6 }}>🎉</div>
          <div style={{ fontSize: 12, fontWeight: 600, color: "var(--color-success)" }}>
            {engine.message ?? "Semua requirement wajib sudah selesai!"}
          </div>
          {engine.all_clear && (
            <div style={{ fontSize: 11, color: "var(--color-success)", opacity: 0.8, marginTop: 4 }}>
              Proyek siap melanjutkan ke tahap berikutnya
            </div>
          )}
        </div>
      </div>
    );
  }

  const primary = engine.primary!;
  const pm      = priorityMeta[primary.priority] ?? priorityMeta.medium;
  const readinessGain = engine.projected_readiness - engine.current_readiness;

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      {/* ── Header ── */}
      <div style={{
        display: "flex", alignItems: "flex-start",
        justifyContent: "space-between", marginBottom: 14,
      }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)" }}>
            🎯 Decision Engine
          </div>
          <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginTop: 2 }}>
            Apa yang harus dilakukan sekarang
          </div>
        </div>
        {/* Readiness projection */}
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: 10, color: "var(--color-ink-3)", marginBottom: 2 }}>
            proyeksi kesiapan
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
            <span style={{ fontSize: 13, fontWeight: 700, color: "var(--color-ink-3)" }}>
              {engine.current_readiness}%
            </span>
            <span style={{ fontSize: 11, color: "var(--color-ink-3)" }}>→</span>
            <span style={{ fontSize: 16, fontWeight: 800, color: "var(--color-success)" }}>
              {engine.projected_readiness}%
            </span>
          </div>
        </div>
      </div>

      {/* ── Primary recommendation card ── */}
      <div style={{
        padding: "14px 16px", borderRadius: 10,
        backgroundColor: "var(--color-paper-2)",
        border: `2px solid ${pm.color}28`,
        marginBottom: engine.alternatives.length > 0 ? 12 : 0,
      }}>
        {/* Priority badge + time estimate */}
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
          <span style={{
            fontSize: 9, fontWeight: 700,
            padding: "2px 8px", borderRadius: 999,
            backgroundColor: pm.color, color: "white",
            textTransform: "uppercase", letterSpacing: "0.05em",
          }}>
            {pm.label}
          </span>
          <span style={{ fontSize: 10, color: "var(--color-ink-3)" }}>
            ~{primary.est_minutes} menit
          </span>
        </div>

        {/* Action title + impact badge */}
        <div style={{
          display: "flex", alignItems: "flex-start",
          justifyContent: "space-between", gap: 12, marginBottom: 12,
        }}>
          <div style={{
            fontSize: 15, fontWeight: 700,
            color: "var(--color-ink)", flex: 1, lineHeight: 1.3,
          }}>
            {primary.action}
          </div>
          {/* Readiness impact badge */}
          <div style={{
            padding: "8px 12px", borderRadius: 8, flexShrink: 0,
            backgroundColor: "var(--color-success-light)",
            textAlign: "center",
          }}>
            <div style={{
              fontSize: 20, fontWeight: 800,
              color: "var(--color-success)", lineHeight: 1,
            }}>
              +{readinessGain}%
            </div>
            <div style={{ fontSize: 9, color: "var(--color-success)", marginTop: 2 }}>
              kesiapan
            </div>
          </div>
        </div>

        {/* Reasons */}
        <div style={{
          display: "flex", flexDirection: "column",
          gap: 5, marginBottom: 14,
        }}>
          {primary.reasons.map((reason, i) => (
            <div key={i} style={{ display: "flex", gap: 7, fontSize: 11, color: "var(--color-ink)", lineHeight: 1.4 }}>
              <span style={{ color: pm.color, flexShrink: 0, fontWeight: 700 }}>•</span>
              {reason}
            </div>
          ))}
        </div>

        {/* CTA — scrolls to the requirements card */}
        <button
          onClick={() => {
            document
              .getElementById("requirements-card")
              ?.scrollIntoView({ behavior: "smooth", block: "start" });
          }}
          style={{
            width: "100%", padding: "10px", borderRadius: 8,
            border: "none", cursor: "pointer",
            backgroundColor: pm.color, color: "white",
            fontSize: 12, fontWeight: 700,
            transition: "opacity 0.15s",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.opacity = "0.88")}
          onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
        >
          Ambil Tindakan →
        </button>
      </div>

      {/* ── Alternatives ── */}
      {engine.alternatives.length > 0 && (
        <div>
          <div style={{
            fontSize: 10, fontWeight: 700, color: "var(--color-ink-3)",
            textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8,
          }}>
            Tindakan Lainnya
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
            {engine.alternatives.map((alt) => (
              <div key={alt.rank} style={{
                display: "flex", alignItems: "center", gap: 10,
                padding: "9px 12px", borderRadius: 8,
                backgroundColor: "var(--color-paper-2)",
              }}>
                {/* Rank circle */}
                <div style={{
                  width: 22, height: 22, borderRadius: "50%", flexShrink: 0,
                  backgroundColor: "rgba(14,13,11,0.07)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 10, fontWeight: 700, color: "var(--color-ink-3)",
                }}>
                  {alt.rank}
                </div>
                {/* Action label */}
                <div style={{ flex: 1, fontSize: 11, fontWeight: 600, color: "var(--color-ink)" }}>
                  {alt.action}
                </div>
                {/* Impact */}
                <div style={{
                  fontSize: 12, fontWeight: 700,
                  color: "var(--color-success)", whiteSpace: "nowrap",
                }}>
                  +{alt.readiness_impact_pct}%
                </div>
                {/* Time estimate */}
                <div style={{
                  fontSize: 10, color: "var(--color-ink-3)",
                  whiteSpace: "nowrap",
                }}>
                  ~{alt.est_minutes} mnt
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Sprint 14: Risk Forecast Panel ───────────────────────────
// Shows current risk vs projected risk in 14 days.
// "What happens if nothing changes?" — honest, deterministic.
// Fetches independently so it doesn't block the rest of the page.

export function RiskForecastPanel({ projectId }: { projectId: string }) {
  const [forecast, setForecast] = useState<RiskForecast | null>(null);
  const [loading,  setLoading]  = useState(true);

  useEffect(() => {
    projectsApi.getRiskForecast(projectId)
      .then(setForecast)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [projectId]);

  // Risk level → colour helper
  const levelColor = (level: string): string => {
    if (level === "high")   return "var(--color-danger)";
    if (level === "medium") return "var(--color-warning)";
    return "var(--color-success)";
  };
  const levelBg = (level: string): string => {
    if (level === "high")   return "var(--color-danger-light)";
    if (level === "medium") return "var(--color-warning-light)";
    return "var(--color-success-light)";
  };

  if (loading) {
    return (
      <div className="card" style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)", marginBottom: 8 }}>
          📈 Risk Forecast
        </div>
        <div style={{ fontSize: 11, color: "var(--color-ink-3)", padding: "10px 0" }}>
          Menghitung proyeksi risiko...
        </div>
      </div>
    );
  }

  if (!forecast) return null;

  const currentColor  = levelColor(forecast.current.level);
  const forecastColor = levelColor(forecast.forecast.level);
  const isGrowing     = forecast.delta > 0;
  const isStable      = forecast.delta === 0;

  return (
    <div className="card" style={{
      marginBottom: 16,
      // Pulse border if escalating — persistent, calm, not alarming
      border: forecast.will_escalate
        ? "1.5px solid var(--color-danger)"
        : "1.5px solid rgba(14,13,11,0.08)",
    }}>
      {/* ── Header ── */}
      <div style={{
        display: "flex", alignItems: "center",
        justifyContent: "space-between", marginBottom: 14,
      }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-ink)" }}>
            📈 Risk Forecast
          </div>
          <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginTop: 2 }}>
            Proyeksi dalam {forecast.days} hari jika tidak ada tindakan
          </div>
        </div>
        {/* Delta badge */}
        {isStable ? (
          <div style={{
            padding: "4px 10px", borderRadius: 6,
            backgroundColor: "var(--color-paper-2)",
            fontSize: 11, fontWeight: 700, color: "var(--color-ink-3)",
          }}>
            = Stabil
          </div>
        ) : (
          <div style={{
            padding: "4px 10px", borderRadius: 6,
            backgroundColor: "var(--color-danger-light)",
            fontSize: 11, fontWeight: 700, color: "var(--color-danger)",
          }}>
            +{forecast.delta} pts
          </div>
        )}
      </div>

      {/* ── Two-column: Current vs Forecast ── */}
      <div style={{
        display: "grid", gridTemplateColumns: "1fr auto 1fr",
        gap: 10, alignItems: "center", marginBottom: 14,
      }}>
        {/* Current */}
        <div style={{
          padding: "14px 16px", borderRadius: 10,
          backgroundColor: levelBg(forecast.current.level),
          textAlign: "center",
        }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: "var(--color-ink-3)", marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Saat Ini
          </div>
          <div style={{ fontSize: 28, fontWeight: 800, color: currentColor, lineHeight: 1 }}>
            {forecast.current.score}
          </div>
          <div style={{ fontSize: 10, color: "var(--color-ink-3)", marginTop: 2 }}>/ 100</div>
          <div style={{
            marginTop: 8, padding: "3px 10px", borderRadius: 999,
            backgroundColor: currentColor, color: "white",
            fontSize: 10, fontWeight: 700, display: "inline-block",
          }}>
            {forecast.current.level_display}
          </div>
        </div>

        {/* Arrow */}
        <div style={{
          fontSize: 20, color: isGrowing ? "var(--color-danger)" : "var(--color-ink-3)",
          textAlign: "center",
        }}>
          {isGrowing ? "→" : "→"}
        </div>

        {/* Forecast */}
        <div style={{
          padding: "14px 16px", borderRadius: 10,
          backgroundColor: levelBg(forecast.forecast.level),
          textAlign: "center",
          border: forecast.will_escalate ? `2px solid ${forecastColor}` : "none",
        }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: "var(--color-ink-3)", marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.05em" }}>
            {forecast.days} Hari Lagi
          </div>
          <div style={{ fontSize: 28, fontWeight: 800, color: forecastColor, lineHeight: 1 }}>
            {forecast.forecast.score}
          </div>
          <div style={{ fontSize: 10, color: "var(--color-ink-3)", marginTop: 2 }}>/ 100</div>
          <div style={{
            marginTop: 8, padding: "3px 10px", borderRadius: 999,
            backgroundColor: forecastColor, color: "white",
            fontSize: 10, fontWeight: 700, display: "inline-block",
          }}>
            {forecast.forecast.level_display}
            {forecast.will_escalate && " ⚠"}
          </div>
        </div>
      </div>

      {/* ── Escalation warning ── */}
      {forecast.will_escalate && (
        <div style={{
          marginBottom: 12, padding: "8px 12px",
          backgroundColor: "var(--color-danger-light)",
          borderRadius: 8, fontSize: 11,
          color: "var(--color-danger)",
          display: "flex", alignItems: "center", gap: 6,
        }}>
          <span style={{ fontSize: 14 }}>⚠</span>
          <span>
            <strong>Tingkat risiko akan naik</strong> dari {forecast.current.level_display} ke {forecast.forecast.level_display} dalam {forecast.days} hari jika tidak ada tindakan.
          </span>
        </div>
      )}

      {/* ── Top drivers ── */}
      {forecast.top_drivers.length > 0 && (
        <div>
          <div style={{
            fontSize: 10, fontWeight: 700, color: "var(--color-ink-3)",
            textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8,
          }}>
            Faktor Risiko
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {forecast.top_drivers.map((driver) => (
              <div key={driver.key} style={{
                display: "flex", alignItems: "flex-start",
                gap: 10, padding: "8px 10px", borderRadius: 8,
                backgroundColor: driver.is_new || driver.delta_points > 0
                  ? "var(--color-warning-light)"
                  : "var(--color-paper-2)",
              }}>
                {/* Points indicator */}
                <div style={{ flexShrink: 0, textAlign: "center", minWidth: 36 }}>
                  <div style={{
                    fontSize: 13, fontWeight: 800,
                    color: driver.delta_points > 0 ? "var(--color-danger)" :
                           driver.is_new          ? "var(--color-warning)" :
                                                    "var(--color-ink-3)",
                  }}>
                    {driver.forecast_points}
                  </div>
                  <div style={{ fontSize: 9, color: "var(--color-ink-3)" }}>pts</div>
                </div>
                {/* Driver info */}
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: "var(--color-ink)", lineHeight: 1.3 }}>
                    {driver.name}
                    {driver.is_new && (
                      <span style={{
                        marginLeft: 6, fontSize: 9, fontWeight: 700,
                        padding: "1px 5px", borderRadius: 3,
                        backgroundColor: "var(--color-warning)",
                        color: "white",
                      }}>
                        Baru
                      </span>
                    )}
                  </div>
                  {driver.delta_points > 0 && (
                    <div style={{ fontSize: 10, color: "var(--color-danger)", marginTop: 2 }}>
                      ↑ +{driver.delta_points} pts dari saat ini
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Stable message ── */}
      {isStable && forecast.top_drivers.length === 0 && (
        <div style={{
          textAlign: "center", padding: "12px 0",
          fontSize: 12, color: "var(--color-success)",
        }}>
          ✅ Tidak ada faktor risiko yang diproyeksikan dalam {forecast.days} hari ke depan
        </div>
      )}
    </div>
  );
}
