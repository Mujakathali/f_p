import { Camera, Send, X } from 'lucide-react';
import { useRef, useState } from 'react';

const InputBar = ({ onSendMessage }) => {
  const [inputValue, setInputValue] = useState('');
  const [selectedImage, setSelectedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const fileInputRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();

    if (selectedImage) {
      // Send image with caption
      onSendMessage(inputValue.trim() || '', 'image', selectedImage);
      setInputValue('');
      setSelectedImage(null);
      setImagePreview(null);
    } else if (inputValue.trim()) {
      // Send text message
      onSendMessage(inputValue.trim(), 'text');
      setInputValue('');
    }
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Create preview URL
      const previewUrl = URL.createObjectURL(file);
      setSelectedImage(file);
      setImagePreview(previewUrl);
      setInputValue(''); // Clear any existing text to focus on image caption

      // Reset file input
      e.target.value = '';
    }
  };

  const handleRemoveImage = () => {
    if (imagePreview) {
      URL.revokeObjectURL(imagePreview);
    }
    setSelectedImage(null);
    setImagePreview(null);
  };

  return (
    <div className="input-bar">
      {imagePreview && (
        <div className="image-preview-container">
          <div className="image-preview-wrapper">
            <img src={imagePreview} alt="Selected" className="input-image-preview" />
            <button
              type="button"
              className="remove-image-btn"
              onClick={handleRemoveImage}
              title="Remove image"
            >
              <X size={16} />
            </button>
          </div>
          <p className="image-caption-hint">Add a caption for your image...</p>
        </div>
      )}
      <form onSubmit={handleSubmit} className="input-form">
        <div className="input-container">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder={selectedImage ? "Add a caption for your image..." : "Share a memory, ask a question..."}
            className="message-input"
          />

          <div className="input-actions">
            <button
              type="button"
              className="action-button"
              onClick={() => fileInputRef.current?.click()}
              title="Upload Image"
            >
              <Camera size={20} />
            </button>

            <button
              type="submit"
              className="send-button"
              disabled={!inputValue.trim() && !selectedImage}
            >
              <Send size={20} />
            </button>
          </div>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleImageUpload}
          style={{ display: 'none' }}
        />
      </form>
    </div>
  );
};

export default InputBar;
