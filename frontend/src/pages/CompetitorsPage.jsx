import { useState, useEffect, useContext } from "react";
import api from "../api/client";

export default function Competitors() {
  const [competitors, setCompetitors] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadCompetitors(); }, []);

  async function loadCompetitors() {
    setLoading(true);
    try {
      const res = await api.get("/competitors");
      setCompetitors(res.data);
    } finally {
      setLoading(false);
    }
  }

  async function deleteCompetitor(id) {
    if (!confirm("Delete this competitor?")) return;
    await api.delete(`/competitors/${id}`);
    loadCompetitors();
  }

  const baseline = competitors.find((c) => c.is_baseline);
  const others   = competitors.filter((c) => !c.is_baseline);

  return (
    <div style={styles.page}>
      <div style={styles.topBar}>
        <div>
          <h1 style={styles.pageTitle}>Competitors</h1>
          <p style={styles.pageSub}>Configure companies to monitor</p>
        </div>
        <button style={styles.btn} onClick={() => { setEditing(null); setShowModal(true); }}
          data-testid="add-competitor-btn">
          + Add Competitor
        </button>
      </div>

      {loading && <p style={styles.muted}>Loading…</p>}

      {!loading && !competitors.length && (
        <div style={styles.emptyState}>
          <div style={{ fontSize: "2.5rem", marginBottom: 12 }}>🏢</div>
          <div style={{ fontWeight: 700, fontSize: "1.1rem", marginBottom: 8 }}>No competitors yet</div>
          <div style={styles.muted}>Add your own company as the baseline, then add competitors to monitor.</div>
        </div>
      )}

      {baseline && (
        <div style={{ marginBottom: 24 }}>
          <div style={styles.sectionLabel}>BASELINE (YOUR COMPANY)</div>
          <CompetitorCard c={baseline} onEdit={() => { setEditing(baseline); setShowModal(true); }} onDelete={() => deleteCompetitor(baseline.id)} />
        </div>
      )}

      {others.length > 0 && (
        <div>
          <div style={styles.sectionLabel}>COMPETITORS</div>
          <div style={styles.list}>
            {others.map((c) => (
              <CompetitorCard key={c.id} c={c}
                onEdit={() => { setEditing(c); setShowModal(true); }}
                onDelete={() => deleteCompetitor(c.id)} />
            ))}
          </div>
        </div>
      )}

      {showModal && (
        <CompetitorModal
          competitor={editing}
          onClose={() => setShowModal(false)}
          onSaved={() => { setShowModal(false); loadCompetitors(); }}
        />
      )}
    </div>
  );
}

function CompetitorCard({ c, onEdit, onDelete }) {
  return (
    <div style={styles.card}>
      <div style={styles.cardLeft}>
        <span style={{ ...styles.dot, background: "#10b981" }} />
        <div>
          <div style={styles.cardName}>
            {c.name}
            {c.is_baseline && <span style={styles.baselineBadge}>Baseline</span>}
            <span style={styles.activeBadge}>Active</span>
          </div>
          <div style={styles.cardUrl}>{c.website}</div>
          {c.last_checked && (
            <div style={styles.cardMeta}>Last checked: {c.last_checked}</div>
          )}
        </div>
      </div>
      <div style={styles.cardActions}>
        <button style={styles.iconBtn} onClick={onEdit} title="Edit">✏️</button>
        <button style={{ ...styles.iconBtn, color: "#ef4444" }} onClick={onDelete} title="Delete">🗑</button>
      </div>
    </div>
  );
}

