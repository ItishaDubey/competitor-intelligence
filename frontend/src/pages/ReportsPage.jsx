import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getReports, getReport } from '../api';
import { Button } from '../components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { 
  TrendingUp, 
  FileText, 
  Loader2,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  LogOut,
  Menu,
  X,
  Calendar,
  BarChart3,
  AlertCircle,
  Sparkles,
  Package,
  DollarSign,
  TrendingDown,
  TrendingUp as TrendingUpIcon
} from 'lucide-react';

const ReportsPage = () => {
  const { user, logout } = useAuth();
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState(null);
  const [selectedReport, setSelectedReport] = useState(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    try {
      const response = await getReports(20);
      setReports(response.data);
      if (response.data.length > 0) {
        setSelectedReport(response.data[0]);
      }
    } catch (err) {
      setError('Failed to load reports');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Unknown';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
      weekday: 'short',
      month: 'short', 
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatShortDate = (dateStr) => {
    if (!dateStr) return 'Unknown';
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
              <Link to="/dashboard" className="text-slate-600 hover:text-primary text-sm">Dashboard</Link>
              <Link to="/competitors" className="text-slate-600 hover:text-primary text-sm">Competitors</Link>
              <Link to="/reports" className="text-primary font-medium text-sm">Reports</Link>
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
        
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-slate-200 bg-white py-4 px-4">
            <nav className="flex flex-col gap-3">
              <Link to="/dashboard" className="text-slate-600 py-2">Dashboard</Link>
              <Link to="/competitors" className="text-slate-600 py-2">Competitors</Link>
              <Link to="/reports" className="text-primary font-medium py-2">Reports</Link>
            </nav>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold font-heading text-slate-900">Intelligence Reports</h1>
          <p className="text-slate-500 mt-1">View historical competitive intelligence data</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3 text-red-700">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {reports.length === 0 ? (
          <Card className="py-16">
            <CardContent className="text-center">
              <FileText className="w-16 h-16 text-slate-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-slate-900 mb-2">No reports yet</h3>
              <p className="text-slate-500 mb-6 max-w-md mx-auto">
                Run your first intelligence scan from the dashboard to generate a report.
              </p>
              <Link to="/dashboard">
                <Button className="gap-2">
                  Go to Dashboard
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </Link>
            </CardContent>
          </Card>
        ) : (
          <div className="grid lg:grid-cols-3 gap-6">
            {/* Reports List */}
            <div className="lg:col-span-1 space-y-2" data-testid="reports-list">
              <h3 className="text-sm font-medium text-slate-500 uppercase tracking-wide mb-3">Recent Reports</h3>
              {reports.map((report) => (
                <button
                  key={report.id}
                  onClick={() => setSelectedReport(report)}
                  className={`w-full text-left p-4 rounded-lg border transition-all ${
                    selectedReport?.id === report.id
                      ? 'bg-primary/5 border-primary'
                      : 'bg-white border-slate-200 hover:border-primary/50'
                  }`}
                  data-testid={`report-item-${report.id}`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${
                        selectedReport?.id === report.id ? 'bg-primary/10' : 'bg-slate-100'
                      }`}>
                        <Calendar className={`w-4 h-4 ${
                          selectedReport?.id === report.id ? 'text-primary' : 'text-slate-500'
                        }`} />
                      </div>
                      <div>
                        <p className="font-medium text-sm text-slate-900">
                          {formatShortDate(report.report_date)}
                        </p>
                        <p className="text-xs text-slate-500">
                          {report.summary.companies_monitored} companies
                        </p>
                      </div>
                    </div>
                    {report.summary.changes_detected > 0 && (
                      <Badge variant="warning" className="text-xs">
                        {report.summary.changes_detected} changes
                      </Badge>
                    )}
                  </div>
                </button>
              ))}
            </div>

            {/* Report Details */}
            <div className="lg:col-span-2">
              {selectedReport && (
                <Card data-testid="report-details">
                  <CardHeader className="border-b border-slate-200">
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="flex items-center gap-2">
                          <FileText className="w-5 h-5" />
                          Intelligence Report
                        </CardTitle>
                        <CardDescription>
                          {formatDate(selectedReport.report_date)}
                        </CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  
                  <CardContent className="space-y-6 py-6">
                    {/* Summary Stats */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                      <div className="text-center p-4 bg-slate-50 rounded-lg">
                        <p className="text-2xl font-bold text-slate-900">{selectedReport.summary.companies_monitored}</p>
                        <p className="text-xs text-slate-500">Companies</p>
                      </div>
                      <div className="text-center p-4 bg-slate-50 rounded-lg">
                        <p className="text-2xl font-bold text-slate-900">{selectedReport.summary.total_products_tracked}</p>
                        <p className="text-xs text-slate-500">Products</p>
                      </div>
                      <div className="text-center p-4 bg-amber-50 rounded-lg">
                        <p className="text-2xl font-bold text-amber-600">{selectedReport.summary.changes_detected}</p>
                        <p className="text-xs text-slate-500">Changes</p>
                      </div>
                      <div className="text-center p-4 bg-indigo-50 rounded-lg">
                        <p className="text-2xl font-bold text-primary">{selectedReport.summary.insights_generated}</p>
                        <p className="text-xs text-slate-500">Insights</p>
                      </div>
                    </div>

                    {/* AI Insights */}
                    {selectedReport.ai_insights && (
                      <div className="space-y-3">
                        <h4 className="text-sm font-medium text-slate-700 flex items-center gap-2">
                          <Sparkles className="w-4 h-4 text-primary" />
                          AI Analysis
                        </h4>
                        <div className="p-4 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg border border-indigo-100">
                          <div className="prose prose-sm text-slate-700 whitespace-pre-wrap">
                            {selectedReport.ai_insights}
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Detailed Results */}
                    <div className="space-y-3">
                      <h4 className="text-sm font-medium text-slate-700">Competitor Details</h4>
                      <div className="space-y-3">
                        {selectedReport.detailed_results.map((result, idx) => (
                          <div 
                            key={idx} 
                            className={`p-4 rounded-lg border ${
                              result.is_baseline ? 'border-primary/30 bg-primary/5' : 'border-slate-200 bg-white'
                            }`}
                          >
                            <div className="flex items-start justify-between">
                              <div>
                                <div className="flex items-center gap-2">
                                  <h5 className="font-semibold text-slate-900">{result.company}</h5>
                                  {result.is_baseline && (
                                    <Badge variant="default" className="text-xs">Baseline</Badge>
                                  )}
                                </div>
                                <a 
                                  href={result.url} 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  className="text-xs text-primary hover:underline"
                                >
                                  {result.url}
                                </a>
                              </div>
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => setExpandedId(expandedId === idx ? null : idx)}
                              >
                                {expandedId === idx ? (
                                  <ChevronUp className="w-4 h-4" />
                                ) : (
                                  <ChevronDown className="w-4 h-4" />
                                )}
                              </Button>
                            </div>
                            
                            <div className="flex flex-wrap gap-4 mt-3">
                              <div className="flex items-center gap-2 text-sm">
                                <Package className="w-4 h-4 text-slate-400" />
                                <span className="text-slate-600">{result.products_found} products</span>
                              </div>
                              {result.price_range && (
                                <div className="flex items-center gap-2 text-sm">
                                  <DollarSign className="w-4 h-4 text-slate-400" />
                                  <span className="text-slate-600">
                                    ${result.price_range.min?.toFixed(2)} - ${result.price_range.max?.toFixed(2)}
                                  </span>
                                </div>
                              )}
                            </div>

                            {/* Changes */}
                            {result.changes && (
                              <div className="mt-3 pt-3 border-t border-slate-200">
                                <h6 className="text-xs font-medium text-amber-600 mb-2 flex items-center gap-1">
                                  <AlertCircle className="w-3 h-3" />
                                  Changes Detected
                                </h6>
                                <div className="space-y-1 text-sm">
                                  {result.changes.new_products && (
                                    <p className="text-emerald-600">
                                      + {result.changes.new_products.length} new products
                                    </p>
                                  )}
                                  {result.changes.removed_products && (
                                    <p className="text-red-600">
                                      - {result.changes.removed_products.length} removed products
                                    </p>
                                  )}
                                  {result.changes.avg_price_change && (
                                    <p className={result.changes.avg_price_change.change_pct > 0 ? 'text-red-600' : 'text-emerald-600'}>
                                      Price change: {result.changes.avg_price_change.change_pct > 0 ? '+' : ''}{result.changes.avg_price_change.change_pct.toFixed(1)}%
                                    </p>
                                  )}
                                  {result.changes.content_changed && (
                                    <p className="text-blue-600">Content updated</p>
                                  )}
                                </div>
                              </div>
                            )}

                            {/* Insights */}
                            {result.insights && result.insights.length > 0 && (
                              <div className="mt-3 pt-3 border-t border-slate-200">
                                <h6 className="text-xs font-medium text-primary mb-2 flex items-center gap-1">
                                  <Sparkles className="w-3 h-3" />
                                  Insights
                                </h6>
                                <div className="space-y-2">
                                  {result.insights.map((insight, iIdx) => (
                                    <div 
                                      key={iIdx} 
                                      className={`p-2 rounded text-sm ${
                                        insight.priority === 'high' ? 'bg-red-50 text-red-700' : 'bg-amber-50 text-amber-700'
                                      }`}
                                    >
                                      <p className="font-medium">{insight.message}</p>
                                      <p className="text-xs opacity-80">{insight.recommendation}</p>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Expanded: Sample Products */}
                            {expandedId === idx && result.sample_products && result.sample_products.length > 0 && (
                              <div className="mt-3 pt-3 border-t border-slate-200">
                                <h6 className="text-xs font-medium text-slate-500 mb-2">Sample Products</h6>
                                <div className="space-y-1">
                                  {result.sample_products.map((product, pIdx) => (
                                    <div key={pIdx} className="flex items-center justify-between p-2 bg-slate-50 rounded text-sm">
                                      <span className="text-slate-700">{product.name}</span>
                                      {product.price && (
                                        <span className="text-primary font-medium">{product.price}</span>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default ReportsPage;
