import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Alert, AlertDescription } from './ui/alert';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import { Target, ArrowRight, CheckCircle, Zap, Eye, Bell, LogIn, Loader2 } from 'lucide-react';
import Header from './Header';
import AuthModal from './AuthModal';
import { useAnalytics } from '../services/analytics';
import { useAuth } from './AuthProvider';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const LandingPage = () => {
  const analytics = useAnalytics();
  const { user, session } = useAuth();

  const [formData, setFormData] = useState({
    term: '',
    email: '',
    phone: '',
    frequency: 'daily'
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('');
  const [quickScanLoading, setQuickScanLoading] = useState(false);
  const [quickScanProgress, setQuickScanProgress] = useState({
    stage: 0,
    message: '',
    progress: 0
  });
  const [feedEmail, setFeedEmail] = useState('');
  const [feedLoading, setFeedLoading] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);

  const navigate = useNavigate();

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.term) {
      setMessage('Please enter a keyword to monitor');
      setMessageType('error');
      return;
    }

    // Check if user is authenticated
    if (!user) {
      setMessage('Please sign in to set up monitoring');
      setMessageType('error');
      setShowAuthModal(true);
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      const response = await axios.post(`${API}/monitors`, {
        term: formData.term,
        frequency: formData.frequency
      }, {
        headers: {
          'Authorization': `Bearer ${session?.access_token}`,
          'Content-Type': 'application/json'
        }
      });

      setMessage(`Now monitoring attacks related to "${formData.term}" (${formData.frequency}). You'll receive alerts via email.`);
      setMessageType('success');

      // Redirect to intelligence feed after 2 seconds
      setTimeout(() => {
        navigate(`/feed?email=${encodeURIComponent(user.email)}`);
      }, 2000);

    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Subscription failed. Please try again.';
      setMessage(errorMessage);
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickScan = async () => {
    if (!formData.term) {
      setMessage('Please enter a keyword to scan');
      setMessageType('error');
      return;
    }

    // Check if user is authenticated
    if (!user) {
      setMessage('Please sign in to perform Quick Scans');
      setMessageType('error');
      setShowAuthModal(true);

      // Track authentication barrier for drop-off analysis
      analytics.trackFunnelStep('scan_to_download', 'auth_required', false);
      return;
    }

    // Track Quick Scan initiation - Key Metric #2: Searches per user
    const scanStartTime = Date.now();
    analytics.trackQuickScanUI('initiated', {
      query: formData.term,
      user_authenticated: true
    });

    setQuickScanLoading(true);
    setMessage('');

    // Progress stages
    const stages = [
      { message: 'Preparing search query...', progress: 10 },
      { message: 'Searching Google for recent news...', progress: 30 },
      { message: 'Analyzing discovered articles...', progress: 60 },
      { message: 'Generating AI-powered insights...', progress: 85 },
      { message: 'Finalizing results...', progress: 100 }
    ];

    try {
      // Simulate progress updates
      for (let i = 0; i < stages.length - 1; i++) {
        setQuickScanProgress({
          stage: i,
          message: stages[i].message,
          progress: stages[i].progress
        });
        await new Promise(resolve => setTimeout(resolve, 800)); // 800ms between stages
      }

      // Set final stage before API call
      setQuickScanProgress({
        stage: stages.length - 2,
        message: stages[stages.length - 2].message,
        progress: stages[stages.length - 2].progress
      });

      const response = await axios.post(`${API}/quick-scan`, {
        query: formData.term
      }, {
        headers: {
          'Authorization': `Bearer ${session?.access_token}`,
          'Content-Type': 'application/json'
        }
      });

      // Complete progress
      setQuickScanProgress({
        stage: stages.length - 1,
        message: stages[stages.length - 1].message,
        progress: stages[stages.length - 1].progress
      });

      // Track successful scan completion
      const scanDuration = (Date.now() - scanStartTime) / 1000;
      analytics.trackQuickScanUI('completed', {
        query: formData.term,
        scan_duration: scanDuration,
        articles_found: response.data.discovered_links?.length || 0,
        success: true
      });

      // Track funnel progression
      analytics.trackFunnelStep('scan_to_download', 'scan_completed', true, scanDuration);

      // Short delay before redirect to show completion
      await new Promise(resolve => setTimeout(resolve, 500));

      // Store enhanced quick scan results with email association and redirect
      const userEmail = user.email;
      const quickScanData = {
        ...response.data,
        userEmail: userEmail,
        timestamp: new Date().toISOString()
      };
      sessionStorage.setItem(`quickScanResult_${userEmail}`, JSON.stringify(quickScanData));
      navigate(`/feed?email=${encodeURIComponent(userEmail)}&quickScan=true`);

    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Quick scan failed. Please try again.';
      const scanDuration = (Date.now() - scanStartTime) / 1000;

      // Track scan failure analytics
      analytics.trackQuickScanUI('failed', {
        query: formData.term,
        error_message: errorMessage,
        scan_duration: scanDuration,
        success: false
      });

      // Track API error
      analytics.trackAPIError('/api/quick-scan', error.response?.status || 500, errorMessage, {
        method: 'POST',
        duration: scanDuration
      });

      setMessage(errorMessage);
      setMessageType('error');
      setQuickScanLoading(false);
      setQuickScanProgress({ stage: 0, message: '', progress: 0 });
    }
  };

  const handleViewFeed = async (e) => {
    e.preventDefault();
    if (!feedEmail) {
      setMessage('Please enter your email address');
      setMessageType('feed-error');
      return;
    }

    setFeedLoading(true);
    setMessage('');

    try {
      // Check if user has any subscriptions by calling the status endpoint
      // This part might need auth if backend requires it, but keeping it as is for now
      const response = await axios.get(`${API}/status`, {
        params: { email: feedEmail }
      });

      // Navigate to feed regardless of whether they have subscriptions
      // This allows users to see their empty feed and add subscriptions
      navigate(`/feed?email=${encodeURIComponent(feedEmail)}`);

    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to load feed. Please try again.';
      setMessage(errorMessage);
      setMessageType('feed-error');
      setFeedLoading(false);
    }
  };

  const handleHeaderAuthSuccess = useCallback(() => {
    navigate('/feed');
  }, [navigate]);

  const handleAuthModalClose = useCallback(() => {
    setShowAuthModal(false);
  }, []);

  const handleAuthModalSuccess = useCallback(() => {
    setShowAuthModal(false);
    navigate('/feed');
  }, [navigate]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-gray-900 to-slate-800">
      <Header onAuthSuccess={handleHeaderAuthSuccess} />

      {/* Hero Section */}
      <section className="py-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <div className="mb-8">
            <h1 className="text-5xl md:text-6xl font-bold text-white mb-6 leading-tight">
              Track Attacks on Your
              <span className="block gradient-text">Industry & Products</span>
            </h1>
            <p className="text-xl text-gray-300 max-w-2xl mx-auto leading-relaxed">
              We monitor security incidents, reports, and attacks happening worldwide.
              Subscribe to alerts on the terms that matter to you.
            </p>
          </div>

          {/* Features Grid */}
          <div className="grid md:grid-cols-3 gap-6 mb-16">
            <div className="glass rounded-lg p-6 hover-glow">
              <Target className="h-12 w-12 text-cyan-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-white mb-2">Targeted Intelligence</h3>
              <p className="text-gray-400 text-sm">Monitor specific keywords, products, and threat vectors</p>
            </div>
            <div className="glass rounded-lg p-6 hover-glow">
              <Bell className="h-12 w-12 text-orange-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-white mb-2">Real-time Alerts</h3>
              <p className="text-gray-400 text-sm">Get notified immediately when threats are detected</p>
            </div>
            <div className="glass rounded-lg p-6 hover-glow">
              <Eye className="h-12 w-12 text-green-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-white mb-2">Global Coverage</h3>
              <p className="text-gray-400 text-sm">Comprehensive monitoring across all threat sources</p>
            </div>
          </div>

          {/* Action Cards */}
          <div className="max-w-4xl mx-auto grid md:grid-cols-2 gap-6">

            {/* Start New Monitoring */}
            <Card className="glass border-gray-700">
              <CardHeader className="text-center">
                <CardTitle className="text-2xl text-white">Start Monitoring</CardTitle>
                <CardDescription className="text-gray-400">
                  Enter a keyword or product name to begin threat monitoring
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <Label htmlFor="term" className="text-gray-300">
                      Keyword/Product Name *
                    </Label>
                    <Input
                      id="term"
                      name="term"
                      placeholder="e.g., ATM fraud, POS malware, NCR"
                      value={formData.term}
                      onChange={handleInputChange}
                      className="bg-gray-800 border-gray-600 text-white placeholder-gray-500 focus:border-cyan-400"
                      required
                    />
                  </div>

                  <div>
                    <Label htmlFor="frequency" className="text-gray-300">
                      Monitoring Frequency
                    </Label>
                    <Select
                      value={formData.frequency}
                      onValueChange={(value) => setFormData({ ...formData, frequency: value })}
                    >
                      <SelectTrigger className="w-full bg-gray-800 border-gray-600 text-white">
                        <SelectValue placeholder="Select frequency" />
                      </SelectTrigger>
                      <SelectContent className="bg-gray-800 border-gray-700 text-white">
                        <SelectItem value="daily">Daily</SelectItem>
                        <SelectItem value="weekly">Weekly</SelectItem>
                        <SelectItem value="monthly">Monthly</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {user && (
                    <div className="bg-gray-800/50 rounded-lg p-3 border border-gray-600">
                      <div className="flex items-center space-x-2">
                        <CheckCircle className="h-4 w-4 text-green-400" />
                        <span className="text-sm text-gray-300">
                          Monitoring for: <span className="text-white font-semibold">{user.email}</span>
                        </span>
                      </div>
                      <div className="text-xs text-gray-400 mt-1">
                        {(user.user_metadata?.subscription_tier === 'free' || !user.user_metadata?.subscription_tier) && `${user.monitoring_terms_count || 0}/0 monitoring terms (upgrade to add more)`}
                        {user.user_metadata?.subscription_tier === 'pro' && `${user.monitoring_terms_count || 0}/10 monitoring terms used`}
                        {user.user_metadata?.subscription_tier === 'enterprise' && `${user.monitoring_terms_count || 0}/50 monitoring terms used`}
                      </div>
                    </div>
                  )}

                  {!user && (
                    <>
                      <div>
                        <Label htmlFor="email" className="text-gray-300">
                          Email Address *
                        </Label>
                        <Input
                          id="email"
                          name="email"
                          type="email"
                          placeholder="your@email.com"
                          value={formData.email}
                          onChange={handleInputChange}
                          className="bg-gray-800 border-gray-600 text-white placeholder-gray-500 focus:border-cyan-400"
                          required
                        />
                      </div>

                      <div>
                        <Label htmlFor="phone" className="text-gray-300">
                          Phone Number (optional)
                        </Label>
                        <Input
                          id="phone"
                          name="phone"
                          type="tel"
                          placeholder="+1 (555) 123-4567"
                          value={formData.phone}
                          onChange={handleInputChange}
                          className="bg-gray-800 border-gray-600 text-white placeholder-gray-500 focus:border-cyan-400"
                        />
                      </div>
                    </>
                  )}

                  {message && (
                    <Alert className={messageType === 'success' ? 'border-green-500 bg-green-900/20' : 'border-red-500 bg-red-900/20'}>
                      <CheckCircle className="h-4 w-4" />
                      <AlertDescription className={messageType === 'success' ? 'text-green-300' : 'text-red-300'}>
                        {message}
                      </AlertDescription>
                    </Alert>
                  )}

                  <div className="space-y-3">
                    <Button
                      type="submit"
                      disabled={loading || quickScanLoading}
                      className="w-full bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white font-semibold py-3 transition-all duration-300"
                    >
                      {loading ? (
                        <div className="flex items-center space-x-2">
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          <span>Setting up monitoring...</span>
                        </div>
                      ) : (
                        <div className="flex items-center space-x-2">
                          <span>Start Monitoring</span>
                          <ArrowRight className="h-4 w-4" />
                        </div>
                      )}
                    </Button>

                    <Button
                      type="button"
                      onClick={handleQuickScan}
                      disabled={loading || quickScanLoading}
                      variant="outline"
                      className="w-full border-orange-500 text-orange-400 hover:bg-orange-500 hover:text-white font-semibold py-3 transition-all duration-300 relative overflow-hidden"
                    >
                      {quickScanLoading ? (
                        <div className="w-full">
                          {/* Progress bar background */}
                          <div className="absolute inset-0 bg-gradient-to-r from-orange-500/20 to-orange-600/20"
                            style={{
                              width: `${quickScanProgress.progress}%`,
                              transition: 'width 0.8s ease-in-out'
                            }}>
                          </div>

                          {/* Progress content */}
                          <div className="relative z-10 flex flex-col items-center space-y-1" role="status" aria-live="polite">
                            <div className="flex items-center space-x-2">
                              <Loader2 className="h-4 w-4 animate-spin text-orange-400" />
                              <span className="text-sm">{quickScanProgress.message}</span>
                            </div>
                            <div
                              role="progressbar"
                              aria-valuenow={quickScanProgress.progress}
                              aria-valuemin="0"
                              aria-valuemax="100"
                              className="w-full bg-gray-700 rounded-full h-1.5 mt-2"
                            >
                              <div
                                className="bg-gradient-to-r from-orange-400 to-orange-500 h-1.5 rounded-full transition-all duration-800 ease-out"
                                style={{ width: `${quickScanProgress.progress}%` }}
                              ></div>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="flex items-center space-x-2">
                          <Zap className="h-4 w-4" />
                          <span>AI-Powered Quick Scan</span>
                        </div>
                      )}
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>

            {/* View Existing Feed */}
            <Card className="glass border-gray-700">
              <CardHeader className="text-center">
                <CardTitle className="text-2xl text-white">View My Feed</CardTitle>
                <CardDescription className="text-gray-400">
                  Access your existing intelligence feed and subscriptions
                </CardDescription>
              </CardHeader>
              <CardContent>
                {user ? (
                  <div className="space-y-4">
                    <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-600">
                      <div className="flex items-center space-x-2 mb-2">
                        <CheckCircle className="h-4 w-4 text-green-400" />
                        <span className="text-white font-semibold">{user.user_metadata?.full_name || 'User'}</span>
                      </div>
                      <p className="text-sm text-gray-400">{user.email}</p>
                      <div className="mt-2 flex items-center space-x-2">
                        <span className="text-xs text-gray-500">Plan:</span>
                        <span className="text-xs capitalize text-cyan-400 font-semibold">{user.user_metadata?.subscription_tier || 'free'}</span>
                      </div>
                    </div>

                    <Button
                      onClick={() => navigate(`/feed?email=${encodeURIComponent(user.email)}`)}
                      className="w-full bg-gradient-to-r from-green-500 to-teal-600 hover:from-green-600 hover:to-teal-700 text-white font-semibold py-3 transition-all duration-300"
                    >
                      <div className="flex items-center space-x-2">
                        <Eye className="h-4 w-4" />
                        <span>View My Feed</span>
                      </div>
                    </Button>
                  </div>
                ) : (
                  <div className="text-center space-y-4">
                    <p className="text-gray-400">Sign in to access your personalized intelligence feed</p>
                    <Button
                      onClick={() => setShowAuthModal(true)}
                      className="w-full bg-gradient-to-r from-green-500 to-teal-600 hover:from-green-600 hover:to-teal-700 text-white font-semibold py-3 transition-all duration-300"
                    >
                      <div className="flex items-center space-x-2">
                        <LogIn className="h-4 w-4" />
                        <span>Sign In to View Feed</span>
                      </div>
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>

          </div>
        </div>
      </section>

      {/* Authentication Modal for page content triggers */}
      <AuthModal
        isOpen={showAuthModal}
        onClose={handleAuthModalClose}
        onAuthSuccess={handleAuthModalSuccess}
      />
    </div>
  );
};

export default LandingPage;
