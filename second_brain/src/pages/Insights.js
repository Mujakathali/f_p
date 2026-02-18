import React, { useState } from 'react';

const Insights = () => {
  const [selectedTimeframe, setSelectedTimeframe] = useState('month');

  const reflectiveQuestions = [
    {
      question: "What did I learn in September 2024?",
      answer: "You've learned the importance of consistency in fitness, discovered new depths in your relationships, and gained confidence in public speaking through your project presentation."
    },
    {
      question: "What patterns do I see in my happiest memories?",
      answer: "Your happiest memories often involve personal achievements, quality time with family, and moments of connection with friends. Physical activities and outdoor settings frequently appear."
    },
    {
      question: "How have I grown this month?",
      answer: "You've developed greater discipline through marathon training, strengthened family bonds during vacation, and expanded your social circle through meaningful conversations."
    }
  ];

  const emotionalPatterns = [
    { emotion: "😊 Happy", percentage: 68, color: "#10B981" },
    { emotion: "🤔 Thoughtful", percentage: 15, color: "#6366F1" },
    { emotion: "🎉 Excited", percentage: 12, color: "#F59E0B" },
    { emotion: "😢 Sad", percentage: 3, color: "#EF4444" },
    { emotion: "😡 Frustrated", percentage: 2, color: "#DC2626" }
  ];

  const growthMetrics = [
    { metric: "Personal Goals Achieved", value: 3, trend: "+2 from last month" },
    { metric: "Social Connections Made", value: 5, trend: "+1 from last month" },
    { metric: "New Experiences", value: 8, trend: "+3 from last month" },
    { metric: "Reflection Sessions", value: 12, trend: "+4 from last month" }
  ];

  const milestones = [
    {
      title: "First Marathon Completed",
      date: "September 8, 2024",
      impact: "Major fitness milestone achieved after 6 months of training",
      emotion: "🏃‍♂️"
    },
    {
      title: "Family Vacation Memories",
      date: "September 10, 2024",
      impact: "Strengthened family bonds and created lasting memories",
      emotion: "😊"
    }
  ];

  return (
    <div className="insights">
      <div className="page-header">
        <h1>AI Insights</h1>
        <p>Discover patterns and meaningful reflections from your memories</p>
      </div>

      <div className="insights-controls">
        <div className="timeframe-selector">
          <button 
            className={`timeframe-btn ${selectedTimeframe === 'week' ? 'active' : ''}`}
            onClick={() => setSelectedTimeframe('week')}
          >
            This Week
          </button>
          <button 
            className={`timeframe-btn ${selectedTimeframe === 'month' ? 'active' : ''}`}
            onClick={() => setSelectedTimeframe('month')}
          >
            This Month
          </button>
          <button 
            className={`timeframe-btn ${selectedTimeframe === 'year' ? 'active' : ''}`}
            onClick={() => setSelectedTimeframe('year')}
          >
            This Year
          </button>
        </div>
      </div>

      <div className="insights-grid">
        <div className="insight-section">
          <div className="card">
            <h2>Reflective Questions</h2>
            <div className="questions-list">
              {reflectiveQuestions.map((item, index) => (
                <div key={index} className="question-item">
                  <h3 className="question">{item.question}</h3>
                  <p className="answer">{item.answer}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="insight-section">
          <div className="card">
            <h2>Emotional Patterns</h2>
            <div className="emotion-chart">
              {emotionalPatterns.map((pattern, index) => (
                <div key={index} className="emotion-bar">
                  <div className="emotion-label">
                    <span>{pattern.emotion}</span>
                    <span>{pattern.percentage}%</span>
                  </div>
                  <div className="emotion-progress">
                    <div 
                      className="emotion-fill"
                      style={{ 
                        width: `${pattern.percentage}%`,
                        backgroundColor: pattern.color
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="insight-section">
          <div className="card">
            <h2>Growth Tracking</h2>
            <div className="growth-metrics">
              {growthMetrics.map((metric, index) => (
                <div key={index} className="metric-item">
                  <div className="metric-header">
                    <h4>{metric.metric}</h4>
                    <span className="metric-value">{metric.value}</span>
                  </div>
                  <p className="metric-trend">{metric.trend}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="insight-section">
          <div className="card">
            <h2>Milestone Highlights</h2>
            <div className="milestones-list">
              {milestones.map((milestone, index) => (
                <div key={index} className="milestone-item">
                  <div className="milestone-emotion">{milestone.emotion}</div>
                  <div className="milestone-content">
                    <h3>{milestone.title}</h3>
                    <p className="milestone-date">{milestone.date}</p>
                    <p className="milestone-impact">{milestone.impact}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="insight-section full-width">
          <div className="card">
            <h2>AI Recommendations</h2>
            <div className="recommendations">
              <div className="recommendation-item">
                <div className="recommendation-icon">💡</div>
                <div className="recommendation-content">
                  <h4>Continue Your Fitness Journey</h4>
                  <p>Your marathon achievement shows great dedication. Consider setting your next fitness goal to maintain momentum.</p>
                </div>
              </div>
              <div className="recommendation-item">
                <div className="recommendation-icon">👥</div>
                <div className="recommendation-content">
                  <h4>Nurture Social Connections</h4>
                  <p>Your coffee conversations show the value of deep connections. Schedule regular catch-ups with friends.</p>
                </div>
              </div>
              <div className="recommendation-item">
                <div className="recommendation-icon">📝</div>
                <div className="recommendation-content">
                  <h4>Document More Moments</h4>
                  <p>You have gaps in your memory timeline. Consider adding daily reflections to capture smaller moments.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Insights;
