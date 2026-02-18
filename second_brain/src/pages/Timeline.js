import { Calendar, ChevronLeft, ChevronRight, Clock, FileText, Image as ImageIcon } from 'lucide-react';
import { useEffect, useState } from 'react';
import ApiService from '../services/api';

const Timeline = () => {
  const backendOrigin = 'http://localhost:8000';
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [memories, setMemories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedImage, setSelectedImage] = useState(null);

  useEffect(() => {
    loadMemories();
  }, []);

  const loadMemories = async () => {
    try {
      setLoading(true);
      const response = await ApiService.getTimelineSummary('weekly', 500);
      const groups = response.groups || [];
      const flattened = groups.flatMap(g => (g.memories || []).map(m => ({
        ...m,
        period: g.period,
        periodStart: g.start,
        periodEnd: g.end,
      })));
      setMemories(flattened);
      setError(null);
    } catch (err) {
      console.error('Failed to load memories:', err);
      setError('Failed to load memories. Please check if the backend is running.');
      // Fallback to sample data
      setMemories([
        {
          id: 1,
          raw_text: 'Just completed my first marathon in 4:30! The training paid off and I feel incredible.',
          timestamp: '2024-01-15T14:30:00Z',
          type: 'text',
          sentiment: { emotion: 'joy' },
          entities: [{ text: 'marathon', label: 'EVENT' }]
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const formatMemoryForTimeline = (memory) => {
    return {
      id: memory.id,
      date: memory.timestamp.split('T')[0],
      title: memory.raw_text.substring(0, 50) + (memory.raw_text.length > 50 ? '...' : ''),
      content: memory.raw_text,
      sentimentLabel: memory.sentiment?.emotion || 'neutral',
      type: memory.type,
      timestamp: memory.timestamp,
      entities: memory.entities || [],
      // Add image-specific data
      imagePath: memory.metadata?.image_path,
      filename: memory.metadata?.filename,
      imageUrl: memory.image_url,
      imageWidth: memory.metadata?.image_width,
      imageHeight: memory.metadata?.image_height
    };
  };

  const timelineData = memories.map(formatMemoryForTimeline);

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getTypeIcon = (type) => {
    if (type === 'image') return <ImageIcon size={14} />;
    return <FileText size={14} />;
  };

  const insightCounts = timelineData.reduce(
    (acc, m) => {
      acc.total += 1;
      if (m.type === 'image') acc.images += 1;
      else acc.text += 1;
      return acc;
    },
    { total: 0, text: 0, images: 0 }
  );

  const resolveImageSrc = (memory) => {
    const raw = memory?.imageUrl || (memory?.filename ? `/api/v1/images/${memory.filename}` : null);
    if (!raw) return null;
    if (typeof raw === 'string' && raw.startsWith('http')) return raw;
    if (typeof raw === 'string' && raw.startsWith('/')) return `${backendOrigin}${raw}`;
    return raw;
  };

  const shouldShowTitle = (memory) => {
    const content = (memory?.content || '').trim();
    const title = (memory?.title || '').trim();
    if (!content) return !!title;
    if (memory?.type === 'image') return true;
    if (content.length <= 70) return false;
    if (!title) return false;
    if (title === content) return false;
    return true;
  };

  return (
    <div className="timeline-page">
      <div className="timeline-container">
        <div className="timeline-header">
          <div className="timeline-title">
            <Clock size={24} />
            <h2>Memory Timeline</h2>
          </div>
          <div className="timeline-nav">
            <button className="nav-button">
              <ChevronLeft size={20} />
              <span>Earlier</span>
            </button>
            <button className="nav-button">
              <Calendar size={20} />
              <span>Today</span>
            </button>
            <button className="nav-button">
              <span>Later</span>
              <ChevronRight size={20} />
            </button>
          </div>
        </div>

        <div className="timeline-insights" aria-label="Timeline insights">
          <div className="insight-pill">
            <span className="insight-label">Total</span>
            <span className="insight-value">{insightCounts.total}</span>
          </div>
          <div className="insight-pill">
            <span className="insight-label">Text</span>
            <span className="insight-value">{insightCounts.text}</span>
          </div>
          <div className="insight-pill">
            <span className="insight-label">Images</span>
            <span className="insight-value">{insightCounts.images}</span>
          </div>
        </div>

        <div className="timeline-content">
          {loading && <div className="loading-message">Loading memories...</div>}
          {error && <div className="error-message">{error}</div>}
          {!loading && timelineData.length === 0 && (
            <div className="empty-message">No memories found. Start adding some memories in the chat!</div>
          )}
          {timelineData.map((memory, index) => {
            const showDate = index === 0 || timelineData[index - 1].date !== memory.date;
            return (
              <div key={memory.id} className="timeline-memory">
                <div className="timeline-rail" aria-hidden="true">
                  <span className="timeline-dot" />
                  <span className="timeline-line" />
                </div>
                <div className="timeline-memory-main">
                  {showDate && (
                    <div className="memory-date-section">
                      <div className="memory-date">{formatDate(memory.date)}</div>
                    </div>
                  )}

                  <div className="memory-card-timeline">
                    <div className="memory-header-timeline">
                      <div className="memory-meta">
                        <span className="memory-type-icon" aria-hidden="true">{getTypeIcon(memory.type)}</span>
                        <span className={`memory-type-chip type-${memory.type || 'text'}`}>
                          {(memory.type || 'text').toUpperCase()}
                        </span>
                        {(memory.sentimentLabel || 'neutral').toLowerCase() !== 'neutral' && (
                          <span className={`memory-sentiment-chip mood-${(memory.sentimentLabel || 'neutral').toLowerCase()}`}>
                            {(memory.sentimentLabel || 'neutral').toUpperCase()}
                          </span>
                        )}
                      </div>
                      <div className="memory-time">{formatTime(memory.timestamp)}</div>
                    </div>

                    <div className="memory-content-timeline">
                      {shouldShowTitle(memory) && (
                        <h3 className="memory-title-timeline">{memory.title}</h3>
                      )}

                      {/* Show image if it's an image memory */}
                      {memory.type === 'image' && (memory.imageUrl || memory.filename) ? (
                        <div className="timeline-image-container">
                          <img
                            src={resolveImageSrc(memory)}
                            alt={memory.content || 'Memory image'}
                            className="timeline-image"
                            onClick={() => setSelectedImage({
                              src: resolveImageSrc(memory),
                              alt: memory.content || 'Memory image',
                              caption: memory.content
                            })}
                            onError={(e) => {
                              e.target.style.display = 'none';
                              e.target.nextSibling.style.display = 'block';
                            }}
                          />
                          <div className="timeline-image-error" style={{ display: 'none' }}>
                            <ImageIcon size={48} />
                            <span>Image not available</span>
                          </div>
                          {memory.content && (
                            <div className="timeline-image-caption">
                              <p>{memory.content}</p>
                            </div>
                          )}
                        </div>
                      ) : (
                        <p className="memory-text">{memory.content}</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        <div className="timeline-footer">
          <p className="timeline-stats">Showing {timelineData.length} memories from this period</p>
        </div>

        {/* Image Modal */}
        {selectedImage && (
          <div className="image-modal-overlay" onClick={() => setSelectedImage(null)}>
            <div className="image-modal-content" onClick={(e) => e.stopPropagation()}>
              <button
                className="image-modal-close"
                onClick={() => setSelectedImage(null)}
              >
                ×
              </button>
              <img
                src={selectedImage.src}
                alt={selectedImage.alt}
                className="image-modal-img"
              />
              {selectedImage.caption && (
                <div className="image-modal-caption">
                  <p>{selectedImage.caption}</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Timeline;
