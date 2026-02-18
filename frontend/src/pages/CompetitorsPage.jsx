import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getCompetitors, createCompetitor, updateCompetitor, deleteCompetitor } from '../api';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Label } from '../components/ui/Label';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { 
  TrendingUp, 
  Plus, 
  Edit2, 
  Trash2, 
  X, 
  Loader2,
  Globe,
  ChevronDown,
  ChevronUp,
  LogOut,
  Menu,
  AlertCircle
} from 'lucide-react';

const CompetitorsPage = () => {
  const { user, logout } = useAuth();
  const [competitors, setCompetitors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [expandedId, setExpandedId] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    website: '',
    is_baseline: false,
    pages_to_monitor: [{ name: 'Homepage', url: '', track: ['content', 'products', 'pricing'] }]
  });

  useEffect(() => {
    loadCompetitors();
  }, []);

  const loadCompetitors = async () => {
    try {
      const response = await getCompetitors();
      setCompetitors(response.data);
    } catch (err) {
      setError('Failed to load competitors');
    } finally {
      setLoading(false);
    }
  };

  const openModal = (competitor = null) => {
    if (competitor) {
      setEditingId(competitor.id);
      setFormData({
        name: competitor.name,
        website: competitor.website,
        is_baseline: competitor.is_baseline,
        pages_to_monitor: competitor.pages_to_monitor.length > 0 
          ? competitor.pages_to_monitor 
          : [{ name: 'Homepage', url: '', track: ['content', 'products', 'pricing'] }]
      });
    } else {
      setEditingId(null);
      setFormData({
        name: '',
        website: '',
        is_baseline: false,
        pages_to_monitor: [{ name: 'Homepage', url: '', track: ['content', 'products', 'pricing'] }]
      });
    }
    setShowModal(true);
    setError('');
  };

  const closeModal = () => {
    setShowModal(false);
    setEditingId(null);
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');

    // Auto-fill page URL if not set
    const processedData = {
      ...formData,
      pages_to_monitor: formData.pages_to_monitor.map(page => ({
        ...page,
        url: page.url || formData.website
      }))
    };

    try {
      if (editingId) {
        await updateCompetitor(editingId, processedData);
      } else {
        await createCompetitor(processedData);
      }
      await loadCompetitors();
      closeModal();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save competitor');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this competitor?')) return;
    
    try {
      await deleteCompetitor(id);
      setCompetitors(competitors.filter(c => c.id !== id));
    } catch (err) {
      setError('Failed to delete competitor');
    }
  };

  const addPage = () => {
    setFormData({
      ...formData,
      pages_to_monitor: [
        ...formData.pages_to_monitor,
        { name: '', url: '', track: ['content', 'products', 'pricing'] }
      ]
    });
  };

  const removePage = (index) => {
    const pages = [...formData.pages_to_monitor];
    pages.splice(index, 1);
    setFormData({ ...formData, pages_to_monitor: pages });
  };

  const updatePage = (index, field, value) => {
    const pages = [...formData.pages_to_monitor];
    pages[index] = { ...pages[index], [field]: value };
    setFormData({ ...formData, pages_to_monitor: pages });
  };

  const toggleTrackOption = (index, option) => {
    const pages = [...formData.pages_to_monitor];
    const track = pages[index].track || [];
    if (track.includes(option)) {
      pages[index].track = track.filter(t => t !== option);
    } else {
      pages[index].track = [...track, option];
    }
    setFormData({ ...formData, pages_to_monitor: pages });
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Never';
    return new Date(dateStr).toLocaleDateString('en-US', { 
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
              <Link to="/competitors" className="text-primary font-medium text-sm">Competitors</Link>
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
        
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-slate-200 bg-white py-4 px-4">
            <nav className="flex flex-col gap-3">
              <Link to="/dashboard" className="text-slate-600 py-2">Dashboard</Link>
              <Link to="/competitors" className="text-primary font-medium py-2">Competitors</Link>
              <Link to="/reports" className="text-slate-600 py-2">Reports</Link>
            </nav>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold font-heading text-slate-900">Competitors</h1>
            <p className="text-slate-500 mt-1">Configure companies to monitor</p>
          </div>
          <Button onClick={() => openModal()} className="gap-2" data-testid="add-competitor-btn">
            <Plus className="w-4 h-4" />
            Add Competitor
          </Button>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3 text-red-700">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {competitors.length === 0 ? (
          <Card className="py-16">
            <CardContent className="text-center">
              <Globe className="w-16 h-16 text-slate-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-slate-900 mb-2">No competitors yet</h3>
              <p className="text-slate-500 mb-6 max-w-md mx-auto">
                Start by adding your first competitor to monitor. You can track their website, products, and pricing changes.
              </p>
              <Button onClick={() => openModal()} className="gap-2" data-testid="add-first-competitor-btn">
                <Plus className="w-4 h-4" />
                Add Your First Competitor
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {competitors.map((competitor) => (
              <Card 
                key={competitor.id} 
                className={`hover:shadow-md transition-shadow ${competitor.is_baseline ? 'border-primary/50' : ''}`}
                data-testid={`competitor-card-${competitor.id}`}
              >
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4">
                      <div className={`w-3 h-3 rounded-full mt-2 ${competitor.status === 'active' ? 'bg-emerald-500' : 'bg-slate-300'}`} />
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="text-lg font-semibold text-slate-900">{competitor.name}</h3>
                          {competitor.is_baseline && (
                            <Badge variant="default" className="text-xs">Baseline</Badge>
                          )}
                          <Badge 
                            variant={competitor.status === 'active' ? 'success' : 'outline'} 
                            className="text-xs"
                          >
                            {competitor.status === 'active' ? 'Active' : 'Pending'}
                          </Badge>
                        </div>
                        <a 
                          href={competitor.website} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-sm text-primary hover:underline"
                        >
                          {competitor.website}
                        </a>
                        <p className="text-xs text-slate-500 mt-1">
                          Last checked: {formatDate(competitor.last_checked)}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        onClick={() => setExpandedId(expandedId === competitor.id ? null : competitor.id)}
                        data-testid={`expand-competitor-${competitor.id}`}
                      >
                        {expandedId === competitor.id ? (
                          <ChevronUp className="w-4 h-4" />
                        ) : (
                          <ChevronDown className="w-4 h-4" />
                        )}
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        onClick={() => openModal(competitor)}
                        data-testid={`edit-competitor-${competitor.id}`}
                      >
                        <Edit2 className="w-4 h-4" />
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        onClick={() => handleDelete(competitor.id)}
                        className="text-red-500 hover:text-red-700 hover:bg-red-50"
                        data-testid={`delete-competitor-${competitor.id}`}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                  
                  {expandedId === competitor.id && competitor.pages_to_monitor.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-slate-200">
                      <h4 className="text-sm font-medium text-slate-700 mb-3">Pages Monitored:</h4>
                      <div className="space-y-2">
                        {competitor.pages_to_monitor.map((page, idx) => (
                          <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                            <div>
                              <p className="font-medium text-sm text-slate-900">{page.name}</p>
                              <p className="text-xs text-slate-500">{page.url}</p>
                            </div>
                            <div className="flex gap-1">
                              {page.track?.map(t => (
                                <Badge key={t} variant="outline" className="text-xs capitalize">{t}</Badge>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </main>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto" data-testid="competitor-modal">
            <CardHeader className="border-b border-slate-200">
              <div className="flex items-center justify-between">
                <CardTitle>{editingId ? 'Edit Competitor' : 'Add Competitor'}</CardTitle>
                <Button variant="ghost" size="icon" onClick={closeModal} data-testid="close-modal-btn">
                  <X className="w-4 h-4" />
                </Button>
              </div>
              <CardDescription>
                {editingId ? 'Update competitor details and monitoring settings' : 'Configure a new competitor to monitor'}
              </CardDescription>
            </CardHeader>
            
            <form onSubmit={handleSubmit}>
              <CardContent className="space-y-6 py-6">
                {error && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm">
                    {error}
                  </div>
                )}
                
                <div className="grid sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Company Name *</Label>
                    <Input
                      id="name"
                      placeholder="e.g., Competitor Inc."
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      required
                      data-testid="competitor-name-input"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="website">Website URL *</Label>
                    <Input
                      id="website"
                      type="url"
                      placeholder="https://example.com"
                      value={formData.website}
                      onChange={(e) => setFormData({ ...formData, website: e.target.value })}
                      required
                      data-testid="competitor-website-input"
                    />
                  </div>
                </div>
                
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    id="is_baseline"
                    checked={formData.is_baseline}
                    onChange={(e) => setFormData({ ...formData, is_baseline: e.target.checked })}
                    className="w-4 h-4 rounded border-slate-300 text-primary focus:ring-primary"
                    data-testid="baseline-checkbox"
                  />
                  <Label htmlFor="is_baseline" className="cursor-pointer">
                    Set as baseline (your company) for comparison
                  </Label>
                </div>
                
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Label>Pages to Monitor</Label>
                    <Button type="button" variant="outline" size="sm" onClick={addPage} data-testid="add-page-btn">
                      <Plus className="w-3 h-3 mr-1" /> Add Page
                    </Button>
                  </div>
                  
                  {formData.pages_to_monitor.map((page, idx) => (
                    <div key={idx} className="p-4 bg-slate-50 rounded-lg space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-slate-700">Page {idx + 1}</span>
                        {formData.pages_to_monitor.length > 1 && (
                          <Button 
                            type="button" 
                            variant="ghost" 
                            size="sm" 
                            onClick={() => removePage(idx)}
                            className="text-red-500 hover:text-red-700"
                          >
                            <Trash2 className="w-3 h-3" />
                          </Button>
                        )}
                      </div>
                      
                      <div className="grid sm:grid-cols-2 gap-3">
                        <div className="space-y-1">
                          <Label className="text-xs">Page Name</Label>
                          <Input
                            placeholder="e.g., Pricing Page"
                            value={page.name}
                            onChange={(e) => updatePage(idx, 'name', e.target.value)}
                            data-testid={`page-name-input-${idx}`}
                          />
                        </div>
                        <div className="space-y-1">
                          <Label className="text-xs">URL (leave empty for main website)</Label>
                          <Input
                            type="url"
                            placeholder="https://example.com/pricing"
                            value={page.url}
                            onChange={(e) => updatePage(idx, 'url', e.target.value)}
                            data-testid={`page-url-input-${idx}`}
                          />
                        </div>
                      </div>
                      
                      <div className="space-y-1">
                        <Label className="text-xs">Track</Label>
                        <div className="flex flex-wrap gap-2">
                          {['content', 'products', 'pricing'].map(option => (
                            <button
                              key={option}
                              type="button"
                              onClick={() => toggleTrackOption(idx, option)}
                              className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                                page.track?.includes(option)
                                  ? 'bg-primary text-white border-primary'
                                  : 'bg-white text-slate-600 border-slate-200 hover:border-primary'
                              }`}
                              data-testid={`track-option-${option}-${idx}`}
                            >
                              {option}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
              
              <div className="flex justify-end gap-3 px-6 py-4 border-t border-slate-200">
                <Button type="button" variant="outline" onClick={closeModal}>
                  Cancel
                </Button>
                <Button type="submit" disabled={saving} data-testid="save-competitor-btn">
                  {saving ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    editingId ? 'Update Competitor' : 'Add Competitor'
                  )}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
};

export default CompetitorsPage;
