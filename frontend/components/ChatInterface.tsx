'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Database, Clock, AlertCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { ChatMessage, ChatRequest, ChatResponse } from '@/types';
import { formatTimestamp, formatExecutionTime, cn } from '@/lib/utils';

interface ChatInterfaceProps {
  dashboardContextId: string;
  disabled?: boolean;
  existingChatSessionId?: string;
}

export default function ChatInterface({ dashboardContextId, disabled = false, existingChatSessionId }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [chatSessionId, setChatSessionId] = useState<string | null>(null);
  const [isInitializing, setIsInitializing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);


  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initialize chat session (existing or create new)
  useEffect(() => {
    const initializeChatSession = async () => {
      if (!dashboardContextId) return;
      
      setIsInitializing(true);
      setError(null);
      setMessages([]);
      
      try {
        if (existingChatSessionId) {
          // Use existing chat session and load its messages
          setChatSessionId(existingChatSessionId);
          await loadChatHistory(existingChatSessionId);
        } else {
          // Create new chat session
          const response = await fetch('/api/v1/chat-sessions/', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'x-user-id': 'user_123'
            },
            body: JSON.stringify({
              dashboard_context_id: dashboardContextId,
              name: `Chat Session - ${new Date().toLocaleString()}`
            }),
          });

          if (!response.ok) {
            throw new Error(`Failed to create chat session: ${response.statusText}`);
          }

          const sessionData = await response.json();
          setChatSessionId(sessionData.id);
        }
      } catch (error) {
        console.error('Error initializing chat session:', error);
        setError('Failed to initialize chat session');
      } finally {
        setIsInitializing(false);
      }
    };

    initializeChatSession();
  }, [dashboardContextId, existingChatSessionId]);

  // Load chat history for existing session
  const loadChatHistory = async (sessionId: string) => {
    try {
      const response = await fetch(`/api/v1/chat-sessions/${sessionId}/messages`, {
        headers: {
          'x-user-id': 'user_123'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load chat history');
      }

      const messagesData = await response.json();
      
      // Convert backend messages to frontend format
      const formattedMessages: ChatMessage[] = messagesData.map((msg: any) => ({
        id: msg.id,
        role: msg.role,
        content: msg.content,
        timestamp: new Date(msg.created_at),
        queryResult: msg.query_result ? JSON.parse(msg.query_result) : undefined,
        reasoning: msg.reasoning
      }));

      setMessages(formattedMessages);
    } catch (error) {
      console.error('Error loading chat history:', error);
      setError('Failed to load chat history');
    }
  };

  const clearChat = () => {
    setMessages([]);
    setError(null);
  };

  const sendMessage = async () => {
    if (!inputValue.trim() || disabled || isLoading || !chatSessionId) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setError(null);

    try {
      const request = {
        message: userMessage.content,
        chat_session_id: chatSessionId,
        stream: true,
      };

      const response = await fetch(`/api/v1/chat-sessions/${chatSessionId}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      // Handle streaming response
      if (request.stream && response.body) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        
        // Add a temporary message showing current step
        let tempMessageId = (Date.now() + 1).toString();
        const tempMessage: ChatMessage = {
          id: tempMessageId,
          role: 'assistant',
          content: 'Processing your request...',
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, tempMessage]);
        
        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';
            
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const jsonStr = line.slice(6);
                if (jsonStr.trim()) {
                  try {
                    const data = JSON.parse(jsonStr);
                    
                    if (data.step) {
                      // Update the temporary message with current step
                      setMessages(prev => prev.map(msg => 
                        msg.id === tempMessageId 
                          ? { ...msg, content: data.step }
                          : msg
                      ));
                    }
                    
                    if (data.final) {
                      // Replace temporary message with final response
                      const finalMessage: ChatMessage = {
                        id: tempMessageId,
                        role: 'assistant',
                        content: data.response || 'Response completed',
                        timestamp: new Date(),
                        queryResult: data.query_result,
                        reasoning: data.reasoning,
                      };
                      setMessages(prev => prev.map(msg => 
                        msg.id === tempMessageId ? finalMessage : msg
                      ));
                      break;
                    }
                  } catch (e) {
                    console.warn('Failed to parse SSE data:', jsonStr);
                  }
                }
              }
            }
          }
        } finally {
          reader.releaseLock();
        }
      } else {
        // Fallback to regular JSON response
        const data: ChatResponse = await response.json();
        const assistantMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.response,
          timestamp: new Date(),
          queryResult: data.queryResult,
          reasoning: data.reasoning,
        };
        setMessages(prev => [...prev, assistantMessage]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
      
      // Add error message to chat
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error while processing your request. Please try again.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border flex flex-col h-[600px]">
      {/* Header */}
      <div className="border-b p-4 flex justify-between items-center">
        <div>
          <h2 className="text-lg font-semibold">Chat</h2>
          <div className="text-sm text-gray-500 space-y-1">
            {dashboardContextId && (
              <p>Dashboard Context: {dashboardContextId}</p>
            )}
            {chatSessionId && (
              <p>Session: {chatSessionId}</p>
            )}
            {existingChatSessionId && messages.length > 0 && (
              <p className="text-green-600">Loaded {messages.length} previous messages</p>
            )}
          </div>
        </div>
        {messages.length > 0 && (
          <button
            onClick={clearChat}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            Clear Chat
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {isInitializing && (
          <div className="text-center text-gray-500 py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p>Initializing chat session...</p>
          </div>
        )}
        
        {!disabled && !isInitializing && messages.length === 0 && chatSessionId && (
          <div className="text-center text-gray-500 py-8">
            <p className="mb-2">Start a conversation!</p>
            <p className="text-sm">Try asking:</p>
            <ul className="text-sm mt-2 space-y-1">
              <li>• "What was our revenue last month?"</li>
              <li>• "Show me top performing products"</li>
              <li>• "Break down sales by region"</li>
            </ul>
          </div>
        )}

        {disabled && !existingChatSessionId && (
          <div className="text-center text-gray-500 py-8">
            <p>Please select a dashboard to start chatting</p>
          </div>
        )}

        {disabled && existingChatSessionId && (
          <div className="text-center text-gray-500 py-8">
            <p>Loading session context...</p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              "flex w-full",
              message.role === 'user' ? 'justify-end' : 'justify-start'
            )}
          >
            <div
              className={cn(
                "max-w-[70%] rounded-lg px-4 py-2",
                message.role === 'user'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-gray-100 text-gray-900'
              )}
            >
              <div className="prose prose-sm max-w-none whitespace-pre-wrap">
                <ReactMarkdown 
                  components={{
                    // Style markdown elements
                    h1: (props) => <h1 className="text-lg font-bold mb-2" {...props} />,
                    h2: (props) => <h2 className="text-md font-bold mb-2" {...props} />,
                    h3: (props) => <h3 className="text-sm font-bold mb-1" {...props} />,
                    strong: (props) => <strong className="font-semibold" {...props} />,
                    ul: (props) => <ul className="list-disc ml-4 mb-2" {...props} />,
                    li: (props) => <li className="mb-1" {...props} />,
                    p: (props) => <p className="mb-2" {...props} />,
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
              
              {/* Query Result */}
              {message.queryResult && (
                <div className="mt-3 border-t pt-3">
                  <div className="flex items-center gap-2 text-xs text-gray-600 mb-2">
                    <Database size={12} />
                    <span>Query executed</span>
                    {message.queryResult.execution_time_ms && (
                      <>
                        <Clock size={12} />
                        <span>{formatExecutionTime(message.queryResult.execution_time_ms)}</span>
                      </>
                    )}
                  </div>
                  
                  <details className="text-xs">
                    <summary className="cursor-pointer text-gray-600 hover:text-gray-800">
                      View SQL & Results ({message.queryResult.row_count} rows)
                    </summary>
                    <div className="mt-2 space-y-2">
                      <div>
                        <strong>SQL:</strong>
                        <pre className="bg-gray-50 p-2 rounded mt-1 overflow-x-auto">
                          <code>{message.queryResult.sql}</code>
                        </pre>
                      </div>
                      
                      {message.queryResult.data.length > 0 && (
                        <div>
                          <strong>Sample Results:</strong>
                          <div className="bg-gray-50 p-2 rounded mt-1 overflow-x-auto">
                            <table className="min-w-full text-xs">
                              <thead>
                                <tr>
                                  {message.queryResult.columns.map((col) => (
                                    <th key={col} className="text-left font-medium p-1 border-b">
                                      {col}
                                    </th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody>
                                {message.queryResult.data.slice(0, 3).map((row, idx) => (
                                  <tr key={idx}>
                                    {message.queryResult!.columns.map((col) => (
                                      <td key={col} className="p-1 border-b">
                                        {String(row[col] ?? '')}
                                      </td>
                                    ))}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                            {message.queryResult.data.length > 3 && (
                              <p className="text-gray-500 mt-1">
                                ... and {message.queryResult.data.length - 3} more rows
                              </p>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </details>
                </div>
              )}
              
              <div className="text-xs opacity-70 mt-2">
                {formatTimestamp(message.timestamp)}
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-4 py-2 max-w-[70%]">
              <div className="flex items-center gap-2">
                <div className="animate-spin h-4 w-4 border-2 border-gray-400 border-t-transparent rounded-full"></div>
                <span className="text-gray-600">Thinking...</span>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="flex justify-center">
            <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-2 flex items-center gap-2 text-red-700">
              <AlertCircle size={16} />
              <span className="text-sm">{error}</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t p-4">
        <div className="flex gap-3">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={
              disabled && !existingChatSessionId 
                ? 'Select a dashboard first...' 
                : disabled && existingChatSessionId 
                  ? 'Loading session context...'
                  : 'Ask a question about your data...'
            }
            disabled={disabled || isLoading}
            className="flex-1 resize-none border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500"
            rows={1}
          />
          <button
            onClick={sendMessage}
            disabled={disabled || isLoading || !inputValue.trim() || !chatSessionId || isInitializing}
            className="bg-primary text-primary-foreground rounded-lg px-4 py-2 hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Send size={16} />
            <span className="hidden sm:inline">Send</span>
          </button>
        </div>
      </div>
    </div>
  );
}