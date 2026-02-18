import React, { useState, useEffect } from 'react';
import { User, UserCog, ChevronDown, LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const UserProfile = ({ user, onLogout }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [profileImage, setProfileImage] = useState(null);
  const navigate = useNavigate();

  // Load profile image from localStorage on component mount
  useEffect(() => {
    const savedImage = localStorage.getItem(`profileImage_${user?.id}`);
    if (savedImage) {
      setProfileImage(savedImage);
    }
  }, [user]);

  const handleLogout = () => {
    // Show confirmation dialog
    const confirmed = window.confirm('Are you sure you want to logout?');
    
    if (confirmed) {
      if (onLogout) {
        onLogout();
      }
      navigate('/');
    }
    setIsOpen(false);
  };

  const handleProfileClick = () => {
    setIsOpen(false);
    navigate('/profile');
  };

  const toggleDropdown = () => setIsOpen(!isOpen);

  return (
    <div className="user-profile">
      <div className="profile-toggle" onClick={toggleDropdown}>
        <div className="profile-image-container">
          {profileImage ? (
            <img 
              src={profileImage} 
              alt={user?.username || 'User'}
              className="profile-image"
            />
          ) : (
            <div className="profile-icon">
              <User size={24} />
            </div>
          )}
        </div>
        <span className="username">{user?.username || 'User'}</span>
        <ChevronDown size={16} className={`dropdown-arrow ${isOpen ? 'open' : ''}`} />
      </div>
      
      {isOpen && (
        <div className="profile-dropdown">
          <div className="dropdown-item" onClick={handleProfileClick}>
            <UserCog size={16} />
            <span>Edit Profile</span>
          </div>
          <div className="dropdown-item" onClick={handleLogout}>
            <LogOut size={16} />
            <span>Logout</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserProfile;
