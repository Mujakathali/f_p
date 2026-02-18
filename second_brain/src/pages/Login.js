import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Brain, Mail, Lock, Eye, EyeOff, CheckCircle } from 'lucide-react';
import AuthService from '../services/auth';
import { toast } from 'react-toastify';

const Login = () => {
  const [emailOrUsername, setEmailOrUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const userData = await AuthService.login(emailOrUsername, password);
      // Show success message with high visibility
      toast.success(
        `🎉 Welcome back, ${userData.user.username}! You have successfully logged in.`,
        {
          position: "top-center",
          autoClose: 4000,
          hideProgressBar: false,
          closeButton: true,
          closeOnClick: true,
          pauseOnHover: true,
          draggable: true,
          style: {
            background: '#10b981',
            color: 'white',
            fontSize: '16px',
            fontWeight: '600',
            padding: '16px 24px',
            borderRadius: '12px',
            boxShadow: '0 10px 40px rgba(16, 185, 129, 0.4)',
            minWidth: '400px',
            textAlign: 'center'
          },
          progressStyle: {
            background: 'rgba(255, 255, 255, 0.8)'
          }
        }
      );
      
      // Redirect to chat after a short delay to show the success message
      setTimeout(() => {
        navigate('/chat');
      }, 1000);
    } catch (err) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-card">
          <div className="auth-header">
            <div className="auth-logo">
              <Brain size={48} />
            </div>
            <h1 className="auth-title">Welcome Back to MemoryGraph AI</h1>
            <p className="auth-subtitle">Sign in to access your personal memory management system</p>
          </div>

          <form className="auth-form" onSubmit={handleLogin}>
            {error && (
              <div className="error-message" style={{
                padding: '12px',
                marginBottom: '16px',
                backgroundColor: '#fee',
                color: '#c33',
                borderRadius: '8px',
                fontSize: '14px'
              }}>
                {error}
              </div>
            )}

            <div className="input-group">
              <div className="input-icon">
                <Mail size={20} />
              </div>
              <input
                type="text"
                placeholder="Email or Username"
                value={emailOrUsername}
                onChange={(e) => setEmailOrUsername(e.target.value)}
                className="auth-input"
                required
              />
            </div>

            <div className="input-group">
              <div className="input-icon">
                <Lock size={20} />
              </div>
              <input
                type={showPassword ? "text" : "password"}
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="auth-input"
                required
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>

            <button type="submit" className="auth-btn primary" disabled={loading}>
              {loading ? 'Signing In...' : 'Sign In to MemoryGraph AI'}
            </button>

            <div className="auth-link">
              <span>Don't have an account? </span>
              <Link to="/signup" className="link-text">Create Account</Link>
            </div>

            <div className="divider">
              <span>OR</span>
            </div>

            <div className="social-login">
              <button type="button" className="social-btn google-btn">
                <div className="social-icon">
                  <svg width="18" height="18" viewBox="0 0 18 18">
                    <path fill="#4285F4" d="M16.51 8H8.98v3h4.3c-.18 1-.74 1.48-1.6 2.04v2.01h2.6a7.8 7.8 0 0 0 2.38-5.88c0-.57-.05-.66-.15-1.18z"/>
                    <path fill="#34A853" d="M8.98 16c2.16 0 3.97-.72 5.3-1.94l-2.6-2.04a4.8 4.8 0 0 1-7.18-2.53H1.83v2.07A8 8 0 0 0 8.98 16z"/>
                    <path fill="#FBBC05" d="M4.5 9.49a4.8 4.8 0 0 1 0-3.07V4.35H1.83a8 8 0 0 0 0 7.22l2.67-2.08z"/>
                    <path fill="#EA4335" d="M8.98 3.2c1.17 0 2.23.4 3.06 1.2l2.3-2.3A8 8 0 0 0 1.83 4.35L4.5 6.42a4.8 4.8 0 0 1 4.48-3.22z"/>
                  </svg>
                </div>
                <span>Continue with Google</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;
