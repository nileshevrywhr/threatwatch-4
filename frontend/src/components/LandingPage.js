import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Alert, AlertDescription } from './ui/alert';
import { Shield, Eye, Bell, Target, ArrowRight, CheckCircle, Zap } from 'lucide-react';

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
  const [quickScanResult, setQuickScanResult] = useState(null);
  const navigate = useNavigate();

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.term || !formData.email) {
      setMessage('Please fill in required fields');
      setMessageType('error');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      const response = await axios.post(`${API}/subscribe`, {
        term: formData.term,
        email: formData.email,
        phone: formData.phone || undefined
      });

      setMessage(`Now monitoring attacks related to "${formData.term}". You'll receive alerts via email${formData.phone ? '/SMS' : ''}.`);
      setMessageType('success');
      
      // Redirect to intelligence feed after 2 seconds
      setTimeout(() => {
        navigate(`/feed?email=${encodeURIComponent(formData.email)}`);
      }, 2000);

    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Subscription failed. Please try again.';
      setMessage(errorMessage);
      setMessageType('error');
    } finally {
      setLoading(false);
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

          {/* Subscription Form */}
          <div className="max-w-md mx-auto">
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

                  {message && (
                    <Alert className={messageType === 'success' ? 'border-green-500 bg-green-900/20' : 'border-red-500 bg-red-900/20'}>
                      <CheckCircle className="h-4 w-4" />
                      <AlertDescription className={messageType === 'success' ? 'text-green-300' : 'text-red-300'}>
                        {message}
                      </AlertDescription>
                    </Alert>
                  )}

                  <Button
                    type="submit"
                    disabled={loading}
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
                </form>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;