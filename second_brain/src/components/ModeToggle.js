import { Plus, Search } from 'lucide-react';

const ModeToggle = ({ mode, onModeChange }) => {
  return (
    <div className="mode-toggle-container">
      <div className="mode-toggle">
        <button
          className={`mode-button ${mode === 'store' ? 'active' : ''}`}
          onClick={() => onModeChange('store')}
        >
          <Plus size={16} />
          Store
        </button>
        <button
          className={`mode-button ${mode === 'search' ? 'active' : ''}`}
          onClick={() => onModeChange('search')}
        >
          <Search size={16} />
          Search
        </button>
        <div className={`mode-slider ${mode}`}></div>
      </div>
      <div className="mode-description">
        {mode === 'store' ? (
          <span>💾 Add new memories, images, and voice notes</span>
        ) : (
          <span>🔍 Search and retrieve your stored memories</span>
        )}
      </div>
    </div>
  );
};

export default ModeToggle;
