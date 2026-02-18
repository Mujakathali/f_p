import React, { useState } from 'react';

const Search = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({
    dateRange: '',
    people: '',
    emotion: '',
    tags: ''
  });

  const searchResults = [
    {
      id: 1,
      title: "My happiest moment in 2024",
      content: "Completing my first marathon was an incredible achievement that filled me with joy and pride.",
      date: "September 8, 2024",
      emotion: "🏃‍♂️",
      type: "📝",
      tags: ["achievement", "fitness", "marathon"],
      people: ["Training partner"]
    },
    {
      id: 2,
      title: "Beach memories with loved ones",
      content: "Spent wonderful time at the beach building sandcastles and watching sunsets.",
      date: "September 10, 2024",
      emotion: "😊",
      type: "📷",
      tags: ["family", "vacation", "beach"],
      people: ["Mom", "Dad", "Sister"]
    }
  ];

  const handleSearch = (e) => {
    e.preventDefault();
    // Implement search logic here
    console.log('Searching for:', searchQuery, filters);
  };

  const handleFilterChange = (filterType, value) => {
    setFilters({
      ...filters,
      [filterType]: value
    });
  };

  return (
    <div className="search">
      <div className="page-header">
        <h1>Search & Retrieve</h1>
        <p>Find your memories using natural language</p>
      </div>

      <div className="search-container">
        <form onSubmit={handleSearch} className="search-form">
          <div className="search-input-container">
            <input
              type="text"
              className="search-input"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search your memories... e.g., 'My happiest moment in 2024'"
            />
            <button type="submit" className="search-btn">
              🔍 Search
            </button>
          </div>
        </form>

        <div className="filters">
          <div className="filter-group">
            <label>Date Range</label>
            <select 
              value={filters.dateRange} 
              onChange={(e) => handleFilterChange('dateRange', e.target.value)}
            >
              <option value="">All Time</option>
              <option value="today">Today</option>
              <option value="week">This Week</option>
              <option value="month">This Month</option>
              <option value="year">This Year</option>
            </select>
          </div>

          <div className="filter-group">
            <label>People</label>
            <input
              type="text"
              value={filters.people}
              onChange={(e) => handleFilterChange('people', e.target.value)}
              placeholder="Filter by people..."
            />
          </div>

          <div className="filter-group">
            <label>Emotion</label>
            <select 
              value={filters.emotion} 
              onChange={(e) => handleFilterChange('emotion', e.target.value)}
            >
              <option value="">All Emotions</option>
              <option value="😊">😊 Happy</option>
              <option value="😢">😢 Sad</option>
              <option value="😡">😡 Angry</option>
              <option value="😍">😍 Love</option>
              <option value="🤔">🤔 Thoughtful</option>
              <option value="🎉">🎉 Excited</option>
            </select>
          </div>

          <div className="filter-group">
            <label>Tags</label>
            <input
              type="text"
              value={filters.tags}
              onChange={(e) => handleFilterChange('tags', e.target.value)}
              placeholder="Filter by tags..."
            />
          </div>
        </div>
      </div>

      <div className="search-results">
        <div className="results-header">
          <h3>Search Results ({searchResults.length})</h3>
          <div className="sort-options">
            <select>
              <option value="relevance">Sort by Relevance</option>
              <option value="date">Sort by Date</option>
              <option value="emotion">Sort by Emotion</option>
            </select>
          </div>
        </div>

        <div className="memories-grid">
          {searchResults.map((memory) => (
            <div key={memory.id} className="memory-card search-result">
              <div className="memory-header">
                <span className="memory-emotion">{memory.emotion}</span>
                <span className="memory-type">{memory.type}</span>
              </div>
              <h3 className="memory-title">{memory.title}</h3>
              <p className="memory-content">{memory.content}</p>
              <p className="memory-date">{memory.date}</p>
              
              {memory.people.length > 0 && (
                <div className="memory-people">
                  <strong>People: </strong>
                  {memory.people.join(', ')}
                </div>
              )}

              <div className="tags">
                {memory.tags.map((tag, index) => (
                  <span key={index} className="tag">{tag}</span>
                ))}
              </div>

              <div className="memory-actions">
                <button className="btn-link">View Details</button>
                <button className="btn-link">Edit</button>
                <button className="btn-link">Share</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Search;
