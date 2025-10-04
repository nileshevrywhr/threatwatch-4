import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { CheckCircle, Crown, Zap, ArrowRight, Loader2 } from 'lucide-react';
import { secureLog } from '../utils/secureLogger';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PaymentSuccess = () => {
  const [searchParams] = useSearchParams();
  const [paymentStatus, setPaymentStatus] = useState('checking');
  const [paymentData, setPaymentData] = useState(null);
  const [user, setUser] = useState(null);
  const navigate = useNavigate();

  const sessionId = searchParams.get('session_id');

  useEffect(() => {
    const checkPaymentStatus = async () => {
      if (!sessionId) {
        setPaymentStatus('error');
        return;
      }

      try {
        const authToken = localStorage.getItem('authToken');
        if (!authToken) {
          navigate('/');
          return;
        }

        const response = await axios.get(`${API}/payments/status/${sessionId}`, {
          headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
          }
        });

        setPaymentData(response.data);
        setPaymentStatus(response.data.payment_status === 'paid' ? 'success' : 'pending');

        // Update user data in localStorage if payment successful
        if (response.data.payment_status === 'paid') {
          const userData = localStorage.getItem('user');
          if (userData) {
            const parsedUser = JSON.parse(userData);
            parsedUser.subscription_tier = response.data.subscription_tier;
            localStorage.setItem('user', JSON.stringify(parsedUser)); // User data already sanitized from auth
            setUser(parsedUser);
          }
        }

      } catch (error) {
        console.error('Payment status check failed:', error);
        setPaymentStatus('error');
      }
    };

    checkPaymentStatus();
  }, [sessionId, navigate]);

  const getPlanIcon = (tier) => {
    return tier === 'enterprise' ? <Crown className="h-8 w-8 text-purple-400" /> : <Zap className="h-8 w-8 text-orange-400" />;
  };

  const getPlanColor = (tier) => {
    return tier === 'enterprise' ? 'border-purple-400/50' : 'border-orange-400/50';
  };

  if (paymentStatus === 'checking') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-gray-900 to-slate-800 flex items-center justify-center">
        <Card className="glass border-gray-700 max-w-md w-full mx-4">
          <CardContent className="p-8 text-center">
            <Loader2 className="h-12 w-12 text-cyan-400 mx-auto mb-4 animate-spin" />
            <h2 className="text-xl font-semibold text-white mb-2">Processing Payment</h2>
            <p className="text-gray-400">Please wait while we confirm your payment...</p>
          </CardContent>
        </Card>
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
                  const userEmail = user?.email || localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user')).email : null;
                  if (userEmail) {
                    navigate(`/feed?email=${encodeURIComponent(userEmail)}`);
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