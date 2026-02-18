import React from 'react';
import { Calendar, User, MapPin, Heart } from 'lucide-react';

const MemoryCard = ({ memory, onClick }) => {
  const formatDate = (timestamp) => {
    return new Date(timestamp).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getEmotionIcon = (emotion) => {
    const emotionMap = {
      'joy': '😊',
      'happiness': '😊',
      'sadness': '😢',
      'anger': '😠',
      'fear': '😨',
      'surprise': '😲',
      'neutral': '😐',
      'positive': '😊',
      'negative': '😢'
    };
    return emotionMap[emotion] || '📝';
  };

  const getEntityIcon = (entityType) => {
    const iconMap = {
      'PERSON': <User size={14} />,
      'PER': <User size={14} />,
      'GPE': <MapPin size={14} />,
      'LOC': <MapPin size={14} />,
      'LOCATION': <MapPin size={14} />,
      'DATE': <Calendar size={14} />,
      'TIME': <Calendar size={14} />
    };
    return iconMap[entityType] || '🏷️';
  };

  return (
    <div className="memory-card" onClick={() => onClick && onClick(memory)}>
      <div className="memory-header">
        <div className="memory-emotion">
          {getEmotionIcon(memory.sentiment?.emotion)}
        </div>
        <div className="memory-date">
          <Calendar size={14} />
          {formatDate(memory.timestamp)}
        </div>
      </div>
      
      {memory.type === 'image' && memory.image_url && (
        <div className="memory-image-container">
          <img 
            src={`http://localhost:8000${memory.image_url}`}
            alt={memory.raw_text}
            className="memory-image"
            onError={(e) => {
              e.target.style.display = 'none';
              console.error('Failed to load image:', memory.image_url);
            }}
          />
        </div>
      )}
      
      <div className="memory-content">
        <p className="memory-text">{memory.raw_text}</p>
      </div>
      
      {memory.entities && Array.isArray(memory.entities) && memory.entities.length > 0 && (
        <div className="memory-entities">
          {memory.entities.slice(0, 3).map((entity, index) => (
            <span key={index} className="entity-tag">
              {getEntityIcon(entity.type || entity.entity_type || entity.label)}
              {entity.entity || entity.text}
            </span>
          ))}
          {memory.entities.length > 3 && (
            <span className="entity-more">+{memory.entities.length - 3} more</span>
          )}
        </div>
      )}
      
      <div className="memory-footer">
        <div className="memory-sentiment">
          <Heart size={14} />
          <span>
            {Array.isArray(memory.sentiments) && memory.sentiments.length > 0 
              ? memory.sentiments[0].label 
              : memory.sentiment?.emotion || 'neutral'
            }
          </span>
        </div>
        <div className="memory-type">
          {memory.type === 'text' && '📝'}
          {memory.type === 'voice' && '🎤'}
          {memory.type === 'image' && '📷'}
        </div>
      </div>
    </div>
  );
};

export default MemoryCard;
