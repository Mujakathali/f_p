import React from 'react';
import { Play, Image, Mic } from 'lucide-react';
import TypingAnimation from './TypingAnimation';

const ChatBubble = ({ message }) => {
  const { type, content, messageType, file, timestamp, isTyping, hasTyped: initialHasTyped } = message;
  const isUser = type === 'user';
  const [hasTyped, setHasTyped] = React.useState(initialHasTyped || false);

  // Update hasTyped when message changes
  React.useEffect(() => {
    setHasTyped(initialHasTyped || false);
  }, [initialHasTyped, message.id]);

  const formatTime = (date) => {
    return new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const renderContent = () => {
    switch (messageType) {
      case 'image':
        return (
          <div className="message-content">
            {file && (
              <div className="image-preview">
                <img 
                  src={file.preview || URL.createObjectURL(file)} 
                  alt="Uploaded image"
                  className="preview-image"
                  onLoad={(e) => {
                    // Revoke object URL after image loads to prevent memory leaks
                    if (file.preview && file.preview.startsWith('blob:')) {
                      URL.revokeObjectURL(file.preview);
                    }
                  }}
                />
                <div className="image-overlay">
                  <Image size={16} />
                  <span>{file.name || 'Image'}</span>
                </div>
              </div>
            )}
            {content && <p className="image-caption">{content}</p>}
          </div>
        );
      case 'voice':
        return (
          <div className="message-content">
            <div className="voice-note">
              <Mic size={16} />
              <span>Voice note</span>
              <button className="play-button">
                <Play size={14} />
              </button>
            </div>
            {content && <p>{content}</p>}
          </div>
        );
      default:
        return (
          <div className="message-content">
            {isTyping && !isUser && !hasTyped ? (
              <TypingAnimation 
                text={content} 
                speed={30} 
                onComplete={() => {
                  setHasTyped(true);
                  // Update the message state to persist hasTyped
                  message.hasTyped = true;
                }}
              />
            ) : (
              content
            )}
          </div>
        );
    }
  };

  return (
    <div className={`chat-bubble ${isUser ? 'user' : 'ai'}`}>
      <div className="bubble-content">
        {renderContent()}
        <div className="message-time">
          {formatTime(timestamp)}
        </div>
      </div>
    </div>
  );
};

export default ChatBubble;
