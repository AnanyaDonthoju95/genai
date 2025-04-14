import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { ClipLoader } from 'react-spinners';

function ChatBox() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const chatBoxRef = useRef(null);

  const sendMessage = async () => {
    if (!input.trim()) {
      return setError('Please enter a message before sending.');
    }

    setError(null);
    const userMsg = { sender: 'You', text: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await axios.post('http://localhost:8000/chat', {
        user_id: 'user123',
        message: input
      });

      const aiMsg = { sender: 'person', text: res.data.response };
      setMessages(prev => [...prev, aiMsg]);
    } catch (error) {
      console.error('Error sending message:', error);
      setError('There was an error with the server. Please try again later.');
    }

    setLoading(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') sendMessage();
  };

  useEffect(() => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div
      className="vh-100 vw-100 d-flex flex-column align-items-center justify-content-center"
      style={{
        background: 'linear-gradient(to right, #e0f7fa, #e3f2fd)',
        padding: '20px',
      }}
    >
      <div
        className="card shadow-lg w-100"
        style={{
          maxWidth: '850px',
          height: '90vh',
          borderRadius: '20px',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <div className="card-header text-center bg-white border-0">
          <h2 style={{ color: '#007bff', fontWeight: 'bold' }}>🤖 IntelliBot</h2>
          <p className="text-muted mb-0">Your smart AI business assistant</p>
        </div>

        <div
          className="flex-grow-1 overflow-auto px-4 py-3"
          ref={chatBoxRef}
          style={{
            backgroundColor: '#f9f9f9',
            borderTop: '1px solid #ddd',
            borderBottom: '1px solid #ddd',
          }}
        >
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`mb-3 text-${msg.sender === 'You' ? 'end' : 'start'}`}
            >
              <div
                className={`d-inline-block p-3 rounded-4 shadow-sm ${
                  msg.sender === 'You'
                    ? 'bg-primary text-white'
                    : 'bg-light text-dark'
                }`}
                style={{ maxWidth: '75%', wordWrap: 'break-word' }}
              >
                <strong>{msg.sender}:</strong> {msg.text}
              </div>
            </div>
          ))}
          {loading && (
            <div className="text-center mt-3">
              <ClipLoader color="#007bff" size={40} />
              <div className="text-muted mt-2">IntelliBot is typing...</div>
            </div>
          )}
        </div>

        {error && (
          <div className="alert alert-danger text-center m-3">{error}</div>
        )}

        <div className="card-footer bg-white border-0 px-4 py-3">
          <div className="input-group">
            <input
              type="text"
              className="form-control rounded-pill"
              placeholder="Ask something..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              style={{
                padding: '12px 20px',
                fontSize: '16px',
                border: '1px solid #ccc',
              }}
            />
            <button
              className="btn btn-primary rounded-pill ms-2"
              onClick={sendMessage}
              style={{ padding: '10px 25px', fontWeight: 'bold' }}
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ChatBox;
