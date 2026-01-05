import React, { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';
import {
  MessageSquare, Send, Plus, Trash2, Menu, X, Star, ChevronDown,
  Cpu, Zap, Bot, User, Clock, Sparkles, Settings, Info, ThumbsUp, ThumbsDown
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

// Model configurations
const MODELS = {
  'gpt-4': { name: 'GPT-4', icon: '🧠', description: 'Complex reasoning', color: '#8b5cf6' },
  'gpt-35-turbo': { name: 'GPT-3.5 Turbo', icon: '⚡', description: 'Fast & efficient', color: '#06b6d4' }
};

function App() {
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState(null); // null = auto-select
  const [showSidebar, setShowSidebar] = useState(true);
  const [showModelSelect, setShowModelSelect] = useState(false);
  const [availableModels, setAvailableModels] = useState([]);
  const [feedbackModal, setFeedbackModal] = useState(null);
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Fetch sessions on mount
  useEffect(() => {
    fetchSessions();
    fetchModels();
  }, []);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchSessions = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/sessions`);
      const data = await res.json();
      setSessions(data);
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
    }
  };

  const fetchModels = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/models`);
      const data = await res.json();
      setAvailableModels(data);
    } catch (error) {
      console.error('Failed to fetch models:', error);
    }
  };

  const loadSession = async (sessionId) => {
    try {
      const res = await fetch(`${API_BASE}/api/sessions/${sessionId}`);
      const data = await res.json();
      setCurrentSession(data);
      setMessages(data.messages || []);
    } catch (error) {
      console.error('Failed to load session:', error);
    }
  };

  const createNewChat = async () => {
    setCurrentSession(null);
    setMessages([]);
    inputRef.current?.focus();
  };

  const deleteSession = async (sessionId, e) => {
    e.stopPropagation();
    try {
      await fetch(`${API_BASE}/api/sessions/${sessionId}`, { method: 'DELETE' });
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      if (currentSession?.id === sessionId) {
        setCurrentSession(null);
        setMessages([]);
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  };

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = inputValue.trim();
    setInputValue('');
    setIsLoading(true);

    // Add user message immediately
    const tempUserMsg = {
      id: 'temp-' + Date.now(),
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, tempUserMsg]);

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          session_id: currentSession?.id || null,
          model: selectedModel,
          stream: false
        })
      });

      const data = await res.json();
      
      // Update session info
      if (!currentSession) {
        setCurrentSession({ id: data.session_id });
        fetchSessions();
      }

      // Add assistant response
      setMessages(prev => [
        ...prev.filter(m => m.id !== tempUserMsg.id),
        {
          id: 'user-' + Date.now(),
          role: 'user',
          content: userMessage,
          timestamp: new Date().toISOString()
        },
        {
          ...data.message,
          model_selected: data.model_selected,
          was_auto_selected: data.was_auto_selected,
          complexity_score: data.complexity_score
        }
      ]);

    } catch (error) {
      console.error('Failed to send message:', error);
      setMessages(prev => [
        ...prev,
        {
          id: 'error-' + Date.now(),
          role: 'assistant',
          content: '❌ Failed to get response. Please check if the backend is running.',
          error: true
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const submitFeedback = async (rating, comment) => {
    if (!currentSession?.id) return;
    
    try {
      await fetch(`${API_BASE}/api/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: currentSession.id,
          message_id: feedbackModal?.messageId,
          rating,
          comment,
          was_helpful: rating >= 4
        })
      });
      setFeedbackModal(null);
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="app">
      {/* Background Effects */}
      <div className="bg-gradient" />
      <div className="bg-grid" />

      {/* Sidebar */}
      <aside className={`sidebar ${showSidebar ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <div className="logo">
            <span className="logo-icon">🦁</span>
            <span className="logo-text">ModelZoo</span>
          </div>
          <button className="sidebar-toggle" onClick={() => setShowSidebar(false)}>
            <X size={20} />
          </button>
        </div>

        <button className="new-chat-btn" onClick={createNewChat}>
          <Plus size={18} />
          <span>New Chat</span>
        </button>

        <div className="sessions-list">
          <div className="sessions-header">
            <MessageSquare size={14} />
            <span>Recent Chats</span>
          </div>
          {sessions.map(session => (
            <div
              key={session.id}
              className={`session-item ${currentSession?.id === session.id ? 'active' : ''}`}
              onClick={() => loadSession(session.id)}
            >
              <div className="session-info">
                <span className="session-title">{session.title}</span>
                <span className="session-meta">{session.message_count} messages</span>
              </div>
              <button
                className="session-delete"
                onClick={(e) => deleteSession(session.id, e)}
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
          {sessions.length === 0 && (
            <div className="no-sessions">
              <Sparkles size={24} />
              <p>Start a new conversation</p>
            </div>
          )}
        </div>

        <div className="sidebar-footer">
          <div className="model-info">
            <Info size={14} />
            <span>Azure OpenAI Powered</span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        {/* Header */}
        <header className="header">
          {!showSidebar && (
            <button className="menu-btn" onClick={() => setShowSidebar(true)}>
              <Menu size={20} />
            </button>
          )}
          
          <div className="header-title">
            <Bot size={20} />
            <span>{currentSession?.title || 'New Conversation'}</span>
          </div>

          {/* Model Selector */}
          <div className="model-selector">
            <button
              className="model-select-btn"
              onClick={() => setShowModelSelect(!showModelSelect)}
            >
              <Cpu size={16} />
              <span>{selectedModel ? MODELS[selectedModel]?.name : 'Auto Select'}</span>
              <ChevronDown size={14} />
            </button>
            
            {showModelSelect && (
              <div className="model-dropdown">
                <div
                  className={`model-option ${!selectedModel ? 'active' : ''}`}
                  onClick={() => { setSelectedModel(null); setShowModelSelect(false); }}
                >
                  <Zap size={16} />
                  <div>
                    <strong>Auto Select</strong>
                    <span>Intelligent model routing</span>
                  </div>
                </div>
                {availableModels.map(model => (
                  <div
                    key={model.id}
                    className={`model-option ${selectedModel === model.id ? 'active' : ''}`}
                    onClick={() => { setSelectedModel(model.id); setShowModelSelect(false); }}
                  >
                    <span className="model-emoji">{MODELS[model.id]?.icon || '🤖'}</span>
                    <div>
                      <strong>{model.display_name}</strong>
                      <span>{model.description}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </header>

        {/* Chat Area */}
        <div className="chat-area">
          {messages.length === 0 ? (
            <div className="welcome-screen">
              <div className="welcome-icon">🦁</div>
              <h1>Welcome to ModelZoo</h1>
              <p>Your intelligent multi-model AI assistant powered by Azure OpenAI</p>
              <div className="features-grid">
                <div className="feature-card">
                  <Zap size={24} />
                  <h3>Smart Routing</h3>
                  <p>Auto-selects the best model for your query</p>
                </div>
                <div className="feature-card">
                  <MessageSquare size={24} />
                  <h3>Chat Memory</h3>
                  <p>Remembers context across conversations</p>
                </div>
                <div className="feature-card">
                  <Star size={24} />
                  <h3>Feedback Loop</h3>
                  <p>Help improve responses with ratings</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="messages-container">
              {messages.map((msg, idx) => (
                <div
                  key={msg.id || idx}
                  className={`message ${msg.role} ${msg.error ? 'error' : ''} fade-in`}
                >
                  <div className="message-avatar">
                    {msg.role === 'user' ? <User size={18} /> : <Bot size={18} />}
                  </div>
                  <div className="message-content">
                    <div className="message-header">
                      <span className="message-role">
                        {msg.role === 'user' ? 'You' : 'ModelZoo'}
                      </span>
                      {msg.model_used && (
                        <span className="message-model" style={{ 
                          background: MODELS[msg.model_used]?.color || '#666' 
                        }}>
                          {MODELS[msg.model_used]?.icon} {MODELS[msg.model_used]?.name}
                          {msg.was_auto_selected && ' (auto)'}
                        </span>
                      )}
                    </div>
                    <div className="message-text">
                      {msg.content.split('\n').map((line, i) => (
                        <React.Fragment key={i}>
                          {line}
                          {i < msg.content.split('\n').length - 1 && <br />}
                        </React.Fragment>
                      ))}
                    </div>
                    {msg.role === 'assistant' && !msg.error && (
                      <div className="message-footer">
                        {msg.response_time && (
                          <span className="response-time">
                            <Clock size={12} /> {msg.response_time.toFixed(2)}s
                          </span>
                        )}
                        {msg.complexity_score !== undefined && (
                          <span className="complexity">
                            Complexity: {msg.complexity_score}
                          </span>
                        )}
                        <div className="message-actions">
                          <button
                            className="action-btn"
                            onClick={() => setFeedbackModal({ messageId: msg.id })}
                          >
                            <ThumbsUp size={14} />
                          </button>
                          <button
                            className="action-btn"
                            onClick={() => setFeedbackModal({ messageId: msg.id, negative: true })}
                          >
                            <ThumbsDown size={14} />
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="message assistant loading fade-in">
                  <div className="message-avatar">
                    <Bot size={18} />
                  </div>
                  <div className="message-content">
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="input-area">
          <div className="input-container">
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Ask ModelZoo anything..."
              rows={1}
              disabled={isLoading}
            />
            <button
              className="send-btn"
              onClick={sendMessage}
              disabled={!inputValue.trim() || isLoading}
            >
              <Send size={18} />
            </button>
          </div>
          <p className="input-hint">
            {selectedModel 
              ? `Using ${MODELS[selectedModel]?.name}` 
              : 'Auto-selecting best model based on query complexity'}
          </p>
        </div>
      </main>

      {/* Feedback Modal */}
      {feedbackModal && (
        <div className="modal-overlay" onClick={() => setFeedbackModal(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h3>Rate this response</h3>
            <div className="star-rating">
              {[1, 2, 3, 4, 5].map(star => (
                <button
                  key={star}
                  className="star-btn"
                  onClick={() => submitFeedback(star, '')}
                >
                  <Star size={24} fill={feedbackModal.negative && star <= 2 ? '#f59e0b' : 'none'} />
                </button>
              ))}
            </div>
            <button className="modal-close" onClick={() => setFeedbackModal(null)}>
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;

