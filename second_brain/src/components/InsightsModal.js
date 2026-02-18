import React from 'react';
import { X, Brain, TrendingUp, Calendar, Heart } from 'lucide-react';

const InsightsModal = ({ onClose }) => {
  const insights = [
    {
      icon: <Brain size={20} />,
      title: "Memory Patterns",
      content: "You've been sharing more visual memories this week. Your creativity seems to be flourishing!"
    },
    {
      icon: <TrendingUp size={20} />,
      title: "Growth Insights",
      content: "You've mentioned 'learning' 12 times this month. What new skills are you developing?"
    },
    {
      icon: <Calendar size={20} />,
      title: "Time Reflection",
      content: "Your most active memory-sharing time is between 7-9 PM. Evening reflections are powerful!"
    },
    {
      icon: <Heart size={20} />,
      title: "Emotional Journey",
      content: "Your recent memories show increasing positivity. You're on a great path!"
    }
  ];

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="insights-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>AI Insights</h2>
          <button className="close-button" onClick={onClose}>
            <X size={24} />
          </button>
        </div>
        
        <div className="modal-content">
          <p className="insights-intro">
            Here's what I've learned about your memory patterns:
          </p>
          
          <div className="insights-grid">
            {insights.map((insight, index) => (
              <div key={index} className="insight-card">
                <div className="insight-icon">
                  {insight.icon}
                </div>
                <div className="insight-content">
                  <h3>{insight.title}</h3>
                  <p>{insight.content}</p>
                </div>
              </div>
            ))}
          </div>
          
          <div className="modal-actions">
            <button className="primary-button" onClick={onClose}>
              Continue Chatting
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InsightsModal;
