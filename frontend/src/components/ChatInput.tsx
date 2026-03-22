import { useState } from 'react';
import { useRecoilValue, useRecoilCallback } from 'recoil';
import { messagesState, sessionIdState, isLoadingState, errorState, Message } from '../atoms/chatAtoms';
import axios from 'axios';
import { SendHorizonal, Loader2 } from 'lucide-react';

const ChatInput: React.FC = () => {
  const [input, setInput] = useState('');
  const sessionId = useRecoilValue(sessionIdState);
  const isLoading = useRecoilValue(isLoadingState);

  const handleSubmit = useRecoilCallback(({ set }) => async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      content: input,
      timestamp: new Date(),
    };

    set(messagesState, prev => [...prev, userMessage]);
    setInput('');
    set(isLoadingState, true);
    set(errorState, null);

    try {
      //   const API_URL = (import.meta as any).env.VITE_API_URL || '/api';
      const API_URL = "https://hr-interviewer-qgql.onrender.com"
      console.log("API URL: ", API_URL)
      const response = await axios.post(`${API_URL}/api/chat`, {
        session_id: sessionId,
        message: input,
      });

      const newMessages: Message[] = [];
      const timestamp = new Date();

      if (response.data.reply) {
        newMessages.push({
          id: Date.now().toString() + '-reply',
          role: 'assistant' as const,
          content: response.data.reply,
          timestamp,
        });
      }

      if (response.data.next_question) {
        // slight delay on timestamp to appear sequentially
        newMessages.push({
          id: Date.now().toString() + '-next',
          role: 'assistant' as const,
          content: response.data.next_question,
          timestamp: new Date(timestamp.getTime() + 1000),
        });
      }

      if (response.data.message) {
        newMessages.push({
          id: Date.now().toString() + '-msg',
          role: 'assistant' as const,
          content: response.data.message,
          timestamp,
        });
      }

      set(messagesState, prev => [...prev, ...newMessages]);
    } catch (error) {
      console.log("Error: ", error)
      set(errorState, 'Failed to send message. Please try again.');
    } finally {
      set(isLoadingState, false);
    }
  }, [input, sessionId, isLoading]);

  return (
    <form onSubmit={handleSubmit} className="chat-input">
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Type a message..."
        disabled={isLoading}
      />
      <button type="submit" disabled={isLoading || !input.trim()}>
        {isLoading ? <Loader2 size={18} className="animate-spin" /> : <SendHorizonal size={18} />}
      </button>
    </form>
  );
};

export default ChatInput;