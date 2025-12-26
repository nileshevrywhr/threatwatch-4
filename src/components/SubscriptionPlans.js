import React, { useState } from 'react';
import axios from 'axios';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { CheckCircle, Zap, Crown, Shield, ArrowRight, Loader2 } from 'lucide-react';
import { secureLog } from '../utils/secureLogger';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SubscriptionPlans = ({ isOpen, onClose, currentUser, authToken }) => {
  const [loading, setLoading] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(null);

  const plans = [
    {
      id: 'free',
      name: 'Free',
      price: '$0',
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
      disabled: currentUser?.subscription_tier === 'free',
      popular: false
    },
    {
      id: 'pro',
      name: 'Pro',
      price: '$9',
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
      buttonText: currentUser?.subscription_tier === 'pro' ? 'Current Plan' : 'Upgrade to Pro',
      disabled: currentUser?.subscription_tier === 'pro',
      popular: true
    },
    {
      id: 'enterprise',
      name: 'Enterprise',
      price: '$29',
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
      buttonText: currentUser?.subscription_tier === 'enterprise' ? 'Current Plan' : 'Upgrade to Enterprise',
      disabled: currentUser?.subscription_tier === 'enterprise',
      popular: false
    }
  ];

  const handleUpgrade = async (planId) => {
    if (planId === 'free' || !authToken) return;

    setLoading(true);
    setSelectedPlan(planId);

    try {
      const currentUrl = window.location.origin;
      const successUrl = `${currentUrl}/payment-success?session_id={CHECKOUT_SESSION_ID}`;
      const cancelUrl = `${currentUrl}/`;

      const response = await axios.post(
        `${API}/payments/checkout`,
        {
          plan: planId,
          success_url: successUrl,
          cancel_url: cancelUrl
        },
        {
          headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
          }
        }
      );

      // Redirect to Stripe Checkout
      window.location.href = response.data.url;

    } catch (error) {
      secureLog.error('Checkout error:', error);
      alert('Failed to start checkout process. Please try again.');
      setLoading(false);
      setSelectedPlan(null);
    }
  };

  const getCurrentPlanInfo = () => {
    const currentTier = currentUser?.subscription_tier || 'free';
    return plans.find(plan => plan.id === currentTier);
  };

  const currentPlan = getCurrentPlanInfo();

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-4xl bg-gray-900 border-gray-700 max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-3xl text-white text-center">Choose Your Plan</DialogTitle>
          <DialogDescription className="text-gray-400 text-center">
            Upgrade your threat monitoring capabilities with advanced features
          </DialogDescription>
        </DialogHeader>

        {/* Current Plan Status */}
        {currentPlan && (
          <div className="mb-6 p-4 bg-gradient-to-r from-gray-800 to-gray-700 rounded-lg border border-gray-600">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <currentPlan.icon className="h-6 w-6 text-cyan-400" />
                <div>
                  <h4 className="text-white font-semibold">Current Plan: {currentPlan.name}</h4>
                  <p className="text-sm text-gray-400">
                    {currentUser?.subscription_tier === 'free' ? 'Free forever' : `${currentPlan.price} ${currentPlan.period}`}
                  </p>
                </div>
              </div>
              <Badge className="bg-cyan-500/20 text-cyan-300 border-cyan-400">
                Active
              </Badge>
            </div>
          </div>
        )}

        <div className="grid gap-6 md:grid-cols-3">
          {plans.map((plan) => {
            const PlanIcon = plan.icon;
            const isCurrentPlan = currentUser?.subscription_tier === plan.id;

            return (
              <Card key={plan.id} className={`relative glass ${
                plan.popular ? 'border-orange-400/50' : 'border-gray-700'
              } ${isCurrentPlan ? 'ring-2 ring-cyan-400' : ''}`}>
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                    <Badge className="bg-orange-500 text-white">Most Popular</Badge>
                  </div>
                )}

                <CardHeader className="text-center">
                  <div className="flex justify-center mb-4">
                    <PlanIcon className={`h-12 w-12 ${
                      plan.id === 'free' ? 'text-gray-400' :
                      plan.id === 'pro' ? 'text-orange-400' : 'text-purple-400'
                    }`} />
                  </div>
                  <CardTitle className="text-2xl text-white">{plan.name}</CardTitle>
                  <CardDescription className="text-gray-400">{plan.description}</CardDescription>
                  <div className="text-center mt-4">
                    <span className="text-4xl font-bold text-white">{plan.price}</span>
                    <span className="text-gray-400 ml-2">{plan.period}</span>
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  <div>
                    <h4 className="text-white font-semibold mb-3">Features included:</h4>
                    <ul className="space-y-2">
                      {plan.features.map((feature, index) => (
                        <li key={index} className="flex items-start space-x-2">
                          <CheckCircle className="h-4 w-4 text-green-400 mt-0.5 flex-shrink-0" />
                          <span className="text-gray-300 text-sm">{feature}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {plan.limitations.length > 0 && (
                    <div>
                      <h4 className="text-gray-400 font-semibold mb-2 text-sm">Limitations:</h4>
                      <ul className="space-y-1">
                        {plan.limitations.map((limitation, index) => (
                          <li key={index} className="text-gray-500 text-xs">
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
                        ? 'bg-gray-600 text-gray-300 cursor-not-allowed'
                        : plan.id === 'pro'
                        ? 'bg-gradient-to-r from-orange-500 to-red-600 hover:from-orange-600 hover:to-red-700 text-white'
                        : plan.id === 'enterprise'
                        ? 'bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-600 hover:to-indigo-700 text-white'
                        : 'bg-gray-700 text-gray-400 cursor-not-allowed'
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

        <div className="mt-6 text-center text-sm text-gray-500">
          <p>• All plans include secure threat intelligence monitoring</p>
          <p>• Cancel or change your plan anytime</p>
          <p>• 30-day money-back guarantee on paid plans</p>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default SubscriptionPlans;