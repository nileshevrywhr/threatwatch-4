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
import { useTheme } from './ThemeProvider';
import { ToggleGroup, ToggleGroupItem } from './ui/toggle-group';

const UserMenu = ({ user, onLogout, onShowSubscriptionPlans }) => {
  const { theme, setTheme } = useTheme();

  const getTierIcon = (tier) => {
    switch (tier) {
      case 'enterprise':
        return <Crown className="h-4 w-4 text-purple-600 dark:text-purple-400" />;
      case 'pro':
        return <Zap className="h-4 w-4 text-orange-600 dark:text-orange-400" />;
      default:
        return <Shield className="h-4 w-4 text-slate-600 dark:text-slate-400" />;
    }
  };

  const getTierColor = (tier) => {
    switch (tier) {
      case 'enterprise':
        return 'bg-purple-500/10 text-purple-700 dark:text-purple-300 border-purple-200 dark:border-purple-800';
      case 'pro':
        return 'bg-orange-500/10 text-orange-700 dark:text-orange-300 border-orange-200 dark:border-orange-800';
      default:
        return 'bg-slate-500/10 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-800';
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="flex items-center space-x-2 text-muted-foreground hover:text-foreground hover:bg-accent">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-full flex items-center justify-center">
              <User className="h-4 w-4 text-white" />
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
      
      <DropdownMenuContent className="w-64 bg-popover border-border" align="end">
        <DropdownMenuLabel className="text-foreground">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium">{user.full_name}</p>
            <p className="text-xs text-muted-foreground">{user.email}</p>
          </div>
        </DropdownMenuLabel>
        
        <DropdownMenuSeparator className="bg-border" />
        
        <div className="px-2 py-1">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Current Plan:</span>
            <Badge variant="outline" className={`text-xs ${getTierColor(user.subscription_tier)}`}>
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
        
        <DropdownMenuSeparator className="bg-border" />

        <div className="px-2 py-1.5 flex items-center justify-between">
          <span className="text-sm text-foreground flex items-center">
            <Sun className="mr-2 h-4 w-4 text-muted-foreground" /> Theme
          </span>
          <ToggleGroup
            type="single"
            value={theme}
            onValueChange={(value) => {
              if (value) setTheme(value);
            }}
            className="border rounded-md p-0.5 bg-muted"
          >
            <ToggleGroupItem value="system" className="h-7 w-7 p-0 rounded-sm data-[state=on]:bg-background data-[state=on]:shadow-sm" aria-label="System theme">
              <Monitor className="h-4 w-4" />
            </ToggleGroupItem>
            <ToggleGroupItem value="light" className="h-7 w-7 p-0 rounded-sm data-[state=on]:bg-background data-[state=on]:shadow-sm" aria-label="Light theme">
              <Sun className="h-4 w-4" />
            </ToggleGroupItem>
            <ToggleGroupItem value="dark" className="h-7 w-7 p-0 rounded-sm data-[state=on]:bg-background data-[state=on]:shadow-sm" aria-label="Dark theme">
              <Moon className="h-4 w-4" />
            </ToggleGroupItem>
          </ToggleGroup>
        </div>

        <DropdownMenuSeparator className="bg-border" />
        
        <DropdownMenuItem 
          onClick={onShowSubscriptionPlans}
          className="text-foreground hover:bg-accent cursor-pointer"
        >
          <CreditCard className="mr-2 h-4 w-4 text-muted-foreground" />
          <span>Manage Subscription</span>
        </DropdownMenuItem>
        
        <DropdownMenuItem className="text-foreground hover:bg-accent cursor-pointer">
          <Settings className="mr-2 h-4 w-4 text-muted-foreground" />
          <span>Settings</span>
        </DropdownMenuItem>
        
        <DropdownMenuSeparator className="bg-border" />
        
        <DropdownMenuItem 
          onClick={onLogout}
          className="text-destructive hover:bg-destructive/10 cursor-pointer"
        >
          <LogOut className="mr-2 h-4 w-4" />
          <span>Sign Out</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default UserMenu;
