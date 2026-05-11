import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import {
  Shield,
  Search,
  Zap,
  Bell,
  Lock,
  ChevronRight,
  CheckCircle,
  ArrowRight,
  Loader2,
  Eye,
  LogIn,
  Monitor,
  Globe,
  Database,
  BarChart
} from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import Header from './Header';
import AuthModal from './AuthModal';
import { createMonitor, quickScan } from '../lib/api';
import { useAuth } from './AuthProvider';

const LandingPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [formData, setFormData] = useState({
    term: '',
    frequency: 'daily',
    email: '',
    phone: ''
  });
  const [loading, setLoading] = useState(false);
  const [quickScanLoading, setQuickScanLoading] = useState(false);
  const [quickScanProgress, setQuickScanProgress] = useState({ progress: 0, message: '' });
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('success');
  const [showAuthModal, setShowAuthModal] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleFrequencyChange = (value) => {
    setFormData(prev => ({ ...prev, frequency: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      if (!user && !formData.email) {
        setMessageType('error');
        setMessage('Please provide an email address or sign in.');
        setLoading(false);
        return;
      }

      const monitorData = {
        term: formData.term,
        frequency: formData.frequency,
        email: user ? user.email : formData.email,
        phone: formData.phone,
        active: true
      };

      await createMonitor(monitorData);

      if (!user) {
        setMessageType('success');
        setMessage('Monitor created! Please sign in to view your feed.');
        setShowAuthModal(true);
      } else {
        navigate('/feed');
      }
    } catch (err) {
      setMessageType('error');
      setMessage(err.message || 'Failed to create monitor. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickScan = async () => {
    if (!formData.term) {
      setMessageType('error');
      setMessage('Please enter a search term for the quick scan.');
      return;
    }

    setQuickScanLoading(true);
    setQuickScanProgress({ progress: 10, message: 'Initializing AI agents...' });

    try {
      const progressSteps = [
        { progress: 30, message: 'Scanning threat databases...' },
        { progress: 50, message: 'Analyzing data leaks...' },
        { progress: 75, message: 'Processing with GPT-4...' },
        { progress: 90, message: 'Generating report...' }
      ];

      for (const step of progressSteps) {
        await new Promise(resolve => setTimeout(resolve, 800));
        setQuickScanProgress(step);
      }

      const result = await quickScan(formData.term);
      sessionStorage.setItem(`quickScanResult_${formData.term}`, JSON.stringify(result));

      setQuickScanProgress({ progress: 100, message: 'Scan complete!' });
      setTimeout(() => {
        navigate(`/feed?term=${encodeURIComponent(formData.term)}`);
      }, 500);
    } catch (err) {
      setMessageType('error');
      setMessage(err.message || 'Quick scan failed. Please try again.');
      setQuickScanLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header onAuthSuccess={() => navigate('/feed')} />

      {/* Hero Section */}
      <section className="relative pt-20 pb-32 overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 relative z-10">
          <div className="text-center mb-16">
            <Badge className="mb-4 bg-cyan-500/10 text-cyan-400 border-cyan-500/20 px-4 py-1 text-sm">
              Enterprise-Grade Threat Intelligence
            </Badge>
            <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-6">
              Protect Your Brand with <br />
              <span className="bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-blue-600">
                AI-Driven Vigilance
              </span>
            </h1>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Monitor the deep web, social platforms, and threat databases in real-time.
              Get instant alerts when your company, products, or data are mentioned in risk contexts.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            {/* Monitoring Form */}
            <Card className="border-border bg-card">
              <CardHeader>
                <CardTitle className="text-2xl">Start Monitoring</CardTitle>
                <CardDescription>
                  Configure your first monitoring term and get real-time alerts
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="space-y-2">
                    <Label htmlFor="term">What do you want to monitor? *</Label>
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input
                        id="term"
                        name="term"
                        placeholder="Company name, product, or keyword"
                        value={formData.term}
                        onChange={handleInputChange}
                        className="pl-10"
                        required
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Monitoring Frequency</Label>
                    <Select value={formData.frequency} onValueChange={handleFrequencyChange}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select frequency" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="daily">Daily</SelectItem>
                        <SelectItem value="weekly">Weekly</SelectItem>
                        <SelectItem value="monthly">Monthly</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {user && (
                    <div className="bg-muted rounded-lg p-3 border border-border">
                      <div className="flex items-center space-x-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        <span className="text-sm">
                          Monitoring for: <span className="font-semibold">{user.email}</span>
                        </span>
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        {(user.user_metadata?.subscription_tier === 'free' || !user.user_metadata?.subscription_tier) && `${user.monitoring_terms_count || 0}/0 monitoring terms (upgrade to add more)`}
                        {user.user_metadata?.subscription_tier === 'pro' && `${user.monitoring_terms_count || 0}/10 monitoring terms used`}
                        {user.user_metadata?.subscription_tier === 'enterprise' && `${user.monitoring_terms_count || 0}/50 monitoring terms used`}
                      </div>
                    </div>
                  )}

                  {!user && (
                    <>
                      <div className="space-y-2">
                        <Label htmlFor="email">Email Address *</Label>
                        <Input
                          id="email"
                          name="email"
                          type="email"
                          placeholder="your@email.com"
                          value={formData.email}
                          onChange={handleInputChange}
                          required
                        />
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="phone">Phone Number (optional)</Label>
                        <Input
                          id="phone"
                          name="phone"
                          type="tel"
                          placeholder="+1 (555) 123-4567"
                          value={formData.phone}
                          onChange={handleInputChange}
                        />
                      </div>
                    </>
                  )}

                  {message && (
                    <Alert variant={messageType === 'success' ? 'default' : 'destructive'} className={messageType === 'success' ? 'border-green-500 bg-green-500/10' : ''}>
                      <CheckCircle className="h-4 w-4" />
                      <AlertDescription className={messageType === 'success' ? 'text-green-500' : ''}>
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
                      className="w-full border-orange-500 text-orange-500 hover:bg-orange-500 hover:text-white font-semibold py-3 transition-all duration-300 relative overflow-hidden"
                    >
                      {quickScanLoading ? (
                        <div className="w-full">
                          {/* Progress bar background */}
                          <div className="absolute inset-0 bg-orange-500/10"
                            style={{
                              width: `${quickScanProgress.progress}%`,
                              transition: 'width 0.8s ease-in-out'
                            }}>
                          </div>

                          {/* Progress content */}
                          <div className="relative z-10 flex flex-col items-center space-y-1" role="status" aria-live="polite">
                            <div className="flex items-center space-x-2">
                              <Loader2 className="h-4 w-4 animate-spin" />
                              <span className="text-sm">{quickScanProgress.message}</span>
                            </div>
                            <div
                              role="progressbar"
                              aria-valuenow={quickScanProgress.progress}
                              aria-valuemin="0"
                              aria-valuemax="100"
                              className="w-full bg-muted rounded-full h-1.5 mt-2"
                            >
                              <div
                                className="bg-orange-500 h-1.5 rounded-full transition-all duration-800 ease-out"
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
            <Card className="border-border bg-card">
              <CardHeader className="text-center">
                <CardTitle className="text-2xl">View My Feed</CardTitle>
                <CardDescription>
                  Access your existing intelligence feed and subscriptions
                </CardDescription>
              </CardHeader>
              <CardContent>
                {user ? (
                  <div className="space-y-4">
                    <div className="bg-muted rounded-lg p-4 border border-border">
                      <div className="flex items-center space-x-2 mb-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        <span className="font-semibold">{user.user_metadata?.full_name || 'User'}</span>
                      </div>
                      <p className="text-sm text-muted-foreground">{user.email}</p>
                      <div className="mt-2 flex items-center space-x-2">
                        <span className="text-xs text-muted-foreground">Plan:</span>
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
                    <p className="text-muted-foreground">Sign in to access your personalized intelligence feed</p>
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
        onClose={() => setShowAuthModal(false)}
        onAuthSuccess={() => {
          setShowAuthModal(false);
          navigate('/feed');
        }}
      />
    </div>
  );
};

export default LandingPage;
