import React, { useState, Suspense, lazy } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from './ui/button';
import { Shield, Eye, Bell, LogIn, UserPlus } from 'lucide-react';
import UserMenu from './UserMenu';
import { useAuth } from './AuthProvider';

// Lazy load modals to reduce initial bundle size and improve TTI
const AuthModal = lazy(() => import('./AuthModal'));
const SubscriptionPlans = lazy(() => import('./SubscriptionPlans'));

const Header = ({ onAuthSuccess }) => {
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
            <header className="py-6 px-4 border-b border-gray-800">
                <div className="max-w-7xl mx-auto flex items-center justify-between">
                    <div
                        className="flex items-center space-x-2 cursor-pointer"
                        onClick={handleLogoClick}
                    >
                        <Shield className="h-8 w-8 text-cyan-400" />
                        <span className="text-2xl font-bold text-white font-mono">ThreatWatch</span>
                    </div>

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
                                onShowSubscriptionPlans={() => setShowSubscriptionPlans(true)}
                            />
                        ) : (
                            <div className="flex items-center space-x-3">
                                <Button
                                    onClick={() => setShowAuthModal(true)}
                                    variant="ghost"
                                    className="text-gray-300 hover:text-white hover:bg-gray-800"
                                >
                                    <LogIn className="h-4 w-4 mr-2" />
                                    Sign In
                                </Button>
                                <Button
                                    onClick={() => setShowAuthModal(true)}
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
            {/* ⚡ Performance: Suspense wrapper allows lazy loading */}
            <Suspense fallback={null}>
                <AuthModal
                    isOpen={showAuthModal}
                    onClose={() => setShowAuthModal(false)}
                    onAuthSuccess={handleAuthSuccess}
                />
            </Suspense>

            {/* Subscription Plans Modal */}
            {/* ⚡ Performance: Conditionally render to avoid fetching chunk until needed */}
            {showSubscriptionPlans && (
                <Suspense fallback={null}>
                    <SubscriptionPlans
                        isOpen={showSubscriptionPlans}
                        onClose={() => setShowSubscriptionPlans(false)}
                        currentUser={user}
                        authToken={session?.access_token}
                    />
                </Suspense>
            )}
        </>
    );
};

export default Header;
