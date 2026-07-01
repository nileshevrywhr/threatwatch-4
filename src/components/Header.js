import React, { useState, memo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from './ui/button';
import { Eye, Bell, LogIn, UserPlus, PlusCircle, Loader2 } from 'lucide-react';
import Logo from './Logo';
import AuthModal from './AuthModal';
import { Suspense, lazy } from 'react';
const SubscriptionPlans = lazy(() => import('./SubscriptionPlans'));
import UserMenu from './UserMenu';
import { useAuth } from './AuthProvider';

const Header = memo(({ onAuthSuccess, onNewMonitorClick }) => {
    const navigate = useNavigate();
    const { user, session, signOut } = useAuth();

    const [showAuthModal, setShowAuthModal] = useState(false);
    const [showSubscriptionPlans, setShowSubscriptionPlans] = useState(false);

    const handleAuthSuccess = () => {
        setShowAuthModal(false);
        if (onAuthSuccess) {
            onAuthSuccess();
        } else {
            navigate('/feed');
        }
    };

    const handleLogout = async () => {
        await signOut();
        // Clear any session storage
        const quickScanKeys = Object.keys(sessionStorage).filter(key => key.startsWith('quickScanResult_'));
        quickScanKeys.forEach(key => sessionStorage.removeItem(key));
    };

    const handleLogoClick = () => {
        navigate('/');
    };

    return (
        <>
            <header className="py-6 px-4 border-b border-border bg-background">
                <div className="max-w-7xl mx-auto flex items-center justify-between">
                    <div
                        className="cursor-pointer"
                        onClick={handleLogoClick}
                    >
                        <Logo className="h-10" />
                    </div>

                    <div className="flex items-center space-x-6">
                        <div className="hidden md:flex items-center space-x-6 text-muted-foreground">
                            <div className="flex items-center space-x-2">
                                <Eye className="h-4 w-4" />
                                <span className="text-sm">Real-time Monitoring</span>
                            </div>
                            <div className="flex items-center space-x-2">
                                <Bell className="h-4 w-4" />
                                <span className="text-sm">Instant Alerts</span>
                            </div>
                        </div>

                        {/* Authentication Section */}
                        {user ? (
                            <div className="flex items-center space-x-3">
                                <Button
                                    onClick={() => navigate('/feed')}
                                    className="bg-[#00FFB2] hover:bg-[#00E6A0] text-black font-semibold"
                                >
                                    <Eye className="h-4 w-4 mr-2" />
                                    View Feed
                                </Button>
                                <UserMenu
                                    user={user}
                                    onLogout={handleLogout}
                                    onShowSubscriptionPlans={() => setShowSubscriptionPlans(true)}
                                />
                            </div>
                        ) : (
                            <div className="flex items-center space-x-3">
                                <Button
                                    onClick={() => setShowAuthModal(true)}
                                    variant="ghost"
                                >
                                    <LogIn className="h-4 w-4 mr-2" />
                                    Sign In
                                </Button>
                                <Button
                                    onClick={() => setShowAuthModal(true)}
                                    className="bg-[#00FFB2] hover:bg-[#00E6A0] text-black"
                                >
                                    <UserPlus className="h-4 w-4 mr-2" />
                                    Get Started
                                </Button>
                            </div>
                        )}
                    </div>
                </div>
            </header>

            {/* Authentication Modal */}
            <AuthModal
                isOpen={showAuthModal}
                onClose={() => setShowAuthModal(false)}
                onAuthSuccess={handleAuthSuccess}
            />

            {/* Subscription Plans Modal */}
            <Suspense fallback={null}>
                <SubscriptionPlans
                    isOpen={showSubscriptionPlans}
                    onClose={() => setShowSubscriptionPlans(false)}
                    currentUser={user}
                    authToken={session?.access_token}
                />
            </Suspense>
        </>
    );
});

Header.displayName = 'Header';

export default Header;
