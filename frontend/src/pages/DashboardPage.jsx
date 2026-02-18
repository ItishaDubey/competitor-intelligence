import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { RefreshCw, Plus } from 'lucide-react';
import { Link } from 'react-router-dom';
import { getDashboardStats, getLatestSummary, runScan } from '../lib/api';

const DashboardPage = () => {
  const [stats, setStats] = useState({ competitors_count: 0, reports_count: 0, active_alerts: 0 });
  const [summary, setSummary] = useState('');
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const [sRes, sumRes] = await Promise.all([getDashboardStats(), getLatestSummary()]);
      setStats(sRes.data);
      setSummary(sumRes.data.summary);
    } catch (e) { console.error(e); } finally { setLoading(false); }
  };

  useEffect(() => { loadData(); }, []);

  if (loading) return <div className="p-10 text-center">Loading...</div>;

  return (
    <div className="p-6 space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Market Intelligence</h1>
        <div className="space-x-4">
          <Button onClick={() => runScan().then(() => alert("Scan Started"))} className="bg-indigo-600 text-white">
            <RefreshCw className="mr-2 h-4 w-4" /> Run New Scan
          </Button>
          <Link to="/competitors"><Button variant="outline"><Plus className="mr-2 h-4 w-4" /> Add Competitor</Button></Link>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card><CardContent className="pt-6 font-bold text-2xl">{stats.competitors_count} Competitors</CardContent></Card>
        <Card><CardContent className="pt-6 font-bold text-2xl">{stats.reports_count} Reports</CardContent></Card>
        <Card><CardContent className="pt-6 font-bold text-2xl">{stats.active_alerts} Alerts</CardContent></Card>
      </div>
      <Card className="border-l-4 border-indigo-500">
        <CardHeader><CardTitle>Latest Intelligence Summary</CardTitle></CardHeader>
        <CardContent className="italic">"{summary}"</CardContent>
      </Card>
    </div>
  );
};
export default DashboardPage;