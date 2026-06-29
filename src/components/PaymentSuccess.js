import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { CheckCircle, ArrowRight, Mail } from 'lucide-react';
import { useAuth } from './AuthProvider';

const PaymentSuccess = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <Card className="border-green-500/50 max-w-md w-full mx-4">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <div className="h-16 w-16 bg-green-500/20 rounded-full flex items-center justify-center">
              <CheckCircle className="h-8 w-8 text-green-500" />
            </div>
          </div>
          <CardTitle className="text-2xl">Payment Received!</CardTitle>
          <CardDescription className="text-muted-foreground">
            Your subscription is being activated
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-6">
          <div className="bg-muted rounded-lg p-4 text-center space-y-2">
            <Mail className="h-6 w-6 text-[#00FFB2] mx-auto" />
            <p className="text-sm text-muted-foreground">
              We're processing your payment. You'll receive an email confirmation shortly.
              Your subscription will be active within a few minutes.
            </p>
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
              className="w-full bg-gradient-to-r from-orange-500 to-red-600 hover:from-orange-600 hover:to-red-700 text-white font-semibold py-3 transition-all duration-300"
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

export default PaymentSuccess;