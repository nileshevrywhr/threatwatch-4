import React from 'react';
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
import {
  User,
  Crown,
  Zap,
  Shield,
  Settings,
  LogOut,
  CreditCard,
  Sun,
  Moon,
  Monitor
} from 'lucide-react';
import { ToggleGroup, ToggleGroupItem } from './ui/toggle-group';
import { useTheme } from './ThemeProvider';

const UserMenu = ({ user, onLogout, onShowSubscriptionPlans }) => {
  const { theme, setTheme } = useTheme();

  const getTierIcon = (tier) => {
    switch (tier) {
      case 'enterprise':
        return <Crown className="h-4 w-4 text-purple-400" />;
      case 'pro':
        return <Zap className="h-4 w-4 text-orange-400" />;
      default:
        return <Shield className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getTierColor = (tier) => {
    switch (tier) {
      case 'enterprise':
        return 'bg-purple-500/10 text-purple-500 border-purple-500/20';
      case 'pro':
        return 'bg-orange-500/10 text-orange-500 border-orange-500/20';
      default:
        return 'bg-muted text-muted-foreground border-border';
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
      <Button
        variant="ghost"
        className="flex items-center space-x-2 text-muted-foreground hover:text-foreground hover:bg-accent"
        aria-label={`User menu for ${user.full_name}`}
      >
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-[#00FFB2] rounded-full flex items-center justify-center">
              <User className="h-4 w-4 text-black" />
            </div>
            <div className="hidden md:block text-left">
              <div className="text-sm font-medium text-foreground">{user.full_name}</div>
              <div className="flex items-center space-x-1">
                {getTierIcon(user.subscription_tier)}
                <span className="text-xs capitalize text-muted-foreground">{user.subscription_tier}</span>
              </div>
            </div>
          </div>
        </Button>
      </DropdownMenuTrigger>
      
      <DropdownMenuContent className="w-64 bg-card border-border" align="end">
        <DropdownMenuLabel>
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium">{user.full_name}</p>
            <p className="text-xs text-muted-foreground">{user.email}</p>
          </div>
        </DropdownMenuLabel>
        
        <DropdownMenuSeparator />
        
        <div className="px-2 py-1">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Current Plan:</span>
            <Badge className={`text-xs ${getTierColor(user.subscription_tier)}`}>
              <div className="flex items-center space-x-1">
                {getTierIcon(user.subscription_tier)}
                <span className="capitalize">{user.subscription_tier}</span>
              </div>
            </Badge>
          </div>
          
          {user.subscription_tier === 'free' && (
            <div className="mt-2 text-xs text-muted-foreground">
              {user.quick_scans_today || 0}/3 scans used today
            </div>
          )}
          
          {(user.subscription_tier === 'pro' || user.subscription_tier === 'enterprise') && (
            <div className="mt-2 space-y-1 text-xs text-muted-foreground">
              <div>Quick scans: {user.quick_scans_today || 0} used today</div>
              <div>Monitoring terms: {user.monitoring_terms_count || 0} active</div>
            </div>
          )}
        </div>
        
        <DropdownMenuSeparator />

        <div className="flex items-center justify-between px-2 py-1.5">
          <span className="text-sm font-medium">Theme</span>
          <ToggleGroup
            type="single"
            value={theme}
            onValueChange={(value) => {
              if (value) setTheme(value);
            }}
            className="border rounded-full p-0.5"
            size="sm"
          >
            <ToggleGroupItem value="system" className="rounded-full w-8 h-8 p-0" title="System">
              <Monitor className="h-4 w-4" />
            </ToggleGroupItem>
            <ToggleGroupItem value="light" className="rounded-full w-8 h-8 p-0" title="Light">
              <Sun className="h-4 w-4" />
            </ToggleGroupItem>
            <ToggleGroupItem value="dark" className="rounded-full w-8 h-8 p-0" title="Dark">
              <Moon className="h-4 w-4" />
            </ToggleGroupItem>
          </ToggleGroup>
        </div>

        <DropdownMenuSeparator />
        
        <DropdownMenuItem 
          onClick={onShowSubscriptionPlans}
          className="cursor-pointer"
        >
          <CreditCard className="mr-2 h-4 w-4" />
          <span>Manage Subscription</span>
        </DropdownMenuItem>
        
        <DropdownMenuItem className="cursor-pointer">
          <Settings className="mr-2 h-4 w-4" />
          <span>Settings</span>
        </DropdownMenuItem>
        
        <DropdownMenuSeparator />
        
        <DropdownMenuItem 
          onClick={onLogout}
          className="text-destructive hover:text-destructive cursor-pointer"
        >
          <LogOut className="mr-2 h-4 w-4" />
          <span>Sign Out</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default UserMenu;
