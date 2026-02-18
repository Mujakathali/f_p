/**
 * API service for MemoryGraph Backend integration
 */

const API_BASE_URL = 'http://localhost:8000/api/v1';

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  /**
   * Get authentication token from localStorage
   */
  getAuthToken() {
    return localStorage.getItem('access_token');
  }

  /**
   * Get authorization headers
   */
  getAuthHeaders() {
    const token = this.getAuthToken();
    if (token) {
      return {
        'Authorization': `Bearer ${token}`
      };
    }
    return {};
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...this.getAuthHeaders(),
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        if (response.status === 401) {
          // Unauthorized - redirect to login
          console.error('❌ Authentication required - redirecting to login');
          console.error('Token present:', !!this.getAuthToken());
          window.location.href = '/login';
          throw new Error('Authentication required');
        }

        // Try to get error details from response
        let errorMessage = `HTTP error! status: ${response.status}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch (e) {
          // Response is not JSON
        }

        console.error('❌ API Error:', errorMessage);
        throw new Error(errorMessage);
      }

      return await response.json();
    } catch (error) {
      console.error('❌ API request failed:', error);
      throw error;
    }
  }

  // Memory operations
  async addMemory(text, metadata = {}) {
    return this.request('/add_memory', {
      method: 'POST',
      body: JSON.stringify({ text, metadata }),
    });
  }

  async addVoiceMemory(audioFile, metadata = {}) {
    const formData = new FormData();
    formData.append('audio_file', audioFile);
    formData.append('metadata', JSON.stringify(metadata));

    const url = `${this.baseURL}/add_voice_memory`;
    const token = this.getAuthToken();

    const headers = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: headers,
        body: formData,
      });

      if (!response.ok) {
        if (response.status === 401) {
          console.error('Authentication required');
          window.location.href = '/login';
          throw new Error('Authentication required');
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  async addImageMemory(imageFile, caption = '', metadata = {}) {
    const formData = new FormData();
    formData.append('image_file', imageFile);
    formData.append('caption', caption);
    formData.append('metadata', JSON.stringify(metadata));

    const url = `${this.baseURL}/add_image_memory`;
    const token = this.getAuthToken();

    const headers = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: headers,
        body: formData,
      });

      if (!response.ok) {
        if (response.status === 401) {
          console.error('Authentication required');
          window.location.href = '/login';
          throw new Error('Authentication required');
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  async uploadImage(imageFile, metadata = {}) {
    // Alias for addImageMemory for consistency
    return this.addImageMemory(imageFile, '', metadata);
  }

  async listMemories(limit = 50, offset = 0) {
    return this.request(`/list_memories?limit=${limit}&offset=${offset}`);
  }

  async searchMemories(query, limit = 20) {
    return this.searchMemoriesWithOptions(query, { limit });
  }

  async searchMemoriesWithOptions(query, options = {}) {
    const {
      limit = 20,
      searchType,
      memoryType,
      memoryTypes,
    } = options;

    const params = new URLSearchParams();
    params.set('query', query);
    params.set('limit', String(limit));
    if (searchType) params.set('search_type', searchType);
    if (memoryType) params.set('memory_type', memoryType);
    if (Array.isArray(memoryTypes) && memoryTypes.length) {
      params.set('memory_types', memoryTypes.join(','));
    }

    return this.request(`/search_memories?${params.toString()}`);
  }

  async askMemories(question, limit = 8, searchType = 'hybrid') {
    return this.askMemoriesWithOptions(question, { limit, searchType });
  }

  async askMemoriesWithOptions(question, options = {}) {
    const {
      limit = 8,
      searchType = 'hybrid',
      memoryType,
      memoryTypes,
    } = options;

    return this.request('/ask', {
      method: 'POST',
      body: JSON.stringify({
        question,
        limit,
        search_type: searchType,
        ...(memoryType ? { memory_type: memoryType } : {}),
        ...(Array.isArray(memoryTypes) && memoryTypes.length ? { memory_types: memoryTypes } : {}),
      }),
    });
  }

  async getMemory(memoryId) {
    return this.request(`/memory/${memoryId}`);
  }

  async getSimilarMemories(memoryId, limit = 10) {
    return this.request(`/similar_memories/${memoryId}?limit=${limit}`);
  }

  async deleteMemory(memoryId) {
    return this.request(`/delete_memory/${memoryId}`, {
      method: 'DELETE',
    });
  }

  async getMemoryStats() {
    return this.request('/memory_stats');
  }

  // Graph operations
  async getGraph(limit = 100) {
    return this.request(`/get_graph?limit=${limit}`);
  }

  async queryGraph(query) {
    return this.request('/query_graph', {
      method: 'POST',
      body: JSON.stringify({ query }),
    });
  }

  async getEntityNetwork(entityName, depth = 2) {
    return this.request(`/entity_network/${encodeURIComponent(entityName)}?depth=${depth}`);
  }

  async createRelationship(fromEntity, toEntity, relationshipType, properties = {}) {
    return this.request('/create_relationship', {
      method: 'POST',
      body: JSON.stringify({
        from_entity: fromEntity,
        to_entity: toEntity,
        relationship_type: relationshipType,
        properties,
      }),
    });
  }

  async getTimelineGraph(startDate = null, endDate = null) {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const queryString = params.toString();
    return this.request(`/timeline_graph${queryString ? '?' + queryString : ''}`);
  }

  async getTimelineSummary(timeframe = 'weekly', limit = 500) {
    return this.request(`/timeline_summary?timeframe=${encodeURIComponent(timeframe)}&limit=${limit}`);
  }

  // Summarization operations
  async summarizeSearch(searchResults) {
    return this.request('/summarize_search', {
      method: 'POST',
      body: JSON.stringify(searchResults),
    });
  }

  async summarizeMemory(memory) {
    return this.request('/summarize_memory', {
      method: 'POST',
      body: JSON.stringify(memory),
    });
  }

  // Health check
  async healthCheck() {
    return this.request('/health', { method: 'GET' });
  }
}

export default new ApiService();
