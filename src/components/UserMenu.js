import React, { useState, memo } from 'react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';
import { User, Crown, Zap, Shield, Settings, LogOut, CreditCard } from 'lucide-react';

const UserMenu = memo(({ user, onLogout, onShowSubscriptionPlans }) => {
  const getTierIcon = (tier) => {
    switch (tier) {
      case 'enterprise':
        return <Crown className="h-4 w-4 text-purple-400" />;
      case 'pro':
        return <Zap className="h-4 w-4 text-orange-400" />;
      default:
        return <Shield className="h-4 w-4 text-gray-400" />;
    }
  };

  const getTierColor = (tier) => {
    switch (tier) {
      case 'enterprise':
        return 'bg-purple-500/20 text-purple-300 border-purple-400';
      case 'pro':
        return 'bg-orange-500/20 text-orange-300 border-orange-400';
      default:
        return 'bg-gray-500/20 text-gray-300 border-gray-400';
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
      <Button
        variant="ghost"
        className="flex items-center space-x-2 text-gray-300 hover:text-white hover:bg-gray-800"
        aria-label={`User menu for ${user.full_name}`}
      >
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-full flex items-center justify-center">
              <User className="h-4 w-4 text-white" />
            </div>
            <div className="hidden md:block text-left">
              <div className="text-sm font-medium">{user.full_name}</div>
              <div className="flex items-center space-x-1">
                {getTierIcon(user.subscription_tier)}
                <span className="text-xs capitalize">{user.subscription_tier}</span>
              </div>
            </div>
          </div>
        </Button>
      </DropdownMenuTrigger>
      
      <DropdownMenuContent className="w-56 bg-gray-800 border-gray-700" align="end">
        <DropdownMenuLabel className="text-gray-300">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium text-white">{user.full_name}</p>
            <p className="text-xs text-gray-400">{user.email}</p>
          </div>
        </DropdownMenuLabel>
        
        <DropdownMenuSeparator className="bg-gray-700" />
        
        <div className="px-2 py-1">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-300">Current Plan:</span>
            <Badge className={`text-xs ${getTierColor(user.subscription_tier)}`}>
              <div className="flex items-center space-x-1">
                {getTierIcon(user.subscription_tier)}
                <span className="capitalize">{user.subscription_tier}</span>
              </div>
            </Badge>
          </div>
          
          {user.subscription_tier === 'free' && (
            <div className="mt-2 text-xs text-gray-400">
              {user.quick_scans_today || 0}/3 scans used today
            </div>
          )}
          
          {(user.subscription_tier === 'pro' || user.subscription_tier === 'enterprise') && (
            <div className="mt-2 space-y-1 text-xs text-gray-400">
              <div>Quick scans: {user.quick_scans_today || 0} used today</div>
              <div>Monitoring terms: {user.monitoring_terms_count || 0} active</div>
            </div>
          )}
        </div>
        
        <DropdownMenuSeparator className="bg-gray-700" />
        
        <DropdownMenuItem 
          onClick={onShowSubscriptionPlans}
          className="text-gray-300 hover:bg-gray-700 hover:text-white cursor-pointer"
        >
          <CreditCard className="mr-2 h-4 w-4" />
          <span>Manage Subscription</span>
        </DropdownMenuItem>
        
        <DropdownMenuItem className="text-gray-300 hover:bg-gray-700 hover:text-white cursor-pointer">
          <Settings className="mr-2 h-4 w-4" />
          <span>Settings</span>
        </DropdownMenuItem>
        
        <DropdownMenuSeparator className="bg-gray-700" />
        
        <DropdownMenuItem 
          onClick={onLogout}
          className="text-red-400 hover:bg-red-900/20 hover:text-red-300 cursor-pointer"
        >
          <LogOut className="mr-2 h-4 w-4" />
          <span>Sign Out</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
});

export default UserMenu;