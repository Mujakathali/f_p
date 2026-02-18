import { Brain, Clock, Network, Shield, Sparkles, TrendingUp, Zap } from 'lucide-react';
import React from 'react';
import { useNavigate } from 'react-router-dom';

const Home = () => {
  const navigate = useNavigate();

  const handleGetStarted = () => {
    navigate('/chat');
  };

  return (
    <div className="home-container">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <div className="hero-icon">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none">
              <path d="M12 2C13.1 2 14 2.9 14 4C14 5.1 13.1 6 12 6C10.9 6 10 5.1 10 4C10 2.9 10.9 2 12 2ZM21 9V7L15 7.5V9C15 10.1 14.1 11 13 11S11 10.1 11 9V7.5L5 7V9C5 10.1 4.1 11 3 11S1 10.1 1 9V7C1 5.9 1.9 5 3 5L21 5C22.1 5 23 5.9 23 7V9C23 10.1 22.1 11 21 11S19 10.1 19 9ZM12 13C13.1 13 14 13.9 14 15V17C14 18.1 13.1 19 12 19S10 18.1 10 17V15C10 13.9 10.9 13 12 13ZM17 13C18.1 13 19 13.9 19 15V17C19 18.1 18.1 19 17 19S15 18.1 15 17V15C15 13.9 15.9 13 17 13ZM7 13C8.1 13 9 13.9 9 15V17C9 18.1 8.1 19 7 19S5 18.1 5 17V15C5 13.9 5.9 13 7 13Z" fill="url(#brainGradient)" />
              <defs>
                <linearGradient id="brainGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#667eea" />
                  <stop offset="100%" stopColor="#764ba2" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          <h1 className="hero-title">
            Welcome to <span className="highlight">Reflecto</span>
          </h1>
          <p className="hero-subtitle">
            Your intelligent personal memory management system that learns, organizes, and helps you recall your most important moments.
          </p>
          <button className="get-started-btn" onClick={handleGetStarted}>
            <Sparkles size={20} />
            Get Started
          </button>
        </div>
        <div className="hero-visual">
          <div className="floating-card card-1">
            <div className="card-icon">📝</div>
            <div className="card-text">Text Memories</div>
          </div>
          <div className="floating-card card-2">
            <div className="card-icon">📷</div>
            <div className="card-text">Photo Memories</div>
          </div>
          <div className="floating-card card-3">
            <div className="card-icon">🎤</div>
            <div className="card-text">Voice Notes</div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section">
        <div className="section-header">
          <h2>Powerful Features for Your Memory Journey</h2>
          <p>Discover how MemoryGraph AI transforms the way you capture, organize, and retrieve your memories.</p>
        </div>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">
              <Brain size={32} />
            </div>
            <h3>AI Intelligence</h3>
            <p>Advanced AI understands context and connections between your memories for smarter organization.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">
              <Clock size={32} />
            </div>
            <h3>Timeline View</h3>
            <p>Visualize your memories chronologically and discover patterns in your life journey.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">
              <Network size={32} />
            </div>
            <h3>Knowledge Graph</h3>
            <p>See how your memories connect through an interactive graph of relationships and themes.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">
              <TrendingUp size={32} />
            </div>
            <h3>Smart Insights</h3>
            <p>Get AI-generated insights about your patterns, growth, and meaningful connections across your memories.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">
              <Shield size={32} />
            </div>
            <h3>Privacy First</h3>
            <p>Your memories are encrypted and secure. We prioritize your privacy with end-to-end encryption.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">
              <Zap size={32} />
            </div>
            <h3>Lightning Fast</h3>
            <p>Instant search and retrieval across all your memories with natural language processing capabilities.</p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="cta-content">
          <h2>Ready to Build Your Second Brain?</h2>
          <p>Join thousands of users who have transformed how they store and recall their most precious memories.</p>
          <button className="cta-button" onClick={handleGetStarted}>
            <Brain size={20} />
            Start Your Memory Journey
          </button>
        </div>
      </section>
    </div>
  );
};

export default Home;
