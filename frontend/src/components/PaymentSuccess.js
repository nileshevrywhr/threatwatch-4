import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { CheckCircle, Crown, Zap, ArrowRight, Loader2, LogIn } from 'lucide-react';
import { secureLog } from '../utils/secureLogger';
import { useAuth } from './AuthProvider';
import AuthModal from './AuthModal';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PaymentSuccess = () => {
  const [searchParams] = useSearchParams();
  const [paymentStatus, setPaymentStatus] = useState('checking');
  const [paymentData, setPaymentData] = useState(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const navigate = useNavigate();

  const { user, session, loading: authLoading } = useAuth();

  const sessionId = searchParams.get('session_id');

  useEffect(() => {
    // Wait for auth to finish loading
    if (authLoading) return;

    const checkPaymentStatus = async () => {
      if (!sessionId) {
        setPaymentStatus('error');
        return;
      }

      // Soft check for auth
      if (!user || !session) {
        setPaymentStatus('auth_required');
        return;
      }

      try {
        const response = await axios.get(`${API}/payments/status/${sessionId}`, {
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json'
          }
        });

        setPaymentData(response.data);
        setPaymentStatus(response.data.payment_status === 'paid' ? 'success' : 'pending');

      } catch (error) {
        secureLog.error('Payment status check failed:', error);
        setPaymentStatus('error');
      }
    };

    checkPaymentStatus();
  }, [sessionId, user, session, authLoading]);

  const handleAuthSuccess = () => {
    setShowAuthModal(false);
    // The useEffect will re-run because user/session will change
  };

  const getPlanIcon = (tier) => {
    return tier === 'enterprise' ? <Crown className="h-8 w-8 text-purple-400" /> : <Zap className="h-8 w-8 text-orange-400" />;
  };

  const getPlanColor = (tier) => {
    return tier === 'enterprise' ? 'border-purple-400/50' : 'border-orange-400/50';
  };

  if (authLoading || paymentStatus === 'checking') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-gray-900 to-slate-800 flex items-center justify-center">
        <Card className="glass border-gray-700 max-w-md w-full mx-4">
          <CardContent className="p-8 text-center">
            <Loader2 className="h-12 w-12 text-cyan-400 mx-auto mb-4 animate-spin" />
            <h2 className="text-xl font-semibold text-white mb-2">
              {authLoading ? 'Verifying Session' : 'Processing Payment'}
            </h2>
            <p className="text-gray-400">Please wait while we confirm your details...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (paymentStatus === 'auth_required') {
     return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-gray-900 to-slate-800 flex items-center justify-center">
        <Card className="glass border-gray-700 max-w-md w-full mx-4">
          <CardContent className="p-8 text-center">
            <div className="h-12 w-12 bg-cyan-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
               <LogIn className="h-6 w-6 text-cyan-400" />
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">Authentication Required</h2>
            <p className="text-gray-400 mb-6">Please log in to verify your payment and activate your subscription.</p>
            <Button
              onClick={() => setShowAuthModal(true)}
              className="w-full bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700"
            >
              Log In to Continue
            </Button>
            <Button
                onClick={() => navigate('/')}
                variant="ghost"
                className="mt-4 text-gray-400 hover:text-white"
            >
                Return to Home
            </Button>
          </CardContent>
        </Card>
        <AuthModal
            isOpen={showAuthModal}
            onClose={() => setShowAuthModal(false)}
            onAuthSuccess={handleAuthSuccess}
        />
      </div>
    );
  }

  if (paymentStatus === 'error') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-gray-900 to-slate-800 flex items-center justify-center">
        <Card className="glass border-red-500/50 max-w-md w-full mx-4">
          <CardContent className="p-8 text-center">
            <div className="h-12 w-12 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-red-400 text-xl">⚠️</span>
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">Payment Error</h2>
            <p className="text-gray-400 mb-6">There was an issue processing your payment. Please try again or contact support.</p>
            <Button
              onClick={() => navigate('/')}
              className="bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700"
            >
              Return to Home
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (paymentStatus === 'success') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-gray-900 to-slate-800 flex items-center justify-center">
        <Card className={`glass ${getPlanColor(paymentData?.subscription_tier)} max-w-md w-full mx-4`}>
          <CardHeader className="text-center">
            <div className="flex justify-center mb-4">
              <div className="h-16 w-16 bg-green-500/20 rounded-full flex items-center justify-center">
                <CheckCircle className="h-8 w-8 text-green-400" />
              </div>
            </div>
            <CardTitle className="text-2xl text-white">Payment Successful!</CardTitle>
            <CardDescription className="text-gray-400">
              Your subscription has been activated
            </CardDescription>
          </CardHeader>
          
          <CardContent className="space-y-6">
            <div className="text-center">
              <div className="flex items-center justify-center space-x-2 mb-2">
                {paymentData?.subscription_tier && getPlanIcon(paymentData.subscription_tier)}
                <span className="text-xl font-semibold text-white capitalize">
                  {paymentData?.subscription_tier} Plan
                </span>
              </div>
              <p className="text-gray-400 text-sm">
                You now have access to advanced threat monitoring features!
              </p>
            </div>

            <div className="bg-gray-800/50 rounded-lg p-4 space-y-2">
              <h4 className="text-white font-semibold">What's included:</h4>
              <ul className="text-sm text-gray-300 space-y-1">
                {paymentData?.subscription_tier === 'pro' && (
                  <>
                    <li>• 50 Quick Scans per day</li>
                    <li>• 10 Continuous monitoring terms</li>
                    <li>• Email alerts & notifications</li>
                    <li>• Priority support</li>
                  </>
                )}
                {paymentData?.subscription_tier === 'enterprise' && (
                  <>
                    <li>• 200 Quick Scans per day</li>
                    <li>• 50 Continuous monitoring terms</li>
                    <li>• Email & SMS alerts</li>
                    <li>• API access & integrations</li>
                    <li>• 24/7 premium support</li>
                  </>
                )}
              </ul>
            </div>

            <div className="space-y-3">
              <Button
                onClick={() => {
                  if (user?.email) {
                    navigate(`/feed?email=${encodeURIComponent(user.email)}`);
                  } else {
                    navigate('/');
                  }
                }}
                className={`w-full font-semibold py-3 transition-all duration-300 ${
                  paymentData?.subscription_tier === 'enterprise'
                    ? 'bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-600 hover:to-indigo-700'
                    : 'bg-gradient-to-r from-orange-500 to-red-600 hover:from-orange-600 hover:to-red-700'
                } text-white`}
              >
                <div className="flex items-center space-x-2">
                  <span>Go to My Intelligence Feed</span>
                  <ArrowRight className="h-4 w-4" />
                </div>
              </Button>

              <Button
                onClick={() => navigate('/')}
                variant="outline"
                className="w-full border-gray-600 text-gray-300 hover:bg-gray-800"
              >
                Return to Home
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return null;
};

export default PaymentSuccess;
