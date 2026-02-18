import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getDashboardStats, getLatestSummary, runScan, getCompetitors } from '../api';
import { Button } from '../components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { 
  TrendingUp, 
  BarChart3, 
  Users, 
  FileText, 
  RefreshCw, 
  Loader2,
  ChevronRight,
  AlertCircle,
  Clock,
  Zap,
  LogOut,
  Menu,
  X
} from 'lucide-react';

const DashboardPage = () => {
  const { user, logout } = useAuth();
  const [stats, setStats] = useState(null);
  const [latestSummary, setLatestSummary] = useState(null);
  const [competitors, setCompetitors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [statsRes, summaryRes, competitorsRes] = await Promise.all([
        getDashboardStats(),
        getLatestSummary(),
        getCompetitors()
      ]);
      setStats(statsRes.data);
      setLatestSummary(summaryRes.data);
      setCompetitors(competitorsRes.data);
    } catch (err) {
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleRunScan = async () => {
    if (competitors.length === 0) {
      setError('Please add at least one competitor before running a scan');
      return;
    }
    setScanning(true);
    setError('');
    try {
      await runScan();
      // Refresh data after a short delay
      setTimeout(() => {
        loadDashboardData();
        setScanning(false);
      }, 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start scan');
      setScanning(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Never';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary rounded-lg">
                <TrendingUp className="w-5 h-5 text-white" />
              </div>
              <span className="font-bold text-lg font-heading hidden sm:block">CI Agent</span>
            </div>
            
            <nav className="hidden md:flex items-center gap-6">
              <Link to="/dashboard" className="text-primary font-medium text-sm">Dashboard</Link>
              <Link to="/competitors" className="text-slate-600 hover:text-primary text-sm">Competitors</Link>
              <Link to="/reports" className="text-slate-600 hover:text-primary text-sm">Reports</Link>
            </nav>
            
            <div className="flex items-center gap-4">
              <div className="hidden sm:flex items-center gap-2 text-sm text-slate-600">
                <span>Hello, {user?.name?.split(' ')[0]}</span>
              </div>
              <Button variant="ghost" size="icon" onClick={logout} data-testid="logout-btn">
                <LogOut className="w-4 h-4" />
              </Button>
              <button 
                className="md:hidden p-2"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              >
                {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>
        
        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-slate-200 bg-white py-4 px-4">
            <nav className="flex flex-col gap-3">
              <Link to="/dashboard" className="text-primary font-medium py-2">Dashboard</Link>
              <Link to="/competitors" className="text-slate-600 py-2">Competitors</Link>
              <Link to="/reports" className="text-slate-600 py-2">Reports</Link>
            </nav>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold font-heading text-slate-900">Dashboard</h1>
            <p className="text-slate-500 mt-1">Monitor your competitive landscape</p>
          </div>
          <Button 
            onClick={handleRunScan} 
            disabled={scanning}
            className="gap-2"
            data-testid="run-scan-btn"
          >
            {scanning ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Scanning...
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4" />
                Run Scan Now
              </>
            )}
          </Button>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3 text-red-700" data-testid="dashboard-error">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <Card className="hover:shadow-md transition-shadow" data-testid="stat-competitors">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500 uppercase tracking-wide">Competitors</p>
                  <p className="text-3xl font-bold text-slate-900 mt-1">{stats?.competitors_tracked || 0}</p>
                </div>
                <div className="p-3 bg-indigo-100 rounded-lg">
                  <Users className="w-6 h-6 text-primary" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="hover:shadow-md transition-shadow" data-testid="stat-reports">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500 uppercase tracking-wide">Reports</p>
                  <p className="text-3xl font-bold text-slate-900 mt-1">{stats?.total_reports || 0}</p>
                </div>
                <div className="p-3 bg-emerald-100 rounded-lg">
                  <FileText className="w-6 h-6 text-emerald-600" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="hover:shadow-md transition-shadow" data-testid="stat-active">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500 uppercase tracking-wide">Active Monitors</p>
                  <p className="text-3xl font-bold text-slate-900 mt-1">{stats?.active_monitors || 0}</p>
                </div>
                <div className="p-3 bg-blue-100 rounded-lg">
                  <BarChart3 className="w-6 h-6 text-blue-600" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="hover:shadow-md transition-shadow" data-testid="stat-changes">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500 uppercase tracking-wide">Changes Detected</p>
                  <p className="text-3xl font-bold text-slate-900 mt-1">{stats?.changes_this_week || 0}</p>
                </div>
                <div className="p-3 bg-amber-100 rounded-lg">
                  <Zap className="w-6 h-6 text-amber-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Competitors List */}
          <Card className="lg:col-span-1" data-testid="competitors-card">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Competitors</CardTitle>
                <CardDescription>Your monitored competitors</CardDescription>
              </div>
              <Link to="/competitors">
                <Button variant="ghost" size="sm" className="gap-1">
                  Manage <ChevronRight className="w-4 h-4" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent>
              {competitors.length === 0 ? (
                <div className="text-center py-8">
                  <Users className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                  <p className="text-slate-500 mb-4">No competitors added yet</p>
                  <Link to="/competitors">
                    <Button size="sm">Add Competitor</Button>
                  </Link>
                </div>
              ) : (
                <div className="space-y-3">
                  {competitors.slice(0, 5).map((comp) => (
                    <div 
                      key={comp.id} 
                      className="flex items-center justify-between p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className={`w-2 h-2 rounded-full ${comp.status === 'active' ? 'bg-emerald-500' : 'bg-slate-300'}`} />
                        <div>
                          <p className="font-medium text-sm text-slate-900">{comp.name}</p>
                          <p className="text-xs text-slate-500 truncate max-w-[150px]">{comp.website}</p>
                        </div>
                      </div>
                      {comp.is_baseline && (
                        <Badge variant="secondary" className="text-xs">Baseline</Badge>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* AI Insights */}
          <Card className="lg:col-span-2" data-testid="insights-card">
            <CardHeader>
              <div className="flex items-center gap-2">
                <CardTitle>AI Insights</CardTitle>
                <Badge variant="secondary">Claude AI</Badge>
              </div>
              <CardDescription>
                Last scan: {formatDate(stats?.last_scan)}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!latestSummary?.has_report ? (
                <div className="text-center py-12">
                  <BarChart3 className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                  <p className="text-slate-500 mb-2">No insights available yet</p>
                  <p className="text-sm text-slate-400">Run a scan to generate AI-powered insights</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {latestSummary.ai_insights ? (
                    <div className="p-4 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg border border-indigo-100">
                      <div className="prose prose-sm text-slate-700 whitespace-pre-wrap">
                        {latestSummary.ai_insights}
                      </div>
                    </div>
                  ) : (
                    <p className="text-slate-500">No AI insights generated for the latest scan.</p>
                  )}
                  
                  {latestSummary.summary && (
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 border-t border-slate-200">
                      <div className="text-center p-3 bg-slate-50 rounded-lg">
                        <p className="text-2xl font-bold text-slate-900">{latestSummary.summary.companies_monitored || 0}</p>
                        <p className="text-xs text-slate-500">Companies</p>
                      </div>
                      <div className="text-center p-3 bg-slate-50 rounded-lg">
                        <p className="text-2xl font-bold text-slate-900">{latestSummary.summary.total_products_tracked || 0}</p>
                        <p className="text-xs text-slate-500">Products</p>
                      </div>
                      <div className="text-center p-3 bg-slate-50 rounded-lg">
                        <p className="text-2xl font-bold text-slate-900">{latestSummary.summary.changes_detected || 0}</p>
                        <p className="text-xs text-slate-500">Changes</p>
                      </div>
                      <div className="text-center p-3 bg-slate-50 rounded-lg">
                        <p className="text-2xl font-bold text-slate-900">{latestSummary.summary.insights_generated || 0}</p>
                        <p className="text-xs text-slate-500">Insights</p>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <div className="mt-8 grid sm:grid-cols-3 gap-4">
          <Link to="/competitors" className="block">
            <Card className="hover:shadow-md hover:border-primary/50 transition-all cursor-pointer h-full">
              <CardContent className="p-6 flex items-center gap-4">
                <div className="p-3 bg-indigo-100 rounded-lg">
                  <Users className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900">Manage Competitors</h3>
                  <p className="text-sm text-slate-500">Add or edit monitored companies</p>
                </div>
              </CardContent>
            </Card>
          </Link>
          
          <Link to="/reports" className="block">
            <Card className="hover:shadow-md hover:border-primary/50 transition-all cursor-pointer h-full">
              <CardContent className="p-6 flex items-center gap-4">
                <div className="p-3 bg-emerald-100 rounded-lg">
                  <FileText className="w-6 h-6 text-emerald-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900">View Reports</h3>
                  <p className="text-sm text-slate-500">Browse historical intelligence</p>
                </div>
              </CardContent>
            </Card>
          </Link>
          
          <Card className="hover:shadow-md transition-all">
            <CardContent className="p-6 flex items-center gap-4">
              <div className="p-3 bg-amber-100 rounded-lg">
                <Clock className="w-6 h-6 text-amber-600" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900">Automated Scans</h3>
                <p className="text-sm text-slate-500">Daily at 9:00 AM UTC</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default DashboardPage;
