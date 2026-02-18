import { Pause, Play, Search, Volume2, VolumeX } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import ApiService from '../services/api';
import MemoryCard from './MemoryCard';

const SearchMode = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [narrative, setNarrative] = useState(null);
  const [aiAnswer, setAiAnswer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [selectedType, setSelectedType] = useState('all');
  const [sortBy, setSortBy] = useState('relevance');
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const speechSynthesisRef = useRef(null);

  const typeLabel = {
    all: 'All',
    text: 'Text',
    image: 'Photo',
  };

  const selectedMemoryTypes = (() => {
    if (selectedType === 'text') return ['text'];
    if (selectedType === 'image') return ['image'];
    return ['text', 'image'];
  })();

  // Cleanup speech on unmount
  useEffect(() => {
    return () => {
      if (speechSynthesisRef.current) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setLoading(true);
    try {
      // 1. Get search results
      const retrievalSearchType = 'hybrid';
      const results = await ApiService.searchMemoriesWithOptions(searchQuery, {
        limit: 20,
        searchType: retrievalSearchType,
        memoryTypes: selectedMemoryTypes,
      });
      setSearchResults(results.memories || []);
      setHasSearched(true);

      // 2. Get AI answer from retrieved memories
      try {
        const answerRes = await ApiService.askMemoriesWithOptions(searchQuery, {
          limit: 8,
          searchType: retrievalSearchType,
          memoryTypes: selectedMemoryTypes,
        });
        setAiAnswer(answerRes.answer || null);
      } catch (err) {
        console.error('AI answer failed:', err);
        setAiAnswer(null);
      }

      // Skip Gemini summarization for now - just show search results
      setNarrative(null);
    } catch (error) {
      console.error('Search failed:', error);
      setSearchResults([]);
      setNarrative(null);
      setAiAnswer(null);
      setHasSearched(true);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
    setIsPaused(false);
    setSearchQuery('');
    setSearchResults([]);
    setNarrative(null);
    setAiAnswer(null);
    setHasSearched(false);
  };

  const filteredResults = (searchResults || []).filter(m => {
    const t = (m?.type || 'text');
    return selectedMemoryTypes.includes(t);
  });

  const displayResults = (() => {
    const arr = [...filteredResults];
    if (sortBy === 'date') {
      arr.sort((a, b) => {
        const ta = new Date(a?.timestamp || 0).getTime();
        const tb = new Date(b?.timestamp || 0).getTime();
        return tb - ta;
      });
      return arr;
    }
    return arr;
  })();

  const resultStats = (() => {
    const stats = { total: displayResults.length, text: 0, image: 0 };
    displayResults.forEach(m => {
      const t = (m?.type || 'text');
      if (stats[t] !== undefined) stats[t] += 1;
    });
    return stats;
  })();

  const handleQuickSearch = async (query) => {
    setSearchQuery(query);
    setLoading(true);
    try {
      // 1. Get search results
      const retrievalSearchType = 'hybrid';
      const results = await ApiService.searchMemoriesWithOptions(query, {
        limit: 20,
        searchType: retrievalSearchType,
        memoryTypes: selectedMemoryTypes,
      });
      setSearchResults(results.memories || []);
      setHasSearched(true);

      // 2. Get AI answer from retrieved memories
      try {
        const answerRes = await ApiService.askMemoriesWithOptions(query, {
          limit: 8,
          searchType: retrievalSearchType,
          memoryTypes: selectedMemoryTypes,
        });
        setAiAnswer(answerRes.answer || null);
      } catch (err) {
        console.error('AI answer failed:', err);
        setAiAnswer(null);
      }

      // Skip Gemini summarization for now - just show search results
      setNarrative(null);
    } catch (error) {
      console.error('Search failed:', error);
      setSearchResults([]);
      setNarrative(null);
      setAiAnswer(null);
      setHasSearched(true);
    } finally {
      setLoading(false);
    }
  };

  // Text-to-Speech Functions
  const speakResults = () => {
    if (!searchResults || searchResults.length === 0) return;

    // Stop any ongoing speech
    window.speechSynthesis.cancel();

    // Create text to speak
    let textToSpeak = `Found ${searchResults.length} memories. `;

    if (aiAnswer) {
      textToSpeak += `Answer: ${aiAnswer}. `;
    }

    // Add narrative summary if available
    if (narrative && narrative.summary) {
      textToSpeak += narrative.summary + ". ";
    }

    // Add individual memories
    searchResults.forEach((memory, index) => {
      textToSpeak += `Memory ${index + 1}: ${memory.raw_text || memory.processed_text}. `;
    });

    // Create speech utterance
    const utterance = new SpeechSynthesisUtterance(textToSpeak);
    utterance.rate = 0.9; // Slightly slower for clarity
    utterance.pitch = 1;
    utterance.volume = 1;

    // Event handlers
    utterance.onstart = () => {
      setIsSpeaking(true);
      setIsPaused(false);
    };

    utterance.onend = () => {
      setIsSpeaking(false);
      setIsPaused(false);
    };

    utterance.onerror = (event) => {
      console.error('Speech synthesis error:', event);
      setIsSpeaking(false);
      setIsPaused(false);
    };

    speechSynthesisRef.current = utterance;
    window.speechSynthesis.speak(utterance);
  };

  const stopSpeaking = () => {
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
    setIsPaused(false);
  };

  const pauseSpeaking = () => {
    if (isSpeaking && !isPaused) {
      window.speechSynthesis.pause();
      setIsPaused(true);
    }
  };

  const resumeSpeaking = () => {
    if (isSpeaking && isPaused) {
      window.speechSynthesis.resume();
      setIsPaused(false);
    }
  };

  return (
    <div className="search-mode-container">
      <form onSubmit={handleSearch} className="search-input-container">
        <input
          type="text"
          className="search-input"
          placeholder="Search your memories... (e.g., 'happy moments', 'meetings with Sarah', 'achievements')"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <button type="submit" className="search-button" disabled={loading}>
          <Search size={16} />
        </button>
      </form>

      <div className="search-toolbar">
        <div className="search-filters">
          {(['all', 'text', 'image']).map((t) => (
            <button
              key={t}
              type="button"
              className={`filter-chip ${selectedType === t ? 'active' : ''}`}
              onClick={() => setSelectedType(t)}
            >
              {typeLabel[t]}
            </button>
          ))}
        </div>
        <div className="search-actions">
          <select
            className="sort-select"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
          >
            <option value="relevance">Sort: Relevance</option>
            <option value="date">Sort: Newest</option>
          </select>
          <button type="button" className="clear-btn" onClick={handleClear}>
            Clear
          </button>
        </div>
      </div>

      <div className="quick-search-suggestions">
        <h4>Quick Searches:</h4>
        <div className="suggestion-buttons">
          <button onClick={() => handleQuickSearch('happy moments')} className="suggestion-btn">
            😊 Happy Moments
          </button>
          <button onClick={() => handleQuickSearch('achievements')} className="suggestion-btn">
            🏆 Achievements
          </button>
          <button onClick={() => handleQuickSearch('people I met')} className="suggestion-btn">
            👥 People
          </button>
          <button onClick={() => handleQuickSearch('work projects')} className="suggestion-btn">
            💼 Work
          </button>
          <button onClick={() => handleQuickSearch('travel experiences')} className="suggestion-btn">
            ✈️ Travel
          </button>
        </div>
      </div>

      {loading && (
        <div className="loading-results">
          <div className="loading-spinner"></div>
          <p>Searching through your memories...</p>
        </div>
      )}

      {hasSearched && !loading && (
        <div className="search-results">
          {displayResults.length > 0 ? (
            <>
              {aiAnswer && (
                <div className="narrative-summary">
                  <div className="narrative-header">
                    <span className="ai-badge">🤖 AI Answer</span>
                  </div>
                  <h3 className="narrative-intro">{aiAnswer}</h3>
                </div>
              )}

              {/* AI-Powered Narrative Summary */}
              {narrative && (
                <div className="narrative-summary">
                  <div className="narrative-header">
                    <span className="ai-badge">🤖 AI Summary</span>
                  </div>
                  <h3 className="narrative-intro">{narrative.summary}</h3>

                  <div className="narrative-memories">
                    {narrative.memory_summaries && narrative.memory_summaries.map((mem, index) => (
                      <div key={mem.memory_id} className="narrative-item">
                        <div className="narrative-number">{index + 1}</div>
                        <div className="narrative-content">
                          <p className="narrative-text">{mem.summary}</p>
                          {mem.image_url && (
                            <img
                              src={`http://localhost:8000${mem.image_url}`}
                              alt="Memory"
                              className="narrative-image"
                            />
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="search-results-header">
                <div className="results-info">
                  <Search size={16} />
                  <span>Found {displayResults.length} memories</span>
                </div>
                <div className="results-stats" aria-hidden="true">
                  <span className="stat-pill">Text {resultStats.text}</span>
                  <span className="stat-pill">Photo {resultStats.image}</span>
                </div>
                <div className="audio-controls">
                  {!isSpeaking ? (
                    <button
                      onClick={speakResults}
                      className="audio-btn speak-btn"
                      title="Listen to results (Text-to-Speech)"
                    >
                      <Volume2 size={18} />
                      <span>Listen to Results</span>
                    </button>
                  ) : (
                    <>
                      {!isPaused ? (
                        <button
                          onClick={pauseSpeaking}
                          className="audio-btn pause-btn"
                          title="Pause"
                        >
                          <Pause size={18} />
                          <span>Pause</span>
                        </button>
                      ) : (
                        <button
                          onClick={resumeSpeaking}
                          className="audio-btn resume-btn"
                          title="Resume"
                        >
                          <Play size={18} />
                          <span>Resume</span>
                        </button>
                      )}
                      <button
                        onClick={stopSpeaking}
                        className="audio-btn stop-btn"
                        title="Stop"
                      >
                        <VolumeX size={18} />
                        <span>Stop</span>
                      </button>
                    </>
                  )}
                </div>
              </div>
              <div className="memory-grid">
                {displayResults.map((memory) => (
                  <MemoryCard
                    key={memory.id}
                    memory={memory}
                    onClick={(mem) => console.log('Memory clicked:', mem)}
                  />
                ))}
              </div>
            </>
          ) : (
            <div className="no-results">
              <Search size={48} />
              <h3>No memories found</h3>
              <p>Try searching for something else or add more memories in Store mode!</p>
            </div>
          )}
        </div>
      )}

      {!hasSearched && !loading && (
        <div className="search-placeholder">
          <Search size={64} />
          <h3>Search Your Memories</h3>
          <p>Find specific moments, people, places, or emotions from your stored memories.</p>
          <div className="search-tips">
            <h4>Search Tips:</h4>
            <ul>
              <li>Use natural language: "happy moments with friends"</li>
              <li>Search by emotion: "sad", "excited", "proud"</li>
              <li>Find people: "conversations with Sarah"</li>
              <li>Look for events: "meetings", "achievements", "travels"</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default SearchMode;
