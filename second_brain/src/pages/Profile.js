import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Mail, Phone, Camera, Save, ArrowLeft } from 'lucide-react';
import AuthService from '../services/auth';
import { toast } from 'react-toastify';

const Profile = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const [user, setUser] = useState(null);
  const [profileImage, setProfileImage] = useState(null);
  const [fullName, setFullName] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const userData = AuthService.getUser();
    if (userData) {
      setUser(userData);
      setFullName(userData.full_name || '');
      
      // Load profile image
      const savedImage = localStorage.getItem(`profileImage_${userData.id}`);
      if (savedImage) {
        setProfileImage(savedImage);
      }
    } else {
      navigate('/login');
    }
  }, [navigate]);

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Check file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        toast.error('Image size should be less than 5MB');
        return;
      }

      const reader = new FileReader();
      reader.onloadend = () => {
        const imageDataUrl = reader.result;
        setProfileImage(imageDataUrl);
        localStorage.setItem(`profileImage_${user.id}`, imageDataUrl);
        toast.success('Profile image updated!');
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    setLoading(true);

    try {
      // Update only full name locally (username is locked)
      const updatedUser = {
        ...user,
        full_name: fullName.trim()
      };
      
      localStorage.setItem('user', JSON.stringify(updatedUser));
      setUser(updatedUser);
      
      toast.success('Profile updated successfully!');
    } catch (error) {
      toast.error('Failed to update profile');
      console.error('Profile update error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    navigate(-1);
  };

  if (!user) {
    return null;
  }

  return (
    <div className="profile-page">
      <div className="profile-container">
        <div className="profile-header">
          <button className="back-btn" onClick={handleBack}>
            <ArrowLeft size={20} />
            <span>Back</span>
          </button>
          <h1>Edit Profile</h1>
        </div>

        <div className="profile-content">
          {/* Profile Image Section */}
          <div className="profile-image-section">
            <div className="profile-image-wrapper">
              {profileImage ? (
                <img 
                  src={profileImage} 
                  alt={user.username}
                  className="profile-image-large"
                />
              ) : (
                <div className="profile-icon-large">
                  <User size={64} />
                </div>
              )}
              <button 
                className="change-photo-btn"
                onClick={() => fileInputRef.current.click()}
              >
                <Camera size={20} />
              </button>
            </div>
            <p className="profile-image-hint">Click the camera icon to change your photo</p>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleImageUpload}
              accept="image/*"
              style={{ display: 'none' }}
            />
          </div>

          {/* Profile Form */}
          <form className="profile-form" onSubmit={handleSubmit}>
            <div className="form-section">
              <h2>Account Information</h2>
              
              <div className="form-group">
                <label htmlFor="username">
                  <User size={18} />
                  <span>Username (Locked)</span>
                </label>
                <input
                  type="text"
                  id="username"
                  name="username"
                  value={user?.username || ''}
                  readOnly
                  className="readonly-field"
                />
              </div>

              <div className="form-group">
                <label htmlFor="fullName">
                  <User size={18} />
                  <span>Full Name</span>
                </label>
                <input
                  type="text"
                  id="fullName"
                  name="fullName"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Enter your full name"
                  className="editable-field"
                />
              </div>

              <div className="form-group">
                <label htmlFor="email">
                  <Mail size={18} />
                  <span>Email Address</span>
                </label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={user?.email || 'Not set'}
                  readOnly
                  className="readonly-field"
                />
              </div>

              <div className="form-group">
                <label htmlFor="phone">
                  <Phone size={18} />
                  <span>Mobile Number</span>
                </label>
                <input
                  type="tel"
                  id="phone"
                  name="phone"
                  value={user?.phone || 'Not set'}
                  readOnly
                  className="readonly-field"
                />
              </div>
            </div>

            <div className="form-actions">
              <button 
                type="submit" 
                className="save-btn"
                disabled={loading}
              >
                <Save size={18} />
                <span>{loading ? 'Saving...' : 'Save Username'}</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Profile;
