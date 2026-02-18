import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { RefreshCw } from 'lucide-react';
import api from '../lib/api';

const ReportsPage = () => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchReports = async () => {
  try {
    setLoading(true);
    const response = await api.get('/reports');
    // Axios stores the backend response in .data
    setReports(response.data || []); 
  } catch (e) { 
    console.error("Report Fetch Error:", e); 
  } finally { 
    setLoading(false); 
  }
};

  useEffect(() => { fetchReports(); }, []);

  const triggerScan = async () => {
    try {
      await api.post('/reports/run');
      alert("Agent Scan Started! The agent is now deep-scanning. Refresh in 1-2 minutes.");
    } catch (e) {
      alert("Failed to start scan. Check if backend is running on port 8001.");
    }
  };

  if (loading && reports.length === 0) {
    return <div className="p-12 text-center text-slate-500">Loading Intelligence...</div>;
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Strategic Intelligence</h1>
        <Button onClick={triggerScan} className="bg-indigo-600 text-white hover:bg-indigo-700">
          <RefreshCw className="mr-2" size={16} /> Trigger Agent Scan
        </Button>
      </div>

      {reports.length === 0 ? (
        <Card className="p-12 text-center">
          <p className="text-slate-500">No reports generated yet. Add your baseline and competitors, then run a scan.</p>
        </Card>
      ) : (
        reports.map((r) => (
          <Card key={r.id} className="border-l-4 border-l-indigo-500 shadow-sm">
            <CardHeader className="bg-slate-50/50 border-b">
              <CardTitle className="text-lg text-slate-700">{r.report_date}</CardTitle>
            </CardHeader>
            <CardContent className="mt-4">
              <div className="whitespace-pre-wrap font-mono text-sm bg-slate-900 text-indigo-100 p-6 rounded-lg overflow-x-auto leading-relaxed">
                {r.brief_data}
              </div>
            </CardContent>
          </Card>
        ))
      )}
    </div>
  );
};

export default ReportsPage;