import { useEffect, useRef } from 'react';
import { useRecoilValue, useRecoilCallback } from 'recoil';
import { messagesState, sessionIdState, errorState, isLoadingState } from '../atoms/chatAtoms';
import ChatMessage from './ChatMessage';
import axios from 'axios';

const ChatWindow: React.FC = () => {
  const messages = useRecoilValue(messagesState);
  const sessionId = useRecoilValue(sessionIdState);
  const error = useRecoilValue(errorState);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const startInterview = useRecoilCallback(({ set }) => async () => {
    try {
      set(isLoadingState, true);
      set(errorState, null);
      const API_URL = (import.meta as any).env.VITE_API_URL || '/api';
      const response = await axios.post(`${API_URL}/start`);
      
      set(sessionIdState, response.data.session_id);

      const initialMessage = {
        id: Date.now().toString(),
        role: 'assistant' as const,
        content: response.data.question,
        timestamp: new Date(),
      };
      set(messagesState, [initialMessage]);
    } catch (error) {
      set(errorState, 'Failed to start interview. Please refresh and try again.');
    } finally {
      set(isLoadingState, false);
    }
  }, []);

  useEffect(() => {
    if (!sessionId) {
      startInterview();
    }
  }, [sessionId, startInterview]);

  return (
    <div className="chat-window">
      {error && <div className="error">{error}</div>}
      <div className="messages">
        {messages.map(message => (
          <ChatMessage key={message.id} message={message} />
        ))}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

export default ChatWindow;