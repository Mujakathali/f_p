import React from 'react';
import { Lightbulb } from 'lucide-react';

const FloatingActionButton = ({ onClick }) => {
  return (
    <button className="floating-action-button" onClick={onClick}>
      <Lightbulb size={24} />
      <span className="fab-tooltip">Insights</span>
    </button>
  );
};

export default FloatingActionButton;
