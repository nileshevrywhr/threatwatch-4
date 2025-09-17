import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Alert, AlertDescription } from './ui/alert';
import { Shield, Eye, Bell, Target, ArrowRight, CheckCircle, Zap, LogIn, UserPlus } from 'lucide-react';
import AuthModal from './AuthModal';
import SubscriptionPlans from './SubscriptionPlans';
import UserMenu from './UserMenu';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const LandingPage = () => {
  const [formData, setFormData] = useState({
    term: '',
    email: '',
    phone: ''
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('');
  const [quickScanLoading, setQuickScanLoading] = useState(false);
  const [feedEmail, setFeedEmail] = useState('');
  const [feedLoading, setFeedLoading] = useState(false);
  
  // Authentication state
  const [user, setUser] = useState(null);
  const [authToken, setAuthToken] = useState(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [showSubscriptionPlans, setShowSubscriptionPlans] = useState(false);
  
  const navigate = useNavigate();

  // Check for existing authentication on component mount
  useEffect(() => {
    const token = localStorage.getItem('authToken');
    const userData = localStorage.getItem('user');
    
    if (token && userData) {
      try {
        const parsedUser = JSON.parse(userData);
        setUser(parsedUser);
        setAuthToken(token);
      } catch (error) {
        console.error('Failed to parse user data:', error);
        localStorage.removeItem('authToken');
        localStorage.removeItem('user');
      }
    }
  }, []);

  const handleAuthSuccess = (userData, token) => {
    setUser(userData);
    setAuthToken(token);
    setShowAuthModal(false);
  };

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
    setUser(null);
    setAuthToken(null);
    
    // Clear any session storage
    const quickScanKeys = Object.keys(sessionStorage).filter(key => key.startsWith('quickScanResult_'));
    quickScanKeys.forEach(key => sessionStorage.removeItem(key));
  };

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
    if (!user || !authToken) {
      setMessage('Please sign in to set up monitoring');
      setMessageType('error');
      setShowAuthModal(true);
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      const response = await axios.post(`${API}/subscribe`, {
        term: formData.term,
        email: user.email
      }, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });

      setMessage(`Now monitoring attacks related to "${formData.term}". You'll receive alerts via email.`);
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
    if (!user || !authToken) {
      setMessage('Please sign in to perform Quick Scans');
      setMessageType('error');
      setShowAuthModal(true);
      return;
    }

    setQuickScanLoading(true);
    setMessage('');

    try {
      const response = await axios.post(`${API}/quick-scan`, {
        query: formData.term
      }, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });

      // Store quick scan results with email association and redirect
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
      setMessage(errorMessage);
      setMessageType('error');
      setQuickScanLoading(false);
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-gray-900 to-slate-800">
      {/* Header */}
      <header className="py-6 px-4 border-b border-gray-800">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Shield className="h-8 w-8 text-cyan-400" />
            <span className="text-2xl font-bold text-white font-mono">ThreatWatch</span>
          </div>
          
          <div className="flex items-center space-x-6">
            <div className="hidden md:flex items-center space-x-6 text-gray-300">
              <div className="flex items-center space-x-2">
                <Eye className="h-4 w-4" />
                <span className="text-sm">Real-time Monitoring</span>
              </div>
              <div className="flex items-center space-x-2">
                <Bell className="h-4 w-4" />
                <span className="text-sm">Instant Alerts</span>
              </div>
            </div>
            
            {/* Authentication Section */}
            {user ? (
              <UserMenu 
                user={user} 
                onLogout={handleLogout}
                onShowSubscriptionPlans={() => setShowSubscriptionPlans(true)}
              />
            ) : (
              <div className="flex items-center space-x-3">
                <Button
                  onClick={() => setShowAuthModal(true)}
                  variant="ghost"
                  className="text-gray-300 hover:text-white hover:bg-gray-800"
                >
                  <LogIn className="h-4 w-4 mr-2" />
                  Sign In
                </Button>
                <Button
                  onClick={() => setShowAuthModal(true)}
                  className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white"
                >
                  <UserPlus className="h-4 w-4 mr-2" />
                  Get Started
                </Button>
              </div>
            )}
          </div>
        </div>
      </header>

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

                  {user && (
                    <div className="bg-gray-800/50 rounded-lg p-3 border border-gray-600">
                      <div className="flex items-center space-x-2">
                        <CheckCircle className="h-4 w-4 text-green-400" />
                        <span className="text-sm text-gray-300">
                          Monitoring for: <span className="text-white font-semibold">{user.email}</span>
                        </span>
                      </div>
                      <div className="text-xs text-gray-400 mt-1">
                        {user.subscription_tier === 'free' && `${user.monitoring_terms_count || 0}/0 monitoring terms (upgrade to add more)`}
                        {user.subscription_tier === 'pro' && `${user.monitoring_terms_count || 0}/10 monitoring terms used`}
                        {user.subscription_tier === 'enterprise' && `${user.monitoring_terms_count || 0}/50 monitoring terms used`}
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
                          <div className="animate-pulse">Setting up monitoring...</div>
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
                      className="w-full border-orange-500 text-orange-400 hover:bg-orange-500 hover:text-white font-semibold py-3 transition-all duration-300"
                    >
                      {quickScanLoading ? (
                        <div className="flex items-center space-x-2">
                          <div className="animate-pulse">Scanning latest threats...</div>
                        </div>
                      ) : (
                        <div className="flex items-center space-x-2">
                          <Zap className="h-4 w-4" />
                          <span>Quick Scan (AI-Powered)</span>
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
                <form onSubmit={handleViewFeed} className="space-y-4">
                  <div>
                    <Label htmlFor="feedEmail" className="text-gray-300">
                      Email Address *
                    </Label>
                    <Input
                      id="feedEmail"
                      name="feedEmail"
                      type="email"
                      placeholder="your@email.com"
                      value={feedEmail}
                      onChange={(e) => setFeedEmail(e.target.value)}
                      className="bg-gray-800 border-gray-600 text-white placeholder-gray-500 focus:border-cyan-400"
                      required
                    />
                  </div>

                  {message && messageType === 'feed-error' && (
                    <Alert className="border-red-500 bg-red-900/20">
                      <CheckCircle className="h-4 w-4" />
                      <AlertDescription className="text-red-300">
                        {message}
                      </AlertDescription>
                    </Alert>
                  )}

                  <Button
                    type="submit"
                    disabled={feedLoading}
                    className="w-full bg-gradient-to-r from-green-500 to-teal-600 hover:from-green-600 hover:to-teal-700 text-white font-semibold py-3 transition-all duration-300"
                  >
                    {feedLoading ? (
                      <div className="flex items-center space-x-2">
                        <div className="animate-pulse">Loading feed...</div>
                      </div>
                    ) : (
                      <div className="flex items-center space-x-2">
                        <Eye className="h-4 w-4" />
                        <span>View My Feed</span>
                      </div>
                    )}
                  </Button>
                </form>
              </CardContent>
            </Card>

          </div>
        </div>
      </section>

      {/* Authentication Modal */}
      <AuthModal 
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        onAuthSuccess={handleAuthSuccess}
      />

      {/* Subscription Plans Modal */}
      <SubscriptionPlans
        isOpen={showSubscriptionPlans}
        onClose={() => setShowSubscriptionPlans(false)}
        currentUser={user}
        authToken={authToken}
      />
    </div>
  );
};

export default LandingPage;