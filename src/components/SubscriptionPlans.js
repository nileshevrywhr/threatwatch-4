import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { CheckCircle, Zap, Crown, Shield, ArrowRight, Loader2 } from 'lucide-react';
import { secureLog } from '../utils/secureLogger';
import { createCheckout, getSubscription } from '../lib/api';

const SubscriptionPlans = ({ isOpen, onClose, currentUser, authToken }) => {
  const [loading, setLoading] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [subscription, setSubscription] = useState(null);
  const [fetchingSubscription, setFetchingSubscription] = useState(false);

  useEffect(() => {
    if (isOpen && authToken) {
      const fetchSubscription = async () => {
        setFetchingSubscription(true);
        try {
          const data = await getSubscription();
          setSubscription(data);
        } catch (error) {
          secureLog.error('Failed to fetch subscription:', error);
        } finally {
          setFetchingSubscription(false);
        }
      };
      fetchSubscription();
    }
  }, [isOpen, authToken]);

  const plans = [
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
      buttonText: 'Current Plan',
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
      popular: true
    },
    {
      id: 'enterprise',
      name: 'Enterprise',
      price: '$29/mo',
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
      popular: false
    }
  ];

  const currentPlanId = subscription?.plan || currentUser?.subscription_tier || 'free';

  const handleUpgrade = async (planId) => {
    if (planId === 'free' || !authToken) return;

    setLoading(true);
    setSelectedPlan(planId);

    try {
      const response = await createCheckout(planId);
      // Redirect to Lemon Squeezy Checkout
      if (response.url) {
        window.location.href = response.url;
      } else {
        throw new Error('No checkout URL returned');
      }
    } catch (error) {
      secureLog.error('Checkout error:', error);
      alert('Failed to start checkout process. Please try again.');
      setLoading(false);
      setSelectedPlan(null);
    }
  };

  const currentPlanInfo = plans.find(plan => plan.id === currentPlanId);

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
        <div className="mb-6 p-4 bg-muted rounded-lg border border-border">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {currentPlanInfo ? (
                <currentPlanInfo.icon className="h-6 w-6 text-[#00FFB2]" />
              ) : (
                <Shield className="h-6 w-6 text-[#00FFB2]" />
              )}
              <div>
                <h4 className="font-semibold">
                  {fetchingSubscription ? 'Loading subscription...' : `Current Plan: ${currentPlanInfo?.name || 'Free'}`}
                </h4>
                <p className="text-sm text-muted-foreground capitalize">
                  Status: {subscription?.status || 'active'}
                </p>
              </div>
            </div>
            <Badge className="bg-[#00FFB2]/10 text-[#00FFB2] border-[#00FFB2]/20">
              Active
            </Badge>
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {plans.map((plan) => {
            const PlanIcon = plan.icon;
            const isCurrentPlan = currentPlanId === plan.id;

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

                  {plan.limitations?.length > 0 && (
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
                    disabled={isCurrentPlan || loading || plan.id === 'free'}
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
                        <span>Upgrade to {plan.name}</span>
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
