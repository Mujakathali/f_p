import React, { useState } from 'react';
import { Route, BrowserRouter as Router, Routes, useLocation } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './App.css';
import ChatScreen from './components/ChatScreen';
import FloatingActionButton from './components/FloatingActionButton';
import Header from './components/Header';
import InputBar from './components/InputBar';
import InsightsModal from './components/InsightsModal';
import ModeToggle from './components/ModeToggle';
import SearchMode from './components/SearchMode';
import { ThemeProvider } from './contexts/ThemeContext';
import GraphView from './pages/GraphView';
import Home from './pages/Home';
import Login from './pages/Login';
import Profile from './pages/Profile';
import SignUp from './pages/SignUp';
import Timeline from './pages/Timeline';
import ApiService from './services/api';

function AppContent() {
  const [currentView, setCurrentView] = useState('home');
  const [chatMode, setChatMode] = useState('store'); // 'store' or 'search'
  const initialMessage = {
    id: 1,
    type: 'ai',
    content: "Hi! I'm your MemoryGraph AI. Share your thoughts, upload images, or record voice notes - I'll help you store and retrieve your memories.",
    timestamp: new Date()
  };
  const [messages, setMessages] = useState([initialMessage]);
  const [showInsights, setShowInsights] = useState(false);
  const location = useLocation();

  // Clear chat when user logs out or changes
  const clearChat = () => {
    setMessages([{
      ...initialMessage,
      id: Date.now(),
      timestamp: new Date()
    }]);
    setChatMode('store');
  };

  // Monitor authentication changes and clear chat when user changes
  React.useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === 'access_token' && !e.newValue) {
        // Token was removed (logout)
        clearChat();
      } else if (e.key === 'user' && e.newValue !== e.oldValue) {
        // User changed
        clearChat();
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  React.useEffect(() => {
    if (location.pathname === '/') {
      setCurrentView('home');
    } else if (location.pathname === '/chat') {
      setCurrentView('chat');
    } else if (location.pathname === '/timeline') {
      setCurrentView('timeline');
    } else if (location.pathname === '/graph') {
      setCurrentView('graph');
    } else if (location.pathname === '/login') {
      setCurrentView('login');
    } else if (location.pathname === '/signup') {
      setCurrentView('signup');
    } else if (location.pathname === '/profile') {
      setCurrentView('profile');
    }
  }, [location.pathname]);

  const addMessage = (message) => {
    setMessages(prev => [...prev, { ...message, id: Date.now(), timestamp: new Date() }]);
  };

  const handleSendMessage = async (content, type = 'text', file = null) => {
    // Add user message
    addMessage({
      type: 'user',
      content,
      messageType: type,
      file
    });

    // Immediately show AI response with typing animation
    const aiMessageId = Date.now() + 1;
    const tempAiMessage = {
      id: aiMessageId,
      type: 'ai',
      content: '✨ Processing your message...',
      timestamp: new Date(),
      isTyping: true,
      hasTyped: false  // Track if typing animation has completed
    };
    setMessages(prev => [...prev, tempAiMessage]);

    try {
      let response;

      if (type === 'voice' && file) {
        // Handle voice upload with Whisper transcription
        response = await ApiService.addVoiceMemory(file, { source: 'chat' });
      } else if (type === 'image' && file) {
        // Handle image upload with caption
        response = await ApiService.addImageMemory(file, content || '', { source: 'chat' });
      } else {
        // Handle text input
        const isQuestion = /\?|what|how|when|where|why|who|tell me|show me|find|search/i.test(content);

        if (chatMode === 'search' && isQuestion) {
          // Ask using AI over retrieved memories
          const askRes = await ApiService.askMemories(content, 8, 'hybrid');
          const searchResults = await ApiService.searchMemories(content, 5);
          const related = (searchResults.memories || []).slice(0, 5);

          const relatedMemories = related.map(mem =>
            `📝 ${mem.raw_text || mem.processed_text} (${new Date(mem.timestamp).toLocaleDateString()})`
          ).join('\n');

          const finalContent =
            `${askRes.answer || "I don't know."}` +
            (related.length ? `\n\nRelated memories:\n\n${relatedMemories}` : '');

          setMessages(prev => prev.map(msg =>
            msg.id === aiMessageId
              ? { ...msg, content: finalContent, isTyping: true, hasTyped: false, memories: related }
              : msg
          ));
          return;
        } else {
          // Store as new memory (always store in 'store' mode)
          response = await ApiService.addMemory(content, { source: 'chat' });
        }
      }

      // Update AI response with final content
      let responseContent = "✅ Memory stored successfully!";

      // Update the temporary message with final content
      setMessages(prev => prev.map(msg =>
        msg.id === aiMessageId
          ? { ...msg, content: responseContent, isTyping: true, hasTyped: false, memory: response }
          : msg
      ));

    } catch (error) {
      console.error('Failed to process message:', error);

      // Update the temporary message with error content
      const errorContent = `❌ Sorry, I couldn't process that right now. Please check if the backend is running. Error: ${error.message}`;
      setMessages(prev => prev.map(msg =>
        msg.id === aiMessageId
          ? { ...msg, content: errorContent, isTyping: true, hasTyped: false }
          : msg
      ));
    }
  };

  return (
    <div className="App">
      <Header currentView={currentView} setCurrentView={setCurrentView} onClearChat={clearChat} />

      <main className="main-content">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/chat" element={
            <>
              <ModeToggle mode={chatMode} onModeChange={setChatMode} />
              {chatMode === 'store' ? (
                <>
                  <ChatScreen messages={messages} />
                  <InputBar onSendMessage={handleSendMessage} />
                  <FloatingActionButton onClick={() => setShowInsights(true)} />
                </>
              ) : (
                <SearchMode />
              )}
            </>
          } />
          <Route path="/timeline" element={<Timeline />} />
          <Route path="/graph" element={<GraphView />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<SignUp />} />
          <Route path="/profile" element={<Profile />} />
        </Routes>
      </main>

      {showInsights && (
        <InsightsModal onClose={() => setShowInsights(false)} />
      )}

      <ToastContainer
        position="top-right"
        autoClose={3000}
        hideProgressBar={false}
        newestOnTop
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="light"
      />
    </div>
  );
}

function App() {
  return (
    <ThemeProvider>
      <Router>
        <AppContent />
      </Router>
    </ThemeProvider>
  );
}

export default App;
