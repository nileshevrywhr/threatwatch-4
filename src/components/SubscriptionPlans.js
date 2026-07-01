import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { CheckCircle, Shield, Zap, Crown, ArrowRight, Loader2 } from 'lucide-react';
import axios from 'axios';
import { secureLog } from '../utils/secureLogger';
import { supabase } from '../lib/supabaseClient';
import { useAuth } from './AuthProvider';
import { cancelSubscription } from '../lib/billing';
import { useMemo, useCallback } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SubscriptionPlans = ({ isOpen, onClose, currentUser, authToken }) => {
  const [loading, setLoading] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const { subscriptionPlan, refreshSubscription } = useAuth();
  const currentTier = subscriptionPlan || currentUser?.user_metadata?.subscription_tier || 'free';

  useEffect(() => {
    if (isOpen) {
      refreshSubscription();
    }
  }, [isOpen, refreshSubscription]);

  const plans = useMemo(() => [
    {
      id: 'free',
      name: 'Free',
      price: '$0/mo',
      period: 'forever',
      description: 'Perfect for getting started with threat monitoring',
      icon: Shield,
      features: [
        '3 Quick Scans per day',
        'Basic threat intelligence',
        'View scan results',
        'Community support'
      ],
      limitations: [
        'No continuous monitoring',
        'Limited scan history',
        'No email alerts'
      ],
      buttonText: currentTier === 'free' ? 'Current Plan' : 'Downgrade to Free',
      disabled: currentTier === 'free',
      popular: false
    },
    {
      id: 'pro',
      name: 'Pro',
      price: '$9/mo',
      period: 'per month',
      description: 'Advanced monitoring for security professionals',
      icon: Zap,
      features: [
        '50 Quick Scans per day',
        '10 Continuous monitoring terms',
        'Email alerts & notifications',
        'Advanced threat intelligence',
        'Scan history & export',
        'Priority support'
      ],
      limitations: [],
      buttonText: currentTier === 'pro' ? 'Current Plan' : currentTier === 'enterprise' ? 'Downgrade to Pro' : 'Upgrade to Pro',
      disabled: currentTier === 'pro',
      popular: true
    },
    {
      id: 'enterprise',
      name: 'Enterprise',
      price: '$19/mo',
      period: 'per month',
      description: 'Complete threat monitoring for large organizations',
      icon: Crown,
      features: [
        '200 Quick Scans per day',
        '50 Continuous monitoring terms',
        'Email & SMS alerts',
        'Advanced threat intelligence',
        'API access & integrations',
        'Custom threat feeds',
        'Dedicated account manager',
        '24/7 premium support'
      ],
      limitations: [],
      buttonText: currentTier === 'enterprise' ? 'Current Plan' : 'Upgrade to Enterprise',
      disabled: currentTier === 'enterprise',
      popular: false
    }
  ], [currentTier]);

  const handleUpgrade = useCallback(async (planId) => {
    if (planId === currentTier) return;

    setLoading(true);
    setSelectedPlan(planId);

    try {
      if (planId === 'free') {
        await cancelSubscription();
        await refreshSubscription();
        setLoading(false);
        setSelectedPlan(null);
        alert('Subscription successfully cancelled. Your plan will be downgraded to Free at the end of the current billing cycle.');
        return;
      }

      const { data: { session } } = await supabase.auth.getSession();
      const token = session?.access_token;
      
      if (!token) {
        alert('Authentication session expired. Please sign in again.');
        setLoading(false);
        setSelectedPlan(null);
        return;
      }

      const response = await axios.post(
        `${API}/billing/create-checkout`,
        {
          plan: planId
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      // Redirect to Lemon Squeezy Checkout
      if (response.data && response.data.checkout_url) {
        window.location.href = response.data.checkout_url;
      } else {
        throw new Error('No checkout URL returned from server');
      }

    } catch (error) {
      secureLog.error('Checkout error:', error);
      const errorMessage = error.response?.data?.message || error.message || 'Failed to start checkout process. Please try again.';
      alert(errorMessage);
      setLoading(false);
      setSelectedPlan(null);
    }
  }, [currentTier, refreshSubscription, supabase.auth]);

  const getCurrentPlanInfo = () => {
    return plans.find(plan => plan.id === currentTier);
  };

  const currentPlan = getCurrentPlanInfo();

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-4xl bg-card border-border max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-3xl text-center">Choose Your Plan</DialogTitle>
          <DialogDescription className="text-center text-muted-foreground">
            Upgrade your threat monitoring capabilities with advanced features
          </DialogDescription>
        </DialogHeader>

        {/* Current Plan Status */}
        {currentPlan && (
          <div className="mb-6 p-4 bg-muted rounded-lg border border-border">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <currentPlan.icon className="h-6 w-6 text-[#00FFB2]" />
                <div>
                  <h4 className="font-semibold">Current Plan: {currentPlan.name}</h4>
                  <p className="text-sm text-muted-foreground">
                    {currentTier === 'free' ? 'Free forever' : `${currentPlan.price} ${currentPlan.period}`}
                  </p>
                </div>
              </div>
              <Badge className="bg-[#00FFB2]/10 text-[#00FFB2] border-[#00FFB2]/20">
                Active
              </Badge>
            </div>
          </div>
        )}

        <div className="grid gap-6 md:grid-cols-3">
          {plans.map((plan) => {
            const PlanIcon = plan.icon;
            const isCurrentPlan = currentTier === plan.id;

            return (
              <Card key={plan.id} className={`relative ${
                plan.popular ? 'border-orange-400' : 'border-border'
              } ${isCurrentPlan ? 'ring-2 ring-cyan-500' : ''}`}>
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                    <Badge className="bg-[#00FFB2] text-white">Most Popular</Badge>
                  </div>
                )}

                <CardHeader className="text-center">
                  <div className="flex justify-center mb-4">
                    <PlanIcon className={`h-12 w-12 ${
                      plan.id === 'free' ? 'text-muted-foreground' :
                      plan.id === 'pro' ? 'text-[#00FFB2]' : 'text-foreground'
                    }`} />
                  </div>
                  <CardTitle className="text-2xl">{plan.name}</CardTitle>
                  <CardDescription className="text-muted-foreground">{plan.description}</CardDescription>
                  <div className="text-center mt-4">
                    <span className="text-4xl font-bold">{plan.price}</span>
                    <span className="text-muted-foreground ml-2">{plan.period}</span>
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  <div>
                    <h4 className="font-semibold mb-3">Features included:</h4>
                    <ul className="space-y-2">
                      {plan.features.map((feature, index) => (
                        <li key={index} className="flex items-start space-x-2">
                          <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                          <span className="text-muted-foreground text-sm">{feature}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {plan.limitations.length > 0 && (
                    <div>
                      <h4 className="text-muted-foreground font-semibold mb-2 text-sm">Limitations:</h4>
                      <ul className="space-y-1">
                        {plan.limitations.map((limitation, index) => (
                          <li key={index} className="text-muted-foreground/60 text-xs">
                            • {limitation}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <Button
                    onClick={() => handleUpgrade(plan.id)}
                    disabled={plan.disabled || loading}
                    className={`w-full font-semibold py-3 transition-all duration-300 ${
                      isCurrentPlan
                        ? 'bg-muted text-muted-foreground cursor-not-allowed'
                        : plan.id === 'pro'
                        ? 'bg-gradient-to-r from-orange-500 to-red-600 hover:from-orange-600 hover:to-red-700 text-white border-0'
                        : plan.id === 'enterprise'
                        ? 'bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-600 hover:to-indigo-700 text-white border-0'
                        : 'bg-muted text-muted-foreground cursor-not-allowed'
                    }`}
                  >
                    {loading && selectedPlan === plan.id ? (
                      <div className="flex items-center space-x-2">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span>Processing...</span>
                      </div>
                    ) : isCurrentPlan ? (
                      'Current Plan'
                    ) : plan.id === 'free' ? (
                      'Free Forever'
                    ) : (
                      <div className="flex items-center space-x-2">
                        <span>{plan.buttonText}</span>
                        <ArrowRight className="h-4 w-4" />
                      </div>
                    )}
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>

        <div className="mt-6 text-center text-sm text-muted-foreground">
          <p>• All plans include secure threat intelligence monitoring</p>
          <p>• Cancel or change your plan anytime</p>
          <p>• 30-day money-back guarantee on paid plans</p>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default SubscriptionPlans;
