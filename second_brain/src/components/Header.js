import { Clock, Home, LogIn, LogOut as LogOutIcon, Menu, MessageCircle, Moon, Network, Sun, X } from 'lucide-react';
import UserProfile from './UserProfile';
import { toast } from 'react-toastify';
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import AuthService from '../services/auth';

const Header = ({ currentView, setCurrentView, onClearChat }) => {
  const { isDarkMode, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Check authentication status
    const checkAuth = () => {
      const authenticated = AuthService.isAuthenticated();
      setIsAuthenticated(authenticated);
      if (authenticated) {
        setUser(AuthService.getUser());
      }
    };
    
    checkAuth();
    // Check on every route change
    window.addEventListener('storage', checkAuth);
    return () => window.removeEventListener('storage', checkAuth);
  }, [currentView]);

  const handleNavigation = (path, view) => {
    navigate(path);
    setCurrentView(view);
    setIsMobileMenuOpen(false);
  };

  const handleLogout = () => {
    AuthService.logout();
    setIsAuthenticated(false);
    setUser(null);
    
    // Clear chat messages when logging out
    if (onClearChat) {
      onClearChat();
    }
    
    navigate('/');
    setIsMobileMenuOpen(false);
    toast.success('Successfully logged out!');
  };

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  return (
    <header className="header">
      <div className="header-content">
        <div className="logo-section">
          <div className="logo" onClick={() => handleNavigation('/', 'home')} style={{ cursor: 'pointer' }}>
            <span className="logo-icon">🧠</span>
          </div>
          <h1 className="app-title desktop-title" onClick={() => handleNavigation('/', 'home')} style={{ cursor: 'pointer' }}>
            Reflecto
          </h1>
        </div>

        {/* Desktop Navigation */}
        <nav className="nav-buttons desktop-nav">
          {/* Always show Home */}
          <button
            className={`nav-btn ${currentView === 'home' ? 'active' : ''}`}
            onClick={() => handleNavigation('/', 'home')}
          >
            <Home size={18} />
            <span>Home</span>
          </button>

          {/* Show these only when authenticated */}
          {isAuthenticated && (
            <>
              <button
                className={`nav-btn ${currentView === 'chat' ? 'active' : ''}`}
                onClick={() => handleNavigation('/chat', 'chat')}
              >
                <MessageCircle size={18} />
                <span>Chat</span>
              </button>
              <button
                className={`nav-btn ${currentView === 'timeline' ? 'active' : ''}`}
                onClick={() => handleNavigation('/timeline', 'timeline')}
              >
                <Clock size={18} />
                <span>Timeline</span>
              </button>
              <button
                className={`nav-btn ${currentView === 'graph' ? 'active' : ''}`}
                onClick={() => handleNavigation('/graph', 'graph')}
              >
                <Network size={18} />
                <span>Graph</span>
              </button>
            </>
          )}

{/* User profile and login button */}
          {isAuthenticated && user ? (
            <div className="user-profile-container">
              <UserProfile user={user} onLogout={handleLogout} />
            </div>
          ) : (
            <button
              className="nav-btn login-btn"
              onClick={() => handleNavigation('/login', 'login')}
            >
              <LogIn size={18} />
              <span>Login</span>
            </button>
          )}

          <button
            className="theme-toggle"
            onClick={toggleTheme}
            title={isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          >
            {isDarkMode ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </nav>

        {/* Mobile Navigation */}
        <div className="mobile-nav">
          <button
            className="theme-toggle mobile-theme-toggle"
            onClick={toggleTheme}
            title={isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          >
            {isDarkMode ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <button
            className="hamburger-btn"
            onClick={toggleMobileMenu}
            aria-label="Toggle menu"
          >
            {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div className="mobile-menu-overlay" onClick={toggleMobileMenu}>
          <nav className="mobile-menu" onClick={(e) => e.stopPropagation()}>
            <button
              className={`mobile-nav-btn ${currentView === 'home' ? 'active' : ''}`}
              onClick={() => handleNavigation('/', 'home')}
            >
              <Home size={20} />
              <span>Home</span>
            </button>

            {/* Show these only when authenticated */}
            {isAuthenticated && (
              <>
                <button
                  className={`mobile-nav-btn ${currentView === 'chat' ? 'active' : ''}`}
                  onClick={() => handleNavigation('/chat', 'chat')}
                >
                  <MessageCircle size={20} />
                  <span>Chat</span>
                </button>
                <button
                  className={`mobile-nav-btn ${currentView === 'timeline' ? 'active' : ''}`}
                  onClick={() => handleNavigation('/timeline', 'timeline')}
                >
                  <Clock size={20} />
                  <span>Timeline</span>
                </button>
                <button
                  className={`mobile-nav-btn ${currentView === 'graph' ? 'active' : ''}`}
                  onClick={() => handleNavigation('/graph', 'graph')}
                >
                  <Network size={20} />
                  <span>Graph</span>
                </button>
              </>
            )}

            {/* Mobile Auth buttons */}
            {isAuthenticated ? (
              <div className="mobile-user-profile">
                <div className="mobile-user-info">
                  <span>Logged in as: <strong>{user?.username}</strong></span>
                </div>
                <button
                  className="mobile-nav-btn logout-btn"
                  onClick={handleLogout}
                >
                  <LogOutIcon size={20} />
                  <span>Logout</span>
                </button>
              </div>
            ) : (
              <button
                className="mobile-nav-btn login-btn"
                onClick={() => handleNavigation('/login', 'login')}
              >
                <LogIn size={20} />
                <span>Login</span>
              </button>
            )}
          </nav>
        </div>
      )}
    </header>
  );
};

export default Header;
