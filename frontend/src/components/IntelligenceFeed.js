import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { Input } from './ui/input';
import { Shield, Plus, RefreshCw, Clock, ExternalLink, AlertTriangle, Zap, CheckCircle, Search, Filter, SortAsc, SortDesc, LogIn, User } from 'lucide-react';
import AuthModal from './AuthModal';
import SubscriptionPlans from './SubscriptionPlans';
import UserMenu from './UserMenu';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const IntelligenceFeed = () => {
  const [searchParams] = useSearchParams();
  const [userData, setUserData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [lastRefresh, setLastRefresh] = useState(new Date());
  const [quickScanResult, setQuickScanResult] = useState(null);
  const [filterTerm, setFilterTerm] = useState('');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [sourceFilter, setSourceFilter] = useState('all');
  const [sortBy, setSortBy] = useState('date');
  const [sortOrder, setSortOrder] = useState('desc');
  
  // Authentication state
  const [user, setUser] = useState(null);
  const [authToken, setAuthToken] = useState(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [showSubscriptionPlans, setShowSubscriptionPlans] = useState(false);
  
  const navigate = useNavigate();

  const userEmail = searchParams.get('email');
  const hasQuickScan = searchParams.get('quickScan') === 'true';

  const fetchUserData = async () => {
    if (!userEmail) {
      setError('No email provided');
      setLoading(false);
      return;
    }

    try {
      const response = await axios.get(`${API}/status`, {
        params: { email: userEmail }
      });
      setUserData(response.data);
      setError('');
      setLastRefresh(new Date());
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to fetch intelligence data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUserData();
    
    // Clean up any stale Quick Scan results from other users in sessionStorage
    if (userEmail) {
      const allKeys = Object.keys(sessionStorage);
      const quickScanKeys = allKeys.filter(key => key.startsWith('quickScanResult_'));
      quickScanKeys.forEach(key => {
        if (key !== `quickScanResult_${userEmail}`) {
          // Remove Quick Scan results from other users
          sessionStorage.removeItem(key);
        }
      });
    }
    
    // Handle quick scan data from sessionStorage (associated with specific email)
    if (hasQuickScan && userEmail) {
      try {
        const storedQuickScan = sessionStorage.getItem(`quickScanResult_${userEmail}`);
        if (storedQuickScan) {
          const parsedQuickScan = JSON.parse(storedQuickScan);
          // Verify the scan belongs to this email and is recent (within 1 hour)
          const scanTime = new Date(parsedQuickScan.timestamp);
          const now = new Date();
          const hoursDiff = Math.abs(now - scanTime) / 36e5;
          
          if (parsedQuickScan.userEmail === userEmail && hoursDiff < 1) {
            setQuickScanResult(parsedQuickScan);
          } else {
            // Clean up old or mismatched scan results
            sessionStorage.removeItem(`quickScanResult_${userEmail}`);
          }
        }
      } catch (error) {
        console.error('Failed to parse quick scan data:', error);
      }
    } else if (!hasQuickScan && userEmail) {
      // User accessed feed directly (View My Feed) - ensure no lingering Quick Scan results
      setQuickScanResult(null);
    }
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchUserData, 30000);
    return () => clearInterval(interval);
  }, [userEmail, hasQuickScan]);

  const getSeverityBadge = (severity) => {
    const severityClasses = {
      'Critical': 'severity-critical',
      'High': 'severity-high', 
      'Medium': 'severity-medium',
      'Low': 'severity-low'
    };
    
    return (
      <Badge className={`${severityClasses[severity]} text-xs font-semibold px-2 py-1`}>
        {severity}
      </Badge>
    );
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const convertQuickScanToMatches = (quickScan) => {
    if (!quickScan) return [];
    
    const matches = [];
    
    // Add AI Summary as main intelligence match
    matches.push({
      id: `quick-scan-summary-${Date.now()}`,
      term: quickScan.query,
      incident_title: `AI Threat Intelligence Analysis: ${quickScan.query}`,
      source: 'AI-Powered Quick Scan',
      date: quickScan.timestamp,
      severity: 'High',
      type: 'quick-scan-summary',
      summary: quickScan.summary,
      url: null
    });
    
    return matches;
  };

  const convertDiscoveredLinksToMatches = (quickScan) => {
    if (!quickScan || !quickScan.discovered_links) return [];
    
    return quickScan.discovered_links.map((link, index) => ({
      id: `discovered-link-${Date.now()}-${index}`,
      term: quickScan.query,
      incident_title: link.title,
      source: new URL(link.url).hostname,
      date: link.date,
      severity: link.severity,
      type: 'discovered-link',
      url: link.url,
      snippet: link.snippet
    }));
  };

  const getAllIntelligenceMatches = () => {
    const regularMatches = userData?.intelligence_matches || [];
    
    // Only include Quick Scan results if they belong to the current user
    const quickScanMatches = (quickScanResult && quickScanResult.userEmail === userEmail) 
      ? convertQuickScanToMatches(quickScanResult) 
      : [];
    const discoveredLinks = (quickScanResult && quickScanResult.userEmail === userEmail) 
      ? convertDiscoveredLinksToMatches(quickScanResult) 
      : [];
    
    return [...quickScanMatches, ...discoveredLinks, ...regularMatches];
  };

  const getFilteredAndSortedMatches = () => {
    let matches = getAllIntelligenceMatches();
    
    // Apply filters
    if (filterTerm) {
      matches = matches.filter(match => 
        match.incident_title.toLowerCase().includes(filterTerm.toLowerCase()) ||
        match.term.toLowerCase().includes(filterTerm.toLowerCase()) ||
        match.source.toLowerCase().includes(filterTerm.toLowerCase())
      );
    }
    
    if (severityFilter !== 'all') {
      matches = matches.filter(match => match.severity.toLowerCase() === severityFilter.toLowerCase());
    }
    
    if (sourceFilter !== 'all') {
      matches = matches.filter(match => {
        if (sourceFilter === 'quick-scan') {
          return match.type === 'quick-scan-summary' || match.type === 'discovered-link';
        } else if (sourceFilter === 'monitoring') {
          return !match.type || match.type === 'regular';
        }
        return match.source.toLowerCase().includes(sourceFilter.toLowerCase());
      });
    }
    
    // Apply sorting
    matches.sort((a, b) => {
      let aValue, bValue;
      
      switch (sortBy) {
        case 'date':
          aValue = new Date(a.date);
          bValue = new Date(b.date);
          break;
        case 'severity':
          const severityOrder = { 'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1 };
          aValue = severityOrder[a.severity] || 0;
          bValue = severityOrder[b.severity] || 0;
          break;
        case 'title':
          aValue = a.incident_title.toLowerCase();
          bValue = b.incident_title.toLowerCase();
          break;
        default:
          return 0;
      }
      
      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });
    
    return matches;
  };

  const getUniqueSourcesForFilter = () => {
    const matches = getAllIntelligenceMatches();
    const sources = [...new Set(matches.map(match => match.source))];
    return sources;
  };

  const handleSubscribeToQuickScan = async () => {
    if (!quickScanResult) return;
    
    try {
      const response = await axios.post(`${API}/subscribe`, {
        term: quickScanResult.query,
        email: userEmail,
      });
      
      // Refresh data to show the new subscription
      fetchUserData();
      
      // Clear quick scan result and show success message
      setQuickScanResult(null);
      if (userEmail) {
        sessionStorage.removeItem(`quickScanResult_${userEmail}`);
      }
      // Remove quick scan from URL
      const newUrl = new URL(window.location);
      newUrl.searchParams.delete('quickScan');
      window.history.replaceState({}, '', newUrl);
      
    } catch (error) {
      console.error('Failed to subscribe:', error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-gray-900 to-slate-800 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-pulse text-cyan-400 mb-4">
            <Shield className="h-16 w-16 mx-auto" />
          </div>
          <p className="text-gray-300">Loading intelligence feed...</p>
        </div>
      </div>
    );
  }

  if (error && !userData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-gray-900 to-slate-800 flex items-center justify-center">
        <div className="max-w-md w-full mx-4">
          <Alert className="border-red-500 bg-red-900/20">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription className="text-red-300">
              {error}
            </AlertDescription>
          </Alert>
          <Button 
            onClick={() => navigate('/')} 
            className="w-full mt-4 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700"
          >
            Return to Home
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-gray-900 to-slate-800">
      {/* Header */}
      <header className="py-6 px-4 border-b border-gray-800">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Shield className="h-8 w-8 text-cyan-400" />
              <span className="text-2xl font-bold text-white font-mono">ThreatWatch</span>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-gray-400 text-sm">
                <Clock className="h-4 w-4" />
                <span>Last updated: {lastRefresh.toLocaleTimeString()}</span>
              </div>
              <Button
                onClick={fetchUserData}
                variant="outline"
                size="sm"
                className="border-gray-600 text-gray-300 hover:bg-gray-800"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
              <Button
                onClick={() => navigate('/')}
                className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700"
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Keyword
              </Button>
            </div>
          </div>
          
          <h1 className="text-3xl font-bold text-white">My Intelligence Feed</h1>
          <p className="text-gray-400 mt-2">Monitoring threats for: {userEmail}</p>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Subscriptions Section */}
        <section className="mb-8">
          <h2 className="text-xl font-semibold text-white mb-4">Active Subscriptions</h2>
          {userData?.subscriptions?.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {userData.subscriptions.map((subscription) => (
                <Card key={subscription.id} className="glass border-gray-700">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-semibold text-white">{subscription.term}</h3>
                        <p className="text-sm text-gray-400">
                          Since {formatDate(subscription.created_at)}
                        </p>
                      </div>
                      <Badge variant="outline" className="border-green-500 text-green-400">
                        Active
                      </Badge>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card className="glass border-gray-700">
              <CardContent className="p-6 text-center">
                <p className="text-gray-400">No active subscriptions found.</p>
                <Button
                  onClick={() => navigate('/')}
                  className="mt-4 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700"
                >
                  Add Your First Keyword
                </Button>
              </CardContent>
            </Card>
          )}
        </section>

        {/* Quick Scan Results Section */}
        {quickScanResult && (
          <section className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-white flex items-center space-x-2">
                <Zap className="h-5 w-5 text-orange-400" />
                <span>Quick Scan Results</span>
              </h2>
              <Button
                onClick={handleSubscribeToQuickScan}
                className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700"
              >
                <Plus className="h-4 w-4 mr-2" />
                Subscribe to Monitor
              </Button>
            </div>
            
            <div className="space-y-4">
              {convertQuickScanToMatches(quickScanResult).map((match, index) => (
                <Card key={`${match.id}-${index}`} className={`glass ${match.type === 'quick-scan-summary' ? 'border-orange-400/30' : 'border-yellow-400/30'} hover-glow`}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <Badge variant="outline" className="border-orange-400 text-orange-400">
                            {match.term}
                          </Badge>
                          {getSeverityBadge(match.severity)}
                          {match.type === 'quick-scan-summary' && (
                            <Badge className="bg-orange-500/20 text-orange-300 border-orange-400">
                              <Zap className="h-3 w-3 mr-1" />
                              AI Analysis
                            </Badge>
                          )}
                        </div>
                        <CardTitle className="text-white text-lg">{match.incident_title}</CardTitle>
                        <CardDescription className="text-gray-400 mt-2">
                          <div className="flex items-center justify-between text-sm">
                            <span>Source: {match.source}</span>
                            <span>{formatDate(match.date)}</span>
                          </div>
                        </CardDescription>
                        
                        {/* Show full summary for AI analysis */}
                        {match.type === 'quick-scan-summary' && match.summary && (
                          <div className="mt-4 bg-gray-800/50 rounded-lg p-4">
                            <pre className="text-gray-300 text-sm whitespace-pre-wrap font-sans leading-relaxed">
                              {match.summary}
                            </pre>
                          </div>
                        )}
                      </div>
                      {match.type === 'quick-scan-summary' ? (
                        <Zap className="h-5 w-5 text-orange-400 ml-4 flex-shrink-0" />
                      ) : (
                        <ExternalLink className="h-5 w-5 text-gray-400 ml-4 flex-shrink-0" />
                      )}
                    </div>
                  </CardHeader>
                </Card>
              ))}
            </div>
            
            {/* Success message for quick scan */}
            <Card className="glass border-green-500/30 mt-4">
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <CheckCircle className="h-5 w-5 text-green-400" />
                  <div>
                    <p className="text-green-300 font-semibold">Quick Scan Completed</p>
                    <p className="text-gray-400 text-sm">
                      AI analysis of "{quickScanResult.query}" threats completed. Click "Subscribe to Monitor" for ongoing surveillance.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </section>
        )}

        {/* Intelligence Matches Section */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-white">
              All Intelligence Matches ({getFilteredAndSortedMatches().length})
            </h2>
            <div className="flex items-center space-x-2">
              <Button
                onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                variant="outline"
                size="sm"
                className="border-gray-600 text-gray-300 hover:bg-gray-800"
              >
                {sortOrder === 'asc' ? <SortAsc className="h-4 w-4" /> : <SortDesc className="h-4 w-4" />}
              </Button>
            </div>
          </div>

          {/* Filter Controls */}
          <div className="mb-6 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {/* Search Filter */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  placeholder="Search threats..."
                  value={filterTerm}
                  onChange={(e) => setFilterTerm(e.target.value)}
                  className="pl-10 bg-gray-800 border-gray-600 text-white placeholder-gray-500 focus:border-cyan-400"
                />
              </div>

              {/* Severity Filter */}
              <div>
                <select
                  value={severityFilter}
                  onChange={(e) => setSeverityFilter(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-md text-white focus:border-cyan-400"
                >
                  <option value="all">All Severities</option>
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>

              {/* Source Filter */}
              <div>
                <select
                  value={sourceFilter}
                  onChange={(e) => setSourceFilter(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-md text-white focus:border-cyan-400"
                >
                  <option value="all">All Sources</option>
                  <option value="quick-scan">Quick Scan Results</option>
                  <option value="monitoring">Continuous Monitoring</option>
                  {getUniqueSourcesForFilter().slice(0, 5).map(source => (
                    <option key={source} value={source}>{source}</option>
                  ))}
                </select>
              </div>

              {/* Sort By Filter */}
              <div>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-md text-white focus:border-cyan-400"
                >
                  <option value="date">Sort by Date</option>
                  <option value="severity">Sort by Severity</option>
                  <option value="title">Sort by Title</option>
                </select>
              </div>
            </div>

            {/* Active Filters Display */}
            {(filterTerm || severityFilter !== 'all' || sourceFilter !== 'all') && (
              <div className="flex items-center space-x-2">
                <Filter className="h-4 w-4 text-gray-400" />
                <span className="text-sm text-gray-400">Active filters:</span>
                {filterTerm && (
                  <Badge variant="outline" className="border-cyan-400 text-cyan-400">
                    Search: {filterTerm}
                  </Badge>
                )}
                {severityFilter !== 'all' && (
                  <Badge variant="outline" className="border-yellow-400 text-yellow-400">
                    Severity: {severityFilter}
                  </Badge>
                )}
                {sourceFilter !== 'all' && (
                  <Badge variant="outline" className="border-green-400 text-green-400">
                    Source: {sourceFilter}
                  </Badge>
                )}
                <Button
                  onClick={() => {
                    setFilterTerm('');
                    setSeverityFilter('all');
                    setSourceFilter('all');
                  }}
                  variant="outline"
                  size="sm"
                  className="border-red-400 text-red-400 hover:bg-red-900/20"
                >
                  Clear All
                </Button>
              </div>
            )}
          </div>

          {/* Intelligence Matches Display */}
          {getFilteredAndSortedMatches().length > 0 ? (
            <div className="space-y-4">
              {getFilteredAndSortedMatches().map((match, index) => (
                <Card key={`${match.id}-${index}`} className={`glass hover-glow ${
                  match.type === 'quick-scan-summary' ? 'border-orange-400/30' : 
                  match.type === 'discovered-link' ? 'border-blue-400/30' : 'border-gray-700'
                }`}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <Badge variant="outline" className={
                            match.type === 'quick-scan-summary' ? 'border-orange-400 text-orange-400' :
                            match.type === 'discovered-link' ? 'border-blue-400 text-blue-400' :
                            'border-cyan-400 text-cyan-400'
                          }>
                            {match.term}
                          </Badge>
                          {getSeverityBadge(match.severity)}
                          {match.type === 'quick-scan-summary' && (
                            <Badge className="bg-orange-500/20 text-orange-300 border-orange-400">
                              <Zap className="h-3 w-3 mr-1" />
                              AI Analysis
                            </Badge>
                          )}
                          {match.type === 'discovered-link' && (
                            <Badge className="bg-blue-500/20 text-blue-300 border-blue-400">
                              <ExternalLink className="h-3 w-3 mr-1" />
                              Discovered Link
                            </Badge>
                          )}
                        </div>
                        <CardTitle className="text-white text-lg">
                          {match.url ? (
                            <a 
                              href={match.url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="hover:text-cyan-400 transition-colors duration-200"
                            >
                              {match.incident_title}
                            </a>
                          ) : (
                            match.incident_title
                          )}
                        </CardTitle>
                        <CardDescription className="text-gray-400 mt-2">
                          <div className="flex items-center justify-between text-sm">
                            <span>Source: {match.source}</span>
                            <span>{formatDate(match.date)}</span>
                          </div>
                          {match.snippet && (
                            <div className="mt-2 text-gray-300 text-sm">
                              {match.snippet}
                            </div>
                          )}
                        </CardDescription>
                        
                        {/* Show full summary for AI analysis */}
                        {match.type === 'quick-scan-summary' && match.summary && (
                          <div className="mt-4 bg-gray-800/50 rounded-lg p-4">
                            <pre className="text-gray-300 text-sm whitespace-pre-wrap font-sans leading-relaxed">
                              {match.summary}
                            </pre>
                          </div>
                        )}
                      </div>
                      {match.url ? (
                        <a 
                          href={match.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="ml-4 flex-shrink-0"
                        >
                          <ExternalLink className="h-5 w-5 text-gray-400 hover:text-cyan-400 transition-colors" />
                        </a>
                      ) : match.type === 'quick-scan-summary' ? (
                        <Zap className="h-5 w-5 text-orange-400 ml-4 flex-shrink-0" />
                      ) : (
                        <ExternalLink className="h-5 w-5 text-gray-400 ml-4 flex-shrink-0" />
                      )}
                    </div>
                  </CardHeader>
                </Card>
              ))}
            </div>
          ) : (
            <Card className="glass border-gray-700">
              <CardContent className="p-6 text-center">
                <AlertTriangle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-400 mb-2">
                  {filterTerm || severityFilter !== 'all' || sourceFilter !== 'all'
                    ? 'No intelligence matches found for the current filters.'
                    : 'No intelligence matches found yet.'
                  }
                </p>
                <p className="text-sm text-gray-500">
                  {filterTerm || severityFilter !== 'all' || sourceFilter !== 'all'
                    ? 'Try adjusting your filters or perform a Quick Scan to discover new threats.'
                    : "Perform a Quick Scan or set up monitoring to start discovering threats."
                  }
                </p>
              </CardContent>
            </Card>
          )}
        </section>
      </div>
    </div>
  );
};

export default IntelligenceFeed;