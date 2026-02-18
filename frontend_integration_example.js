/**
 * Frontend Integration Example for Summarization API
 * Add this to your ApiService or SearchMode component
 */

// Add to ApiService.js
class ApiService {
  static BASE_URL = 'http://localhost:8000/api/v1';

  // Existing search method
  static async searchMemories(query, limit = 20) {
    const response = await fetch(
      `${this.BASE_URL}/search_memories?query=${encodeURIComponent(query)}&limit=${limit}`
    );
    return await response.json();
  }

  // NEW: Summarize search results
  static async summarizeSearch(searchResults) {
    const response = await fetch(`${this.BASE_URL}/summarize_search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(searchResults)
    });
    return await response.json();
  }

  // NEW: Summarize single memory
  static async summarizeMemory(memory) {
    const response = await fetch(`${this.BASE_URL}/summarize_memory`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(memory)
    });
    return await response.json();
  }
}

// Example usage in SearchMode.js
const SearchMode = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState([]);
  const [narrative, setNarrative] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    setLoading(true);
    try {
      // 1. Get search results
      const searchResults = await ApiService.searchMemories(searchQuery);
      setResults(searchResults.memories);

      // 2. Get narrative summary
      const summary = await ApiService.summarizeSearch(searchResults);
      setNarrative(summary);

      console.log('📖 Narrative:', summary.summary);
      // "I found 3 memories matching 'birthday' (2 images, 1 text memory):"

    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="search-mode">
      <input
        type="text"
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        placeholder="Search your memories..."
      />
      <button onClick={handleSearch}>Search</button>

      {loading && <div>Searching...</div>}

      {narrative && (
        <div className="narrative-summary">
          <h3>📖 {narrative.summary}</h3>
          
          {narrative.memory_summaries.map((mem, index) => (
            <div key={mem.memory_id} className="memory-narrative">
              <p>{mem.summary}</p>
              
              {mem.image_url && (
                <img 
                  src={`http://localhost:8000${mem.image_url}`}
                  alt="Memory"
                  className="memory-image"
                />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Example CSS for narrative display
const narrativeStyles = `
.narrative-summary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 24px;
  border-radius: 16px;
  margin: 20px 0;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

.narrative-summary h3 {
  font-size: 20px;
  margin-bottom: 20px;
  font-weight: 600;
}

.memory-narrative {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  padding: 16px;
  border-radius: 12px;
  margin: 12px 0;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.memory-narrative p {
  line-height: 1.6;
  margin-bottom: 12px;
  white-space: pre-line;
}

.memory-image {
  width: 100%;
  max-height: 300px;
  object-fit: cover;
  border-radius: 8px;
  margin-top: 12px;
}
`;

// Alternative: Simpler integration - just show narrative text
const SimpleSearchWithNarrative = () => {
  const [query, setQuery] = useState('');
  const [narrative, setNarrative] = useState('');

  const search = async () => {
    const results = await ApiService.searchMemories(query);
    const summary = await ApiService.summarizeSearch(results);

    let fullNarrative = summary.summary + '\n\n';
    summary.memory_summaries.forEach(mem => {
      fullNarrative += mem.summary + '\n\n';
    });
    
    setNarrative(fullNarrative);
  };

  return (
    <div>
      <input value={query} onChange={e => setQuery(e.target.value)} />
      <button onClick={search}>Search</button>
      
      {narrative && (
        <div className="narrative-box">
          <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>
            {narrative}
          </pre>
        </div>
      )}
    </div>
  );
};

export { ApiService, SearchMode, SimpleSearchWithNarrative };
