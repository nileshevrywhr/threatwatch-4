import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { Shield, Plus, RefreshCw, Clock, ExternalLink, AlertTriangle, Zap, CheckCircle } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const IntelligenceFeed = () => {
  const [searchParams] = useSearchParams();
  const [userData, setUserData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [lastRefresh, setLastRefresh] = useState(new Date());
  const [quickScanResult, setQuickScanResult] = useState(null);
  const navigate = useNavigate();

  const userEmail = searchParams.get('email');
  const quickScanData = searchParams.get('quickScan');

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
    
    // Handle quick scan data from URL
    if (quickScanData) {
      try {
        const parsedQuickScan = JSON.parse(decodeURIComponent(quickScanData));
        setQuickScanResult(parsedQuickScan);
      } catch (error) {
        console.error('Failed to parse quick scan data:', error);
      }
    }
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchUserData, 30000);
    return () => clearInterval(interval);
  }, [userEmail, quickScanData]);

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
      summary: quickScan.summary
    });
    
    // Add each key threat as separate intelligence matches
    if (quickScan.key_threats && quickScan.key_threats.length > 0) {
      quickScan.key_threats.forEach((threat, index) => {
        matches.push({
          id: `quick-scan-threat-${Date.now()}-${index}`,
          term: quickScan.query,
          incident_title: threat,
          source: 'AI Threat Extraction',
          date: quickScan.timestamp,
          severity: 'Medium',
          type: 'quick-scan-threat'
        });
      });
    }
    
    return matches;
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
          <h2 className="text-xl font-semibold text-white mb-4">
            {quickScanResult ? 'Continuous Monitoring Matches' : 'Recent Intelligence Matches'}
          </h2>
          {userData?.intelligence_matches?.length > 0 ? (
            <div className="space-y-4">
              {userData.intelligence_matches.map((match, index) => (
                <Card key={`${match.id}-${index}`} className="glass border-gray-700 hover-glow">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <Badge variant="outline" className="border-cyan-400 text-cyan-400">
                            {match.term}
                          </Badge>
                          {getSeverityBadge(match.severity)}
                        </div>
                        <CardTitle className="text-white text-lg">{match.incident_title}</CardTitle>
                        <CardDescription className="text-gray-400 mt-2">
                          <div className="flex items-center justify-between text-sm">
                            <span>Source: {match.source}</span>
                            <span>{formatDate(match.date)}</span>
                          </div>
                        </CardDescription>
                      </div>
                      <ExternalLink className="h-5 w-5 text-gray-400 ml-4 flex-shrink-0" />
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
                  {quickScanResult 
                    ? 'No continuous monitoring subscriptions yet.' 
                    : 'No intelligence matches found yet.'
                  }
                </p>
                <p className="text-sm text-gray-500">
                  {quickScanResult
                    ? 'Subscribe to the Quick Scan results above to start continuous monitoring.'
                    : "We'll notify you as soon as we detect threats related to your subscribed terms."
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