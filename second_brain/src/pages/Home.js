import { Brain, Clock, Network, Shield, Sparkles, Zap } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import AuthService from '../services/auth';

const Home = () => {
  const navigate = useNavigate();

  const handleGetStarted = () => {
    // Check if user is already logged in
    if (AuthService.isAuthenticated()) {
      navigate('/chat');
    } else {
      navigate('/login');
    }
  };

  return (
    <div className="home-container home-v2">
      <section className="hero-section hero-v2">
        <div className="hero-bg" aria-hidden="true">
          <div className="hero-blob hero-blob-1" />
          <div className="hero-blob hero-blob-2" />
          <div className="hero-grid" />
        </div>

        <div className="hero-inner">
          <div className="hero-content">
            <div className="hero-kicker">
              <span className="kicker-pill kicker-pill-primary">
                <span className="kicker-accent" aria-hidden="true" />
                <Sparkles size={14} />
                <span className="kicker-text">RAG + Multimodal Memories</span>
              </span>
            </div>

            <h1 className="hero-title">
              Build a <span className="highlight">Second Brain</span> that remembers, connects, and answers.
            </h1>

            <p className="hero-subtitle">
              MemoryGraph AI turns your notes, photos, and voice into a searchable memory graph with emotionally-aware answers powered by retrieval.
            </p>

            <div className="hero-actions">
              <button className="get-started-btn" onClick={handleGetStarted}>
                <Zap size={18} />
                Get Started
              </button>

            </div>


          </div>

          <div className="hero-visual hero-visual-v2" aria-hidden="true">
            <div className="preview-card preview-main">
              <div className="preview-top">
                <div className="preview-dot" />
                <div className="preview-dot" />
                <div className="preview-dot" />
                <div className="preview-title">MemoryGraph AI</div>
              </div>
              <div className="preview-body">
                <div className="preview-row">
                  <div className="preview-icon">
                    <Brain size={18} />
                  </div>
                  <div className="preview-text">
                    <div className="preview-line strong" />
                    <div className="preview-line" />
                  </div>
                </div>
                <div className="preview-row">
                  <div className="preview-icon alt">
                    <Network size={18} />
                  </div>
                  <div className="preview-text">
                    <div className="preview-line strong" />
                    <div className="preview-line" />
                  </div>
                </div>
                <div className="preview-pill-row">
                  <span className="mini-pill">semantic search</span>
                  <span className="mini-pill">hybrid rank</span>
                  <span className="mini-pill">image recall</span>
                </div>
              </div>
            </div>

            <div className="floating-card card-1">
              <div className="floating-top">
                <div className="floating-icon gradient-1"><Brain size={18} /></div>
                <span className="floating-badge">capture</span>
              </div>
              <div className="floating-body">
                <div className="floating-title">Text Memories</div>
                <div className="floating-subtitle">Store moments in your own words</div>
              </div>
              <div className="floating-preview">
                <span className="preview-chip">entities</span>
                <span className="preview-chip">sentiment</span>
              </div>
            </div>

            <div className="floating-card card-2">
              <div className="floating-top">
                <div className="floating-icon gradient-2"><Network size={18} /></div>
                <span className="floating-badge">recall</span>
              </div>
              <div className="floating-body">
                <div className="floating-title">Photo Memories</div>
                <div className="floating-subtitle">Search images by meaning</div>
              </div>
              <div className="floating-preview">
                <span className="preview-chip">caption</span>
                <span className="preview-chip">OCR</span>
              </div>
            </div>

            <div className="floating-card card-3">
              <div className="floating-top">
                <div className="floating-icon gradient-3"><Clock size={18} /></div>
                <span className="floating-badge">ask</span>
              </div>
              <div className="floating-body">
                <div className="floating-title">Voice Notes</div>
                <div className="floating-subtitle">Transcribe and revisit later</div>
              </div>
              <div className="floating-preview">
                <span className="preview-chip">transcribe</span>
                <span className="preview-chip">timeline</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section">
        <div className="section-header">
          <h2>Why it stands out</h2>
          <p>A modern memory assistant that feels like a product, not a demo.</p>
        </div>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">
              <Brain size={32} />
            </div>
            <h3>Emotion-aware answers</h3>
            <p>Generates natural answers grounded in retrieved memories, with calm support only when the context is truly sad.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">
              <Clock size={32} />
            </div>
            <h3>Timeline View</h3>
            <p>Zoom through days and weeks to revisit what mattered, fast.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">
              <Network size={32} />
            </div>
            <h3>Knowledge Graph</h3>
            <p>Explore relationships between people, topics, and moments with a clean interactive graph.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">
              <Sparkles size={32} />
            </div>
            <h3>Smart Insights</h3>
            <p>Spot trends and recurring themes across your memories using semantic retrieval.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">
              <Shield size={32} />
            </div>
            <h3>Privacy First</h3>
            <p>Designed to keep your data under your control, with secure auth and careful API key handling.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">
              <Zap size={32} />
            </div>
            <h3>Lightning Fast</h3>
            <p>Hybrid retrieval and rank fusion to surface the best matches quickly.</p>
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
