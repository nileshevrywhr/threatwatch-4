import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription
} from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import {
  Mail,
  Lock,
  User,
  Eye,
  EyeOff,
  Loader2,
  CheckCircle,
  AlertTriangle
} from 'lucide-react';
import { Alert, AlertDescription } from './ui/alert';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "./ui/tooltip";
import { supabase } from '../lib/supabaseClient';
import Logo from './Logo';

const AuthModal = ({ isOpen, onClose, onAuthSuccess }) => {
  const [activeTab, setActiveTab] = useState('login');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState(null);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [loginData, setLoginData] = useState({
    email: '',
    password: ''
  });

  const [registerData, setRegisterData] = useState({
    full_name: '',
    email: '',
    password: '',
    confirm_password: ''
  });

  const handleInputChange = (e, form) => {
    const { name, value } = e.target;
    if (form === 'login') {
      setLoginData(prev => ({ ...prev, [name]: value }));
    } else {
      setRegisterData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email: loginData.email,
        password: loginData.password,
      });

      if (error) throw error;

      setMessageType('success');
      setMessage('Successfully signed in!');
      setTimeout(() => {
        onAuthSuccess(data.user);
      }, 1000);
    } catch (err) {
      setMessageType('error');
      setMessage(err.message || 'Failed to sign in. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    if (registerData.password !== registerData.confirm_password) {
      setMessageType('error');
      setMessage('Passwords do not match.');
      setLoading(false);
      return;
    }

    try {
      const { data, error } = await supabase.auth.signUp({
        email: registerData.email,
        password: registerData.password,
        options: {
          data: {
            full_name: registerData.full_name,
            subscription_tier: 'free'
          }
        }
      });

      if (error) throw error;

      setMessageType('success');
      setMessage('Account created! Please check your email for confirmation.');
      // Auto-login after successful registration (if confirmation is not required)
      if (data.session) {
        setTimeout(() => {
          onAuthSuccess(data.user);
        }, 1500);
      }
    } catch (err) {
      setMessageType('error');
      setMessage(err.message || 'Failed to create account. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px] border-border bg-card">
        <DialogHeader>
          <DialogTitle className="flex justify-center mb-4"><Logo className="h-10" /></DialogTitle>
          <DialogDescription className="text-center">
            {activeTab === 'login'
              ? 'Access your intelligence dashboard'
              : 'Create an account to start monitoring'}
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="login">
              Sign In
            </TabsTrigger>
            <TabsTrigger value="register">
              Sign Up
            </TabsTrigger>
          </TabsList>

          <TabsContent value="login" className="space-y-4 mt-6">
            <form onSubmit={handleLogin} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="loginEmail">Email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
                  <Input
                    id="loginEmail"
                    name="email"
                    type="email"
                    placeholder="your@email.com"
                    value={loginData.email}
                    onChange={(e) => handleInputChange(e, 'login')}
                    className="pl-10"
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="loginPassword">Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
                  <Input
                    id="loginPassword"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Enter your password"
                    value={loginData.password}
                    onChange={(e) => handleInputChange(e, 'login')}
                    className="pl-10 pr-10"
                    required
                  />
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground"
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
                className="w-full bg-[#00FFB2] hover:bg-[#00E6A0] text-black text-white font-semibold py-3"
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
              <div className="space-y-2">
                <Label htmlFor="registerName">Full Name</Label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
                  <Input
                    id="registerName"
                    name="full_name"
                    type="text"
                    placeholder="Your full name"
                    value={registerData.full_name}
                    onChange={(e) => handleInputChange(e, 'register')}
                    className="pl-10"
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="registerEmail">Email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
                  <Input
                    id="registerEmail"
                    name="email"
                    type="email"
                    placeholder="your@email.com"
                    value={registerData.email}
                    onChange={(e) => handleInputChange(e, 'register')}
                    className="pl-10"
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="registerPassword">Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
                  <Input
                    id="registerPassword"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Create a strong password"
                    value={registerData.password}
                    onChange={(e) => handleInputChange(e, 'register')}
                    className="pl-10 pr-10"
                    required
                  />
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground"
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
                <p className="text-xs text-muted-foreground mt-1">
                  Must include uppercase, lowercase, number, and be 8+ characters
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirm Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
                  <Input
                    id="confirmPassword"
                    name="confirm_password"
                    type={showConfirmPassword ? "text" : "password"}
                    placeholder="Confirm your password"
                    value={registerData.confirm_password}
                    onChange={(e) => handleInputChange(e, 'register')}
                    className="pl-10 pr-10"
                    required
                  />
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground"
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
                className="w-full bg-[#00FFB2] hover:bg-[#00E6A0] text-black text-white font-semibold py-3"
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

        {message && messageType && (
          <Alert variant={messageType === 'success' ? 'default' : 'destructive'} className={`mt-4 ${messageType === 'success' ? 'border-green-500 bg-green-500/10' : ''}`}>
            {messageType === 'success' ? (
              <CheckCircle className="h-4 w-4 text-green-500" />
            ) : (
              <AlertTriangle className="h-4 w-4" />
            )}
            <AlertDescription className={messageType === 'success' ? 'text-green-500' : ''}>
              {message}
            </AlertDescription>
          </Alert>
        )}

        <div className="text-center text-sm text-muted-foreground mt-4">
          By signing up, you start with our <span className="text-[#00FFB2] font-semibold">Free Plan</span>
          <br />
          3 Quick Scans per day • Upgrade anytime for more features
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default AuthModal;
