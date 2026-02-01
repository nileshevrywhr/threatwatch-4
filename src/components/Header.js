import React, { useState, lazy, Suspense, memo, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Button } from './ui/button';
import { Shield, Eye, Bell, LogIn, UserPlus, Loader2 } from 'lucide-react';
import UserMenu from './UserMenu';
import { useAuth } from './AuthProvider';

// Optimization: Lazy load heavy components to reduce initial bundle size
const AuthModal = lazy(() => import('./AuthModal'));
const SubscriptionPlans = lazy(() => import('./SubscriptionPlans'));

const Header = memo(({ onAuthSuccess }) => {
    const navigate = useNavigate();
    const { user, session, signOut } = useAuth();

    const [showAuthModal, setShowAuthModal] = useState(false);
    const [showSubscriptionPlans, setShowSubscriptionPlans] = useState(false);

    const handleAuthSuccess = useCallback(() => {
        setShowAuthModal(false);
        if (onAuthSuccess) {
            onAuthSuccess();
        } else {
            navigate('/feed');
        }
    }, [onAuthSuccess, navigate]);

    const handleLogout = useCallback(async () => {
        await signOut();
        // Clear any session storage
        const quickScanKeys = Object.keys(sessionStorage).filter(key => key.startsWith('quickScanResult_'));
        quickScanKeys.forEach(key => sessionStorage.removeItem(key));
    }, [signOut]);

    const handleLogoClick = useCallback(() => {
        navigate('/');
    }, [navigate]);

    const handleAuthModalClose = useCallback(() => {
        setShowAuthModal(false);
    }, []);

    const handleShowAuthModal = useCallback(() => {
        setShowAuthModal(true);
    }, []);

    const handleShowSubscriptionPlans = useCallback(() => {
        setShowSubscriptionPlans(true);
    }, []);

    const handleSubscriptionPlansClose = useCallback(() => {
        setShowSubscriptionPlans(false);
    }, []);

    return (
        <>
            <header className="py-6 px-4 border-b border-gray-800">
                <div className="max-w-7xl mx-auto flex items-center justify-between">
                    <Link
                        to="/"
                        className="flex items-center space-x-2 focus-visible:ring-2 focus-visible:ring-cyan-400 rounded-lg p-1 -m-1 transition-colors hover:opacity-90"
                        aria-label="ThreatWatch Home"
                    >
                        <Shield className="h-8 w-8 text-cyan-400" />
                        <span className="text-2xl font-bold text-white font-mono">ThreatWatch</span>
                    </Link>

                    <div className="flex items-center space-x-6">
                        <div className="hidden md:flex items-center space-x-6 text-gray-300">
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
                            <UserMenu
                                user={user}
                                onLogout={handleLogout}
                                onShowSubscriptionPlans={handleShowSubscriptionPlans}
                            />
                        ) : (
                            <div className="flex items-center space-x-3">
                                <Button
                                    onClick={handleShowAuthModal}
                                    variant="ghost"
                                    className="text-gray-300 hover:text-white hover:bg-gray-800"
                                >
                                    <LogIn className="h-4 w-4 mr-2" />
                                    Sign In
                                </Button>
                                <Button
                                    onClick={handleShowAuthModal}
                                    className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white"
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
            <Suspense fallback={
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
                    <Loader2 className="h-10 w-10 animate-spin text-cyan-500" />
                </div>
            }>
                {showAuthModal && (
                    <AuthModal
                        isOpen={showAuthModal}
                        onClose={() => setShowAuthModal(false)}
                        onAuthSuccess={handleAuthSuccess}
                    />
                )}
            </Suspense>

            {/* Subscription Plans Modal */}
            <Suspense fallback={
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
                    <Loader2 className="h-10 w-10 animate-spin text-cyan-500" />
                </div>
            }>
                {showSubscriptionPlans && (
                    <SubscriptionPlans
                        isOpen={showSubscriptionPlans}
                        onClose={() => setShowSubscriptionPlans(false)}
                        currentUser={user}
                        authToken={session?.access_token}
                    />
                )}
            </Suspense>           
        </>
    );
});

export default Header;
