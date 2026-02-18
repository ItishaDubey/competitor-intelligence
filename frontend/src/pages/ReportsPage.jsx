// frontend/src/pages/ReportsPage.jsx
import React, { useState, useEffect } from 'react';
import { getReports } from '../api'; // Ensure this endpoint returns 'brief_data'
import { Loader2, AlertCircle, ShieldAlert } from 'lucide-react';

const ReportsPage = () => {
  const [loading, setLoading] = useState(true);
  const [selectedReport, setSelectedReport] = useState(null);

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    try {
      const res = await getReports();
      setReports(res.data);
      if (res.data.length > 0) setSelectedReport(res.data[0]);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="flex justify-center p-10"><Loader2 className="animate-spin" /></div>;

  // Use the brief_data from the backend, or fallback
  const data = selectedReport?.brief_data || {
    metrics: { competitors: 0, skus: 0, changes: 0 },
    insights: [],
    matrix: []
  };

  return (
    <div className="min-h-screen bg-slate-50 p-8 font-sans text-slate-800">
      <div className="max-w-5xl mx-auto bg-white shadow-xl rounded-xl overflow-hidden border border-slate-200">
        
        {/* === HEADER === */}
        <div className="border-b-2 border-slate-100 p-8 flex justify-between items-center bg-white">
          <div>
            <h1 className="text-2xl font-bold text-slate-800 uppercase tracking-wide">Strategic Intelligence Brief</h1>
            <div className="text-slate-400 text-sm mt-1 font-medium">Generated: {data.report_date || "Just Now"}</div>
          </div>
          <span className="bg-slate-100 px-4 py-1 rounded-full text-xs font-bold text-slate-500 tracking-wider">CONFIDENTIAL</span>
        </div>

        <div className="p-8">
          
          {/* === METRICS CARDS === */}
          <div className="grid grid-cols-4 gap-6 mb-10">
            {[
              { label: "Competitors", val: data.metrics?.competitors_tracked || 0 },
              { label: "Total SKUs", val: data.metrics?.total_skus || 0 },
              { label: "Active Changes", val: data.metrics?.active_changes || 0 },
              { label: "Market Players", val: data.metrics?.market_players || 0 }
            ].map((m, i) => (
              <div key={i} className="bg-slate-50 p-6 rounded-lg text-center border border-slate-100">
                <div className="text-3xl font-bold text-slate-700">{m.val}</div>
                <div className="text-xs text-slate-400 uppercase font-bold mt-2 tracking-wide">{m.label}</div>
              </div>
            ))}
          </div>

          {/* === STRATEGIC INSIGHTS === */}
          <h3 className="text-sm font-bold text-indigo-500 uppercase tracking-widest mb-4">Strategic Insights</h3>
          <div className="space-y-3 mb-10">
            {data.insights?.length > 0 ? data.insights.map((insight, idx) => (
              <div key={idx} className={`p-4 border-l-4 rounded-r-md bg-white shadow-sm flex items-start gap-3 ${
                insight.priority === 'high' ? 'border-red-500 bg-red-50/50' : 'border-amber-400 bg-amber-50/50'
              }`}>
                {insight.priority === 'high' ? <ShieldAlert className="w-5 h-5 text-red-500" /> : <AlertCircle className="w-5 h-5 text-amber-500" />}
                <div>
                  <strong className="block text-slate-800 text-sm mb-1">{insight.title}</strong>
                  <p className="text-slate-600 text-sm">{insight.text}</p>
                </div>
              </div>
            )) : (
              <div className="p-4 bg-slate-50 text-slate-400 text-sm italic text-center">No major anomalies detected in this scan.</div>
            )}
          </div>

          {/* === LANDSCAPE MATRIX (The Table) === */}
          <h3 className="text-sm font-bold text-indigo-500 uppercase tracking-widest mb-4">Competitive Landscape Matrix</h3>
          <div className="overflow-hidden rounded-lg border border-slate-200">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-500 font-bold uppercase text-xs">
                <tr>
                  <th className="p-4">Entity</th>
                  <th className="p-4">Price Positioning</th>
                  <th className="p-4">Catalog Depth</th>
                  <th className="p-4">Recent Signals</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.matrix?.map((row, i) => (
                  <tr key={i} className={row.is_baseline ? "bg-amber-50/30 border-l-4 border-amber-400" : "hover:bg-slate-50"}>
                    <td className="p-4 font-semibold text-slate-700">
                      {row.entity}
                    </td>
                    <td className="p-4">
                      <div className="font-bold text-slate-700">{row.positioning}</div>
                      <div className="text-xs text-slate-400 mt-0.5">Avg: {row.avg_price}</div>
                    </td>
                    <td className="p-4 text-slate-600">{row.catalog_depth}</td>
                    <td className="p-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        row.signals.includes("New") ? "bg-green-100 text-green-800" : "bg-slate-100 text-slate-600"
                      }`}>
                        {row.signals}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        
        </div>
      </div>
    </div>
  );
};

export default ReportsPage;