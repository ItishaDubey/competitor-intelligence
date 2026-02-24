import { useState, useEffect, useContext } from "react";
import { AuthContext } from "../context/AuthContext";
import api from "../api/client";

const METRIC_CARDS = [
  { key: "competitors",      label: "Competitors",      icon: "👥", color: "#4f6ef7" },
  { key: "reports",          label: "Reports",          icon: "📋", color: "#10b981" },
  { key: "active_monitors",  label: "Active Monitors",  icon: "📡", color: "#f59e0b" },
  { key: "changes_detected", label: "Changes Detected", icon: "⚡", color: "#ef4444" },
];

export default function Dashboard() {
  const { user } = useContext(AuthContext);
  const [stats, setStats]       = useState(null);
  const [report, setReport]     = useState(null);
  const [scanning, setScanning] = useState(false);
  const [loading, setLoading]   = useState(true);
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [s, r] = await Promise.all([
        api.get("/dashboard/stats"),
        api.get("/reports/latest").catch(() => null),
      ]);
      setStats(s.data);
      if (r) setReport(r.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function runScan() {
    setScanning(true);
    try {
      await api.post("/reports/run");
      // Poll every 5s for up to 3 min
      let tries = 0;
      const poll = setInterval(async () => {
        tries++;
        await loadData();
        if (tries > 36) clearInterval(poll);
      }, 5000);
      setTimeout(() => {
        clearInterval(poll);
        setScanning(false);
      }, 180_000);
    } catch (e) {
      setScanning(false);
    }
  }

  const digest = report?.digest;

  return (
    <div style={styles.page}>

      {/* ── Top Bar ── */}
      <div style={styles.topBar}>
        <div>
          <h1 style={styles.pageTitle}>Dashboard</h1>
          <p style={styles.pageSub}>Monitor your competitive landscape</p>
        </div>
        <button
          onClick={runScan}
          disabled={scanning}
          style={{ ...styles.btn, opacity: scanning ? 0.7 : 1 }}
          data-testid="run-scan-btn"
        >
          {scanning ? (
            <><span style={styles.spinner} />Scanning…</>
          ) : (
            <><span>⟳</span> Run Scan Now</>
          )}
        </button>
      </div>

      {/* ── Stat Cards ── */}
      <div style={styles.statsGrid}>
        {METRIC_CARDS.map((m) => (
          <div key={m.key} style={styles.statCard}>
            <div style={{ ...styles.statIcon, background: m.color + "22", color: m.color }}>
              {m.icon}
            </div>
            <div>
              <div style={styles.statLabel}>{m.label}</div>
              <div style={styles.statNum}>
                {loading ? "—" : (stats?.[m.key] ?? 0)}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* ── Tabs ── */}
      <div style={styles.tabs}>
        {["overview", "competitors", "changes", "insights"].map((t) => (
          <button
            key={t}
            onClick={() => setActiveTab(t)}
            style={{
              ...styles.tab,
              ...(activeTab === t ? styles.tabActive : {}),
            }}
          >
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {/* ── Content ── */}
      {!digest && !loading && (
        <div style={styles.emptyState}>
          <div style={styles.emptyIcon}>🔍</div>
          <div style={styles.emptyTitle}>No report yet</div>
          <div style={styles.emptySub}>Click "Run Scan Now" to generate your first competitive intelligence report.</div>
        </div>
      )}

      {digest && activeTab === "overview"    && <OverviewTab  digest={digest} stats={stats} />}
      {digest && activeTab === "competitors" && <CompetitorsTab digest={digest} />}
      {digest && activeTab === "changes"     && <ChangesTab digest={digest} />}
      {digest && activeTab === "insights"    && <InsightsTab digest={digest} />}

    </div>
  );
}

/* ════════════════════════════════════════════════════════════
   OVERVIEW TAB – pricing matrix + gaps summary
════════════════════════════════════════════════════════════ */
function OverviewTab({ digest, stats }) {
  const baseline = digest?.baseline || {};
  const comps    = digest?.competitors || [];

  return (
    <div style={styles.tabContent}>
      {/* Baseline summary */}
      <div style={styles.card}>
        <div style={styles.cardTitle}>🏠 Baseline: {baseline.name}</div>
        <div style={styles.baselineStats}>
          <div style={styles.bStat}>
            <span style={styles.bNum}>{baseline.products?.length || 0}</span>
            <span style={styles.bLbl}>Products Tracked</span>
          </div>
          {comps.map((c) => (
            <div key={c.name} style={styles.bStat}>
              <span style={styles.bNum}>{c.diff?.missing?.length || 0}</span>
              <span style={styles.bLbl}>Gaps vs {c.name}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Pricing Matrix */}
      <PricingMatrix baseline={baseline} competitors={comps} />
    </div>
  );
}

function PricingMatrix({ baseline, competitors }) {
  const products = baseline?.products?.slice(0, 30) || [];
  if (!products.length) return <div style={styles.card}><p style={styles.muted}>No baseline products extracted yet.</p></div>;

  // Build price maps
  const compMaps = {};
  competitors.forEach((c) => {
    const m = {};
    (c.products || []).forEach((p) => {
      const k = `${p.signature}__${p.variant_value}`;
      m[k] = p.price;
      const fb = `${p.signature}__null`;
      if (!m[fb]) m[fb] = p.price;
    });
    compMaps[c.name] = m;
  });

  function fmtPrice(v) {
    if (v == null) return "–";
    const n = parseFloat(v);
    if (isNaN(n)) return String(v);
    return `₹${n.toLocaleString("en-IN")}`;
  }

  return (
    <div style={styles.card}>
      <div style={styles.cardTitle}>📊 Pricing Comparison</div>
      <div style={{ overflowX: "auto" }}>
        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>Product</th>
              <th style={styles.th}>Variant</th>
              <th style={styles.th}>Baseline Price</th>
              {competitors.map((c) => (
                <th key={c.name} style={styles.th}>{c.name} Price</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {products.map((p, i) => {
              const sig = p.signature;
              const vari = p.variant_value;
              const k = `${sig}__${vari}`;
              const kb = `${sig}__null`;

              return (
                <tr key={i} style={i % 2 === 0 ? {} : { background: "#f9faff" }}>
                  <td style={{ ...styles.td, fontWeight: 500 }}>{p.name}</td>
                  <td style={{ ...styles.td, color: "#888" }}>{vari ? fmtPrice(vari) : "–"}</td>
                  <td style={styles.td}>{fmtPrice(p.price)}</td>
                  {competitors.map((c) => {
                    const m = compMaps[c.name] || {};
                    const cp = m[k] ?? m[kb];
                    let cellStyle = styles.td;
                    let badge = null;
                    if (cp && p.price) {
                      const diff = (parseFloat(cp) - parseFloat(p.price)) / parseFloat(p.price) * 100;
                      if (diff < -3) { cellStyle = { ...styles.td, color: "#e34b4b" }; badge = <span style={styles.badgeDown}>▼{Math.abs(diff).toFixed(0)}%</span>; }
                      else if (diff > 3) { cellStyle = { ...styles.td, color: "#10b981" }; badge = <span style={styles.badgeUp}>▲{diff.toFixed(0)}%</span>; }
                    }
                    return <td key={c.name} style={cellStyle}>{fmtPrice(cp)}{badge}</td>;
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ════════════════════════════════════════════════════════════
   COMPETITORS TAB – per-competitor product + variant gaps
════════════════════════════════════════════════════════════ */
function CompetitorsTab({ digest }) {
  const comps = digest?.competitors || [];

  return (
    <div style={styles.tabContent}>
      {comps.map((c) => (
        <div key={c.name} style={styles.card}>
          <div style={styles.cardTitle}>🎯 {c.name}</div>

          <div style={styles.compStatRow}>
            <StatPill label="Total Products" value={c.products?.length || 0} color="#4f6ef7" />
            <StatPill label="Matched" value={c.diff?.matched?.length || 0} color="#10b981" />
            <StatPill label="Product Gaps" value={c.diff?.missing?.length || 0} color="#ef4444" />
            <StatPill label="Variant Gaps" value={c.diff?.variant_gaps?.length || 0} color="#f59e0b" />
            <StatPill label="Price Diffs" value={c.diff?.price_diffs?.length || 0} color="#8b5cf6" />
          </div>

          {/* Product gaps */}
          {c.diff?.missing?.length > 0 && (
            <div style={{ marginTop: 20 }}>
              <div style={styles.subTitle}>🕳️ Missing from Baseline</div>
              <div style={styles.chipGrid}>
                {c.diff.missing.slice(0, 16).map((p, i) => (
                  <div key={i} style={styles.chip}>{p.name}</div>
                ))}
                {c.diff.missing.length > 16 && (
                  <div style={{ ...styles.chip, background: "#f0f0f0", color: "#888" }}>
                    +{c.diff.missing.length - 16} more
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Variant gaps */}
          {c.diff?.variant_gaps?.length > 0 && (
            <div style={{ marginTop: 20 }}>
              <div style={styles.subTitle}>↔️ Variant Gaps</div>
              <table style={styles.table}>
                <thead>
                  <tr>
                    <th style={styles.th}>Product</th>
                    <th style={styles.th}>Missing Denomination</th>
                    <th style={styles.th}>Competitor Price</th>
                  </tr>
                </thead>
                <tbody>
                  {c.diff.variant_gaps.slice(0, 12).map((g, i) => (
                    <tr key={i}>
                      <td style={styles.td}>{g.product_name}</td>
                      <td style={{ ...styles.td, fontFamily: "monospace" }}>₹{g.missing_variant?.toLocaleString("en-IN") || "–"}</td>
                      <td style={{ ...styles.td, fontFamily: "monospace" }}>₹{g.competitor_price?.toLocaleString("en-IN") || "–"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Price diffs */}
          {c.diff?.price_diffs?.length > 0 && (
            <div style={{ marginTop: 20 }}>
              <div style={styles.subTitle}>💰 Price Differences</div>
              <table style={styles.table}>
                <thead>
                  <tr>
                    <th style={styles.th}>Product</th>
                    <th style={styles.th}>Variant</th>
                    <th style={styles.th}>Baseline</th>
                    <th style={styles.th}>Competitor</th>
                    <th style={styles.th}>Δ</th>
                  </tr>
                </thead>
                <tbody>
                  {c.diff.price_diffs.slice(0, 12).map((d, i) => (
                    <tr key={i}>
                      <td style={styles.td}>{d.product_name}</td>
                      <td style={styles.td}>{d.variant ? `₹${d.variant}` : "–"}</td>
                      <td style={styles.td}>₹{d.baseline_price?.toLocaleString("en-IN")}</td>
                      <td style={styles.td}>₹{d.competitor_price?.toLocaleString("en-IN")}</td>
                      <td style={styles.td}>
                        <span style={d.pct_diff < 0 ? styles.badgeDown : styles.badgeUp}>
                          {d.pct_diff > 0 ? "▲" : "▼"}{Math.abs(d.pct_diff).toFixed(1)}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

/* ════════════════════════════════════════════════════════════
   CHANGES TAB
════════════════════════════════════════════════════════════ */
function ChangesTab({ digest }) {
  const ch = digest?.changes || {};
  const changes = ch.changes || [];

  if (ch.status === "first_run" || !changes.length) {
    return (
      <div style={styles.tabContent}>
        <div style={styles.card}>
          <p style={styles.muted}>
            {ch.status === "first_run"
              ? "This is the first run. Daily changes will appear after the next scan."
              : "✅ No changes detected since last scan."}
          </p>
        </div>
      </div>
    );
  }

  const typeConfig = {
    new_sku:      { icon: "🆕", label: "New SKU",      bg: "#f0fff7", border: "#a7f3d0" },
    removed_sku:  { icon: "🗑️", label: "Removed",      bg: "#fff5f5", border: "#fca5a5" },
    price_change: { icon: "💰", label: "Price Change",  bg: "#fffbf0", border: "#fcd34d" },
  };

  return (
    <div style={styles.tabContent}>
      <div style={styles.card}>
        <div style={styles.cardTitle}>📈 Daily Changes ({changes.length} detected)</div>
        <div style={styles.changesGrid}>
          {changes.map((c, i) => {
            const cfg = typeConfig[c.type] || { icon: "•", label: c.type, bg: "#f8f9ff", border: "#ccc" };
            let detail = "";
            if (c.type === "new_sku") detail = `₹${c.price || "?"}`;
            else if (c.type === "removed_sku") detail = `Was ₹${c.old_price || "?"}`;
            else if (c.type === "price_change") {
              const arrow = c.pct_change > 0 ? "▲" : "▼";
              detail = `₹${c.old_price} → ₹${c.new_price} ${arrow}${Math.abs(c.pct_change).toFixed(1)}%`;
            }
            return (
              <div key={i} style={{ ...styles.changeCard, background: cfg.bg, borderColor: cfg.border }}>
                <span style={{ fontSize: 22 }}>{cfg.icon}</span>
                <div>
                  <div style={{ fontSize: "0.72rem", fontWeight: 700, color: "#888", textTransform: "uppercase", letterSpacing: "0.5px" }}>{c.competitor} · {cfg.label}</div>
                  <div style={{ fontWeight: 600, fontSize: "0.9rem", marginTop: 2 }}>{c.product}</div>
                  <div style={{ fontSize: "0.82rem", fontFamily: "monospace", color: "#666", marginTop: 2 }}>{detail}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

/* ════════════════════════════════════════════════════════════
   INSIGHTS TAB
════════════════════════════════════════════════════════════ */
function InsightsTab({ digest }) {
  const comps = digest?.competitors || [];

  return (
    <div style={styles.tabContent}>
      {comps.map((c) => {
        const ins = c.insights || {};
        if (typeof ins === "string") {
          return (
            <div key={c.name} style={styles.card}>
              <div style={styles.cardTitle}>🎯 {c.name}</div>
              <pre style={{ whiteSpace: "pre-wrap", fontSize: "0.9rem", lineHeight: 1.7 }}>{ins}</pre>
            </div>
          );
        }
        return (
          <div key={c.name} style={styles.card}>
            <div style={styles.cardTitle}>🎯 {c.name}</div>
            {ins.summary && (
              <p style={{ ...styles.insightSummary, marginBottom: 20 }}>{ins.summary}</p>
            )}
            <div style={styles.insightGrid}>
              <InsightCol title="🕳️ Product Gaps"   items={ins.product_gaps}   listStyle={styles.listDefault} />
              <InsightCol title="↔️ Variant Gaps"   items={ins.variant_gaps}   listStyle={styles.listDefault} />
              <InsightCol title="⚠️ Pricing Risks"  items={ins.pricing_risks}  listStyle={styles.listDanger} />
              <InsightCol title="✅ Recommendations" items={ins.recommendations} listStyle={styles.listSuccess} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function InsightCol({ title, items, listStyle }) {
  return (
    <div>
      <div style={styles.insightColTitle}>{title}</div>
      {(!items || !items.length)
        ? <p style={styles.muted}>None identified.</p>
        : <ul style={{ listStyle: "none", padding: 0, display: "flex", flexDirection: "column", gap: 6 }}>
            {items.map((item, i) => (
              <li key={i} style={{ ...styles.insightItem, ...listStyle }}>{item}</li>
            ))}
          </ul>
      }
    </div>
  );
}

/* ── Micro components ── */
function StatPill({ label, value, color }) {
  return (
    <div style={{ textAlign: "center" }}>
      <div style={{ fontSize: "1.6rem", fontWeight: 700, color }}>{value}</div>
      <div style={{ fontSize: "0.72rem", color: "#888", marginTop: 2 }}>{label}</div>
    </div>
  );
}

/* ════════════════════════════════════════════════════════════
   STYLES
════════════════════════════════════════════════════════════ */
const styles = {
  page: {
    padding: "32px 40px",
    minHeight: "100vh",
    background: "#f0f2f7",
    fontFamily: "'DM Sans', 'Inter', sans-serif",
  },
  topBar: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 28,
  },
  pageTitle: { fontSize: "1.8rem", fontWeight: 700, color: "#1a1f36", marginBottom: 4 },
  pageSub:   { fontSize: "0.9rem", color: "#888" },
  btn: {
    display: "flex", alignItems: "center", gap: 8,
    background: "linear-gradient(135deg, #2d3a8c 0%, #4f6ef7 100%)",
    color: "#fff", border: "none", borderRadius: 10,
    padding: "11px 22px", fontSize: "0.92rem", fontWeight: 600,
    cursor: "pointer", boxShadow: "0 2px 12px rgba(79,110,247,.35)",
  },
  spinner: {
    display: "inline-block", width: 14, height: 14,
    border: "2px solid #ffffff55", borderTopColor: "#fff",
    borderRadius: "50%", animation: "spin 0.7s linear infinite",
  },
  statsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
    gap: 16, marginBottom: 24,
  },
  statCard: {
    background: "#fff", borderRadius: 12, border: "1px solid #e3e7ef",
    padding: "18px 22px", display: "flex", alignItems: "center", gap: 16,
    boxShadow: "0 1px 3px rgba(0,0,0,.04)",
  },
  statIcon: { width: 44, height: 44, borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20 },
  statLabel: { fontSize: "0.78rem", color: "#888", marginBottom: 2, textTransform: "uppercase", letterSpacing: "0.5px" },
  statNum:   { fontSize: "1.7rem", fontWeight: 700, color: "#1a1f36" },
  tabs: { display: "flex", gap: 4, marginBottom: 20 },
  tab: {
    padding: "8px 20px", borderRadius: 8, border: "1px solid #e3e7ef",
    background: "#fff", cursor: "pointer", fontSize: "0.88rem", fontWeight: 500,
    color: "#555", transition: "all 0.15s",
  },
  tabActive: { background: "#2d3a8c", color: "#fff", borderColor: "#2d3a8c" },
  tabContent: { display: "flex", flexDirection: "column", gap: 20 },
  card: {
    background: "#fff", borderRadius: 14, border: "1px solid #e3e7ef",
    padding: "24px 28px", boxShadow: "0 1px 4px rgba(0,0,0,.04)",
  },
  cardTitle: {
    fontSize: "1.05rem", fontWeight: 700, color: "#2d3a8c",
    marginBottom: 18, paddingBottom: 12, borderBottom: "2px solid #e3e7ef",
  },
  baselineStats: { display: "flex", gap: 36 },
  bStat:  { display: "flex", flexDirection: "column", gap: 2 },
  bNum:   { fontSize: "2rem", fontWeight: 700, color: "#2d3a8c" },
  bLbl:   { fontSize: "0.8rem", color: "#888" },
  table:  { width: "100%", borderCollapse: "collapse", fontSize: "0.86rem" },
  th: { background: "#f6f8fe", border: "1px solid #e3e7ef", padding: "9px 14px", textAlign: "left", fontWeight: 600, color: "#2d3a8c", whiteSpace: "nowrap" },
  td: { border: "1px solid #e3e7ef", padding: "8px 14px", fontFamily: "monospace" },
  badgeUp:   { display: "inline-block", background: "#e6f9f0", color: "#10b981", fontSize: "0.72rem", fontWeight: 700, padding: "2px 6px", borderRadius: 4, marginLeft: 4 },
  badgeDown: { display: "inline-block", background: "#fce8e8", color: "#ef4444", fontSize: "0.72rem", fontWeight: 700, padding: "2px 6px", borderRadius: 4, marginLeft: 4 },
  muted:  { color: "#888", fontStyle: "italic", fontSize: "0.9rem" },
  subTitle: { fontSize: "0.85rem", fontWeight: 700, color: "#555", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 10 },
  chipGrid: { display: "flex", flexWrap: "wrap", gap: 8 },
  chip: { background: "#eef1ff", color: "#2d3a8c", fontSize: "0.8rem", fontWeight: 500, padding: "5px 12px", borderRadius: 20 },
  compStatRow: { display: "flex", gap: 28, flexWrap: "wrap", marginBottom: 4 },
  changesGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 12, marginTop: 4 },
  changeCard: { display: "flex", gap: 12, alignItems: "flex-start", padding: "12px 16px", borderRadius: 10, border: "1px solid" },
  insightSummary: {
    background: "#f6f8fe", borderLeft: "4px solid #4f6ef7",
    padding: "12px 16px", borderRadius: "0 8px 8px 0",
    fontSize: "0.92rem", lineHeight: 1.6, color: "#1a1f36",
  },
  insightGrid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 },
  insightColTitle: { fontSize: "0.78rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.8px", color: "#888", marginBottom: 8 },
  insightItem: { fontSize: "0.87rem", padding: "6px 10px 6px 14px", borderLeft: "3px solid #ccc", lineHeight: 1.45, borderRadius: "0 4px 4px 0" },
  listDefault: { borderLeftColor: "#4f6ef7", background: "#f6f8fe" },
  listDanger:  { borderLeftColor: "#ef4444", background: "#fff9f9" },
  listSuccess: { borderLeftColor: "#10b981", background: "#f3fdf8" },
  emptyState: { textAlign: "center", padding: "80px 40px" },
  emptyIcon:  { fontSize: "3rem", marginBottom: 12 },
  emptyTitle: { fontSize: "1.2rem", fontWeight: 700, color: "#1a1f36", marginBottom: 8 },
  emptySub:   { fontSize: "0.9rem", color: "#888", maxWidth: 420, margin: "0 auto" },
};