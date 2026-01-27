import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Alert, AlertDescription } from './ui/alert';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Tooltip, TooltipContent, TooltipTrigger } from './ui/tooltip';
import { CheckCircle, AlertTriangle, User, Mail, Lock, Eye, EyeOff, Loader2 } from 'lucide-react';
import { useAnalytics } from '../services/analytics';
import { supabase } from '../lib/supabaseClient';

const AuthModal = ({ isOpen, onClose, onAuthSuccess }) => {
  const analytics = useAnalytics();
  const [activeTab, setActiveTab] = useState('login');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [timerId, setTimerId] = useState(null);

  useEffect(() => {
    return () => {
      if (timerId) clearTimeout(timerId);
    };
  }, [timerId]);

  const [loginData, setLoginData] = useState({
    email: '',
    password: ''
  });

  const [registerData, setRegisterData] = useState({
    email: '',
    password: '',
    confirm_password: '',
    full_name: ''
  });

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!loginData.email || !loginData.password) {
      setMessage('Please fill in all fields');
      setMessageType('error');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email: loginData.email,
        password: loginData.password,
      });

      if (error) throw error;

      analytics.trackAuthEvent('login', true);
      analytics.identify(data.user.id, {
        email: data.user.email,
        full_name: data.user.user_metadata?.full_name,
      });

      setMessage('Login successful!');
      setMessageType('success');

      if (onAuthSuccess) {
        onAuthSuccess(data.user, data.session?.access_token);
      }

      const id = setTimeout(() => {
        onClose();
      }, 1000);
      setTimerId(id);

    } catch (error) {
      const errorMessage = error.message || 'Login failed. Please try again.';
      analytics.trackAuthEvent('login', false, errorMessage);
      setMessage(errorMessage);
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    if (!registerData.email || !registerData.password || !registerData.confirm_password || !registerData.full_name) {
      setMessage('Please fill in all fields');
      setMessageType('error');
      return;
    }

    if (registerData.password !== registerData.confirm_password) {
      setMessage('Passwords do not match');
      setMessageType('error');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      const { data, error } = await supabase.auth.signUp({
        email: registerData.email,
        password: registerData.password,
        options: {
          data: {
            full_name: registerData.full_name,
            subscription_tier: 'free',
          },
        },
      });

      if (error) throw error;

      analytics.trackAuthEvent('register', true);
      analytics.identify(data.user.id, {
        email: data.user.email,
        full_name: registerData.full_name,
        signup_timestamp: new Date().toISOString()
      });

      setMessage('Registration successful! You are now logged in.');
      setMessageType('success');

      if (onAuthSuccess) {
        onAuthSuccess(data.user, data.session?.access_token);
      }

      const id = setTimeout(() => {
        onClose();
      }, 1000);
      setTimerId(id);

    } catch (error) {
      const errorMessage = error.message || 'Registration failed. Please try again.';
      analytics.trackAuthEvent('register', false, errorMessage);
      setMessage(errorMessage);
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e, formType) => {
    const { name, value } = e.target;
    if (formType === 'login') {
      setLoginData(prev => ({ ...prev, [name]: value }));
    } else {
      setRegisterData(prev => ({ ...prev, [name]: value }));
    }
    setMessage(''); // Clear any existing messages
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md bg-gray-900 border-gray-700">
        <DialogHeader>
          <DialogTitle className="text-2xl text-white text-center">Welcome to ThreatWatch</DialogTitle>
          <DialogDescription className="text-gray-400 text-center">
            Sign in to access advanced threat monitoring features
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-2 bg-gray-800">
            <TabsTrigger value="login" className="text-gray-300 data-[state=active]:bg-gray-700 data-[state=active]:text-white">
              Sign In
            </TabsTrigger>
            <TabsTrigger value="register" className="text-gray-300 data-[state=active]:bg-gray-700 data-[state=active]:text-white">
              Sign Up
            </TabsTrigger>
          </TabsList>

          <TabsContent value="login" className="space-y-4 mt-6">
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <Label htmlFor="loginEmail" className="text-gray-300">Email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                  <Input
                    id="loginEmail"
                    name="email"
                    type="email"
                    placeholder="your@email.com"
                    value={loginData.email}
                    onChange={(e) => handleInputChange(e, 'login')}
                    className="pl-10 bg-gray-800 border-gray-600 text-white placeholder-gray-500 focus:border-cyan-400"
                    required
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="loginPassword" className="text-gray-300">Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                  <Input
                    id="loginPassword"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Enter your password"
                    value={loginData.password}
                    onChange={(e) => handleInputChange(e, 'login')}
                    className="pl-10 pr-10 bg-gray-800 border-gray-600 text-white placeholder-gray-500 focus:border-cyan-400"
                    required
                  />
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-300 rounded-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
                        aria-label={showPassword ? "Hide password" : "Show password"}
                      >
                        {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>{showPassword ? "Hide password" : "Show password"}</p>
                    </TooltipContent>
                  </Tooltip>
                </div>
              </div>

              <Button
                type="submit"
                disabled={loading}
                className="w-full bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white font-semibold py-3"
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Signing In...
                  </>
                ) : (
                  'Sign In'
                )}
              </Button>
            </form>
          </TabsContent>

          <TabsContent value="register" className="space-y-4 mt-6">
            <form onSubmit={handleRegister} className="space-y-4">
              <div>
                <Label htmlFor="registerName" className="text-gray-300">Full Name</Label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                  <Input
                    id="registerName"
                    name="full_name"
                    type="text"
                    placeholder="Your full name"
                    value={registerData.full_name}
                    onChange={(e) => handleInputChange(e, 'register')}
                    className="pl-10 bg-gray-800 border-gray-600 text-white placeholder-gray-500 focus:border-cyan-400"
                    required
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="registerEmail" className="text-gray-300">Email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                  <Input
                    id="registerEmail"
                    name="email"
                    type="email"
                    placeholder="your@email.com"
                    value={registerData.email}
                    onChange={(e) => handleInputChange(e, 'register')}
                    className="pl-10 bg-gray-800 border-gray-600 text-white placeholder-gray-500 focus:border-cyan-400"
                    required
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="registerPassword" className="text-gray-300">Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                  <Input
                    id="registerPassword"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Create a strong password"
                    value={registerData.password}
                    onChange={(e) => handleInputChange(e, 'register')}
                    className="pl-10 pr-10 bg-gray-800 border-gray-600 text-white placeholder-gray-500 focus:border-cyan-400"
                    required
                  />
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-300 rounded-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
                        aria-label={showPassword ? "Hide password" : "Show password"}
                      >
                        {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>{showPassword ? "Hide password" : "Show password"}</p>
                    </TooltipContent>
                  </Tooltip>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Must include uppercase, lowercase, number, and be 8+ characters
                </p>
              </div>

              <div>
                <Label htmlFor="confirmPassword" className="text-gray-300">Confirm Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                  <Input
                    id="confirmPassword"
                    name="confirm_password"
                    type={showConfirmPassword ? "text" : "password"}
                    placeholder="Confirm your password"
                    value={registerData.confirm_password}
                    onChange={(e) => handleInputChange(e, 'register')}
                    className="pl-10 pr-10 bg-gray-800 border-gray-600 text-white placeholder-gray-500 focus:border-cyan-400"
                    required
                  />
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-300 rounded-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
                        aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                      >
                        {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>{showConfirmPassword ? "Hide password" : "Show password"}</p>
                    </TooltipContent>
                  </Tooltip>
                </div>
              </div>

              <Button
                type="submit"
                disabled={loading}
                className="w-full bg-gradient-to-r from-green-500 to-teal-600 hover:from-green-600 hover:to-teal-700 text-white font-semibold py-3"
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating Account...
                  </>
                ) : (
                  'Create Account'
                )}
              </Button>
            </form>
          </TabsContent>
        </Tabs>

        {message && (
          <Alert className={`mt-4 ${messageType === 'success' ? 'border-green-500 bg-green-900/20' : 'border-red-500 bg-red-900/20'}`}>
            {messageType === 'success' ? (
              <CheckCircle className="h-4 w-4" />
            ) : (
              <AlertTriangle className="h-4 w-4" />
            )}
            <AlertDescription className={messageType === 'success' ? 'text-green-300' : 'text-red-300'}>
              {message}
            </AlertDescription>
          </Alert>
        )}

        <div className="text-center text-sm text-gray-500 mt-4">
          By signing up, you start with our <span className="text-cyan-400 font-semibold">Free Plan</span>
          <br />
          3 Quick Scans per day • Upgrade anytime for more features
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default AuthModal;
