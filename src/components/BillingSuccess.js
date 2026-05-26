import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { CheckCircle, Crown, Zap, ArrowRight, Loader2 } from 'lucide-react';
import { useAuth } from './AuthProvider';
import { getSubscription } from '../lib/api';

const BillingSuccess = () => {
  const [loading, setLoading] = useState(true);
  const [subscription, setSubscription] = useState(null);
  const navigate = useNavigate();
  const { user, loading: authLoading } = useAuth();

  useEffect(() => {
    if (authLoading) return;

    const fetchSubscription = async () => {
      try {
        const data = await getSubscription();
        setSubscription(data);
      } catch (error) {
        console.error('Failed to fetch subscription:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchSubscription();
  }, [authLoading]);

  const getPlanIcon = (tier) => {
    return tier === 'enterprise' ? <Crown className="h-8 w-8 text-purple-400" /> : <Zap className="h-8 w-8 text-orange-400" />;
  };

  const getPlanColor = (tier) => {
    return tier === 'enterprise' ? 'border-purple-500/50' : 'border-orange-500/50';
  };

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Card className="border-border max-w-md w-full mx-4">
          <CardContent className="p-8 text-center">
            <Loader2 className="h-12 w-12 text-[#00FFB2] mx-auto mb-4 animate-spin" />
            <h2 className="text-xl font-semibold mb-2">Verifying Subscription</h2>
            <p className="text-muted-foreground">Please wait while we confirm your details...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <Card className={`border-border ${getPlanColor(subscription?.plan)} max-w-md w-full mx-4`}>
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <div className="h-16 w-16 bg-green-500/20 rounded-full flex items-center justify-center">
              <CheckCircle className="h-8 w-8 text-green-500" />
            </div>
          </div>
          <CardTitle className="text-2xl">Upgrade Successful!</CardTitle>
          <CardDescription className="text-muted-foreground">
            Your subscription has been activated
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-6">
          <div className="text-center">
            <div className="flex items-center justify-center space-x-2 mb-2">
              {subscription?.plan && getPlanIcon(subscription.plan)}
              <span className="text-xl font-semibold capitalize">
                {subscription?.plan || 'Pro'} Plan
              </span>
            </div>
            <p className="text-muted-foreground text-sm">
              You now have access to advanced threat monitoring features!
            </p>
          </div>

          <div className="bg-muted rounded-lg p-4 space-y-2">
            <h4 className="font-semibold">What's included:</h4>
            <ul className="text-sm text-muted-foreground space-y-1">
              {subscription?.plan === 'enterprise' ? (
                <>
                  <li>• 200 Quick Scans per day</li>
                  <li>• 50 Continuous monitoring terms</li>
                  <li>• Email & SMS alerts</li>
                  <li>• API access & integrations</li>
                  <li>• 24/7 premium support</li>
                </>
              ) : (
                <>
                  <li>• 50 Quick Scans per day</li>
                  <li>• 10 Continuous monitoring terms</li>
                  <li>• Email alerts & notifications</li>
                  <li>• Priority support</li>
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
                  navigate('/feed');
                }
              }}
              className={`w-full font-semibold py-3 transition-all duration-300 ${
                subscription?.plan === 'enterprise'
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
              className="w-full"
            >
              Return to Home
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default BillingSuccess;
