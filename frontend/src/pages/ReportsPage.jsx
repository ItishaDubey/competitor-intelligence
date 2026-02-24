import { useState, useEffect } from "react";
import api from "../api/client";

export default function Reports() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(null);

  useEffect(() => { loadReports(); }, []);

  async function loadReports() {
    setLoading(true);
    try {
      const res = await api.get("/reports");
      setReports(res.data);
    } finally {
      setLoading(false);
    }
  }

  async function viewReport(id) {
    if (expanded === id) { setExpanded(null); return; }
    setExpanded(id);
  }

  return (
    <div style={styles.page}>
      <div style={styles.topBar}>
        <div>
          <h1 style={styles.pageTitle}>Reports</h1>
          <p style={styles.pageSub}>{reports.length} intelligence reports generated</p>
        </div>
      </div>

      {loading && <p style={styles.muted}>Loading…</p>}

      {!loading && !reports.length && (
        <div style={styles.emptyState}>
          <div style={{ fontSize: "2.5rem", marginBottom: 12 }}>📋</div>
          <div style={{ fontWeight: 700, marginBottom: 8 }}>No reports yet</div>
          <div style={styles.muted}>Run a scan from the Dashboard to generate your first report.</div>
        </div>
      )}

      <div style={styles.list}>
        {reports.map((r) => (
          <div key={r.id} style={styles.card}>
            <div style={styles.cardHeader}>
              <div>
                <div style={styles.reportDate}>📊 {r.report_date || r.created_at?.slice(0, 10)}</div>
                <div style={styles.reportMeta}>
                  <span style={r.status === "success" ? styles.badgeSuccess : styles.badgeError}>
                    {r.status === "success" ? "✅ Success" : "❌ Error"}
                  </span>
                  {r.changes_count !== undefined && (
                    <span style={styles.chip}>⚡ {r.changes_count} changes</span>
                  )}
                  {r.gaps_count !== undefined && (
                    <span style={styles.chip}>🕳️ {r.gaps_count} gaps</span>
                  )}
                </div>
              </div>
              <div style={styles.cardActions}>
                <button style={styles.viewBtn} onClick={() => viewReport(r.id)}>
                  {expanded === r.id ? "Collapse" : "View Details"}
                </button>
              </div>
            </div>

            {expanded === r.id && r.digest && (
              <ReportDetail digest={r.digest} />
            )}
            {expanded === r.id && r.error && (
              <div style={styles.errorBox}>{r.error}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function ReportDetail({ digest }) {
  const comps = digest?.competitors || [];
  const changes = digest?.changes?.changes || [];

  return (
    <div style={styles.detail}>
      <div style={styles.detailSection}>
        <div style={styles.sectionTitle}>Baseline: {digest?.baseline?.name}</div>
        <p style={{ color: "#555", fontSize: "0.9rem" }}>
          {digest?.baseline?.products?.length || 0} products tracked
        </p>
      </div>

      {comps.map((c) => (
        <div key={c.name} style={styles.detailSection}>
          <div style={styles.sectionTitle}>🎯 {c.name}</div>
          <div style={styles.statsRow}>
            <Stat n={c.products?.length || 0} label="Total Products" />
            <Stat n={c.diff?.matched?.length || 0} label="Matched" />
            <Stat n={c.diff?.missing?.length || 0} label="Gaps" />
            <Stat n={c.diff?.variant_gaps?.length || 0} label="Variant Gaps" />
          </div>

          {c.insights?.summary && (
            <div style={styles.summary}>{c.insights.summary}</div>
          )}

          {c.insights?.recommendations?.length > 0 && (
            <div>
              <div style={styles.subLabel}>Recommendations</div>
              <ul style={styles.recList}>
                {c.insights.recommendations.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            </div>
          )}
        </div>
      ))}

      {changes.length > 0 && (
        <div style={styles.detailSection}>
          <div style={styles.sectionTitle}>📈 Changes ({changes.length})</div>
          <div style={styles.changesList}>
            {changes.slice(0, 10).map((ch, i) => (
              <div key={i} style={styles.changeItem}>
                <span style={styles.changeType}>{ch.type.replace("_", " ").toUpperCase()}</span>
                <span>{ch.product}</span>
                {ch.pct_change && <span style={{ color: ch.pct_change < 0 ? "#ef4444" : "#10b981" }}>
                  {ch.pct_change > 0 ? "▲" : "▼"}{Math.abs(ch.pct_change).toFixed(1)}%
                </span>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({ n, label }) {
  return (
    <div style={{ textAlign: "center" }}>
      <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#2d3a8c" }}>{n}</div>
      <div style={{ fontSize: "0.72rem", color: "#888" }}>{label}</div>
    </div>
  );
}

const styles = {
  page: { padding: "32px 40px", minHeight: "100vh", background: "#f0f2f7", fontFamily: "'DM Sans','Inter',sans-serif" },
  topBar: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 28 },
  pageTitle: { fontSize: "1.8rem", fontWeight: 700, color: "#1a1f36", marginBottom: 4 },
  pageSub:   { fontSize: "0.9rem", color: "#888" },
  muted: { color: "#888", fontSize: "0.9rem" },
  emptyState: { textAlign: "center", padding: "80px 40px", color: "#888" },
  list: { display: "flex", flexDirection: "column", gap: 16 },
  card: { background: "#fff", borderRadius: 14, border: "1px solid #e3e7ef", padding: "20px 24px", boxShadow: "0 1px 4px rgba(0,0,0,.04)" },
  cardHeader: { display: "flex", justifyContent: "space-between", alignItems: "flex-start" },
  reportDate: { fontWeight: 600, fontSize: "1rem", color: "#1a1f36", marginBottom: 8 },
  reportMeta: { display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" },
  badgeSuccess: { background: "#f0fff7", color: "#10b981", fontSize: "0.78rem", fontWeight: 700, padding: "3px 10px", borderRadius: 20 },
  badgeError:   { background: "#fff5f5", color: "#ef4444", fontSize: "0.78rem", fontWeight: 700, padding: "3px 10px", borderRadius: 20 },
  chip: { background: "#f0f2f7", color: "#555", fontSize: "0.78rem", padding: "3px 10px", borderRadius: 20 },
  cardActions: { display: "flex", gap: 10 },
  viewBtn: { padding: "8px 18px", borderRadius: 8, border: "1px solid #2d3a8c", background: "none", color: "#2d3a8c", cursor: "pointer", fontWeight: 600, fontSize: "0.85rem" },
  detail: { marginTop: 20, borderTop: "1px solid #e3e7ef", paddingTop: 20, display: "flex", flexDirection: "column", gap: 20 },
  detailSection: { background: "#f8f9ff", borderRadius: 10, padding: "16px 20px" },
  sectionTitle: { fontWeight: 700, color: "#2d3a8c", marginBottom: 12, fontSize: "0.95rem" },
  statsRow: { display: "flex", gap: 28, marginBottom: 12 },
  summary: { background: "#fff", border: "1px solid #c7d2fe", borderRadius: 8, padding: "10px 14px", fontSize: "0.88rem", lineHeight: 1.6, marginTop: 8, marginBottom: 12 },
  subLabel: { fontSize: "0.72rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.5px", color: "#888", marginBottom: 8 },
  recList: { paddingLeft: 18, fontSize: "0.88rem", lineHeight: 1.8, color: "#444" },
  changesList: { display: "flex", flexDirection: "column", gap: 6 },
  changeItem: { display: "flex", gap: 12, alignItems: "center", fontSize: "0.86rem" },
  changeType: { background: "#eef1ff", color: "#2d3a8c", fontSize: "0.7rem", fontWeight: 700, padding: "2px 8px", borderRadius: 4 },
  errorBox: { background: "#fff5f5", border: "1px solid #fca5a5", borderRadius: 8, padding: "12px 16px", color: "#ef4444", fontSize: "0.88rem", marginTop: 16 },
};