function CompetitorModal({ competitor, onClose, onSaved }) {
  const [form, setForm] = useState({
    name: competitor?.name || "",
    website: competitor?.website || "",
    is_baseline: competitor?.is_baseline || false,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError]   = useState("");

  async function save() {
    if (!form.name.trim() || !form.website.trim()) {
      setError("Name and website URL are required."); return;
    }
    setSaving(true);
    setError("");
    try {
      if (competitor?.id) {
        await api.put(`/competitors/${competitor.id}`, form);
      } else {
        await api.post("/competitors", form);
      }
      onSaved();
    } catch (e) {
      setError(e.response?.data?.detail || "Save failed");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div style={styles.overlay}>
      <div style={styles.modal}>
        <div style={styles.modalHeader}>
          <div style={{ fontWeight: 700, fontSize: "1.1rem" }}>
            {competitor ? "Edit Competitor" : "Add Competitor"}
          </div>
          <button style={styles.closeBtn} onClick={onClose}>✕</button>
        </div>

        <p style={styles.modalSub}>Configure a company to monitor</p>

        <div style={styles.fieldRow}>
          <div style={styles.field}>
            <label style={styles.label}>Company Name *</label>
            <input style={styles.input} placeholder="e.g. Woohoo" value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Website URL *</label>
            <input style={styles.input} placeholder="https://example.com/products" value={form.website}
              onChange={(e) => setForm({ ...form, website: e.target.value })} />
          </div>
        </div>

        <label style={styles.checkRow}>
          <input type="checkbox" checked={form.is_baseline}
            onChange={(e) => setForm({ ...form, is_baseline: e.target.checked })} />
          <span style={{ marginLeft: 8 }}>Set as baseline (your company) for comparison</span>
        </label>

        <div style={styles.modalHint}>
          <strong>Tip:</strong> For best results, use a product listing page URL — e.g. a category page or search results page that lists multiple products/gift cards.
        </div>

        {error && <div style={styles.errorMsg}>{error}</div>}

        <div style={styles.modalFooter}>
          <button style={styles.cancelBtn} onClick={onClose}>Cancel</button>
          <button style={styles.saveBtn} onClick={save} disabled={saving}>
            {saving ? "Saving…" : (competitor ? "Update Competitor" : "Add Competitor")}
          </button>
        </div>
      </div>
    </div>
  );
}

const styles = {
  page: { padding: "32px 40px", minHeight: "100vh", background: "#f0f2f7", fontFamily: "'DM Sans','Inter',sans-serif" },
  topBar: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 28 },
  pageTitle: { fontSize: "1.8rem", fontWeight: 700, color: "#1a1f36", marginBottom: 4 },
  pageSub:   { fontSize: "0.9rem", color: "#888" },
  btn: {
    background: "linear-gradient(135deg, #2d3a8c 0%, #4f6ef7 100%)",
    color: "#fff", border: "none", borderRadius: 10,
    padding: "11px 22px", fontSize: "0.92rem", fontWeight: 600,
    cursor: "pointer", boxShadow: "0 2px 12px rgba(79,110,247,.3)",
  },
  sectionLabel: { fontSize: "0.72rem", fontWeight: 700, letterSpacing: "1px", color: "#888", textTransform: "uppercase", marginBottom: 10 },
  list: { display: "flex", flexDirection: "column", gap: 12 },
  card: {
    background: "#fff", borderRadius: 12, border: "1px solid #e3e7ef",
    padding: "18px 22px", display: "flex", justifyContent: "space-between",
    alignItems: "center", boxShadow: "0 1px 3px rgba(0,0,0,.04)",
  },
  cardLeft: { display: "flex", gap: 14, alignItems: "flex-start" },
  dot: { width: 10, height: 10, borderRadius: "50%", marginTop: 6, flexShrink: 0 },
  cardName: { fontWeight: 600, fontSize: "1rem", color: "#1a1f36", display: "flex", alignItems: "center", gap: 8, marginBottom: 3 },
  cardUrl:  { fontSize: "0.82rem", color: "#4f6ef7", marginBottom: 3 },
  cardMeta: { fontSize: "0.78rem", color: "#aaa" },
  baselineBadge: { background: "#eef1ff", color: "#2d3a8c", fontSize: "0.72rem", fontWeight: 700, padding: "2px 10px", borderRadius: 20 },
  activeBadge:   { background: "#f0fff7", color: "#10b981", fontSize: "0.72rem", fontWeight: 700, padding: "2px 10px", borderRadius: 20 },
  cardActions: { display: "flex", gap: 8 },
  iconBtn: { background: "none", border: "1px solid #e3e7ef", borderRadius: 8, width: 34, height: 34, cursor: "pointer", fontSize: "1rem", display: "flex", alignItems: "center", justifyContent: "center" },
  emptyState: { textAlign: "center", padding: "80px 40px", color: "#888" },
  muted: { color: "#888", fontSize: "0.9rem" },
  // Modal
  overlay: { position: "fixed", inset: 0, background: "rgba(0,0,0,.4)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 },
  modal: { background: "#fff", borderRadius: 16, padding: "28px 32px", width: "min(580px, 95vw)", maxHeight: "90vh", overflowY: "auto" },
  modalHeader: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 },
  modalSub: { color: "#888", fontSize: "0.88rem", marginBottom: 20 },
  closeBtn: { background: "none", border: "none", cursor: "pointer", fontSize: "1.1rem", color: "#888" },
  fieldRow: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 },
  field: { display: "flex", flexDirection: "column", gap: 6 },
  label: { fontSize: "0.83rem", fontWeight: 600, color: "#555" },
  input: { border: "1px solid #d1d5db", borderRadius: 8, padding: "9px 12px", fontSize: "0.9rem", outline: "none" },
  checkRow: { display: "flex", alignItems: "center", marginBottom: 16, cursor: "pointer", fontSize: "0.9rem", color: "#444" },
  modalHint: { background: "#f6f8fe", border: "1px solid #c7d2fe", borderRadius: 8, padding: "10px 14px", fontSize: "0.83rem", color: "#3730a3", marginBottom: 16, lineHeight: 1.5 },
  errorMsg: { background: "#fff5f5", border: "1px solid #fca5a5", borderRadius: 8, padding: "8px 14px", color: "#ef4444", fontSize: "0.88rem", marginBottom: 14 },
  modalFooter: { display: "flex", justifyContent: "flex-end", gap: 12 },
  cancelBtn: { padding: "9px 20px", borderRadius: 8, border: "1px solid #e3e7ef", background: "#fff", cursor: "pointer", fontWeight: 500 },
  saveBtn: { padding: "9px 20px", borderRadius: 8, border: "none", background: "#2d3a8c", color: "#fff", cursor: "pointer", fontWeight: 600 },
};