import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const Navigation = ({ sidebarOpen, setSidebarOpen }) => {
  const location = useLocation();

  const navItems = [
    { path: '/', icon: '🏠', label: 'Dashboard' },
    { path: '/add-memory', icon: '➕', label: 'Add Memory' },
    { path: '/search', icon: '🔍', label: 'Search' },
    { path: '/timeline', icon: '📅', label: 'Timeline' },
    { path: '/graph', icon: '🕸️', label: 'Graph View' },
    { path: '/insights', icon: '💡', label: 'Insights' },
    { path: '/settings', icon: '⚙️', label: 'Settings' }
  ];

  return (
    <nav className="sidebar">
      <div className="logo">
        <span className="logo-icon">🧠</span>
        <span className="logo-text">MemoryGraph AI</span>
      </div>
      
      <ul className="nav-menu">
        {navItems.map((item) => (
          <li key={item.path} className="nav-item">
            <Link 
              to={item.path} 
              className={`nav-link ${location.pathname === item.path ? 'active' : ''}`}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
};

export default Navigation;
