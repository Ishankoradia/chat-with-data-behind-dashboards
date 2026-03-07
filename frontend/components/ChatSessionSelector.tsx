'use client';

import { useState, useEffect } from 'react';
import { MessageCircle, Plus, Calendar, ArrowRight } from 'lucide-react';
import { formatTimestamp } from '@/lib/utils';

interface ChatSession {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  message_count?: number;
  last_message?: string;
}

interface ChatSessionSelectorProps {
  dashboardContextId: string;
  onSessionSelected: (sessionId: string) => void;
  onNewSession: () => void;
}

export default function ChatSessionSelector({ 
  dashboardContextId, 
  onSessionSelected, 
  onNewSession 
}: ChatSessionSelectorProps) {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadChatSessions();
  }, [dashboardContextId]);

  const loadChatSessions = async () => {
    if (!dashboardContextId) return;

    try {
      setLoading(true);
      const response = await fetch(`/api/v1/chat-sessions/?dashboard_context_id=${dashboardContextId}`, {
        headers: {
          'x-user-id': 'user_123'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load chat sessions');
      }

      const sessionsData = await response.json();
      setSessions(sessionsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load chat sessions');
    } finally {
      setLoading(false);
    }
  };

  const handleSessionClick = (sessionId: string) => {
    onSessionSelected(sessionId);
  };

  const handleNewSessionClick = () => {
    onNewSession();
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-500">Loading chat sessions...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="text-center py-8">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={loadChatSessions}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border">
      {/* Header */}
      <div className="border-b p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <MessageCircle size={24} />
              Chat Sessions
            </h2>
            <p className="text-gray-600 mt-1">
              Continue a previous conversation or start a new one
            </p>
          </div>
          <button
            onClick={handleNewSessionClick}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <Plus size={16} />
            New Chat
          </button>
        </div>
      </div>

      {/* Sessions List */}
      <div className="divide-y">
        {sessions.length === 0 ? (
          <div className="p-8 text-center">
            <MessageCircle size={48} className="text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No chat sessions yet</h3>
            <p className="text-gray-500 mb-4">
              Start your first conversation with this dashboard context
            </p>
            <button
              onClick={handleNewSessionClick}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 flex items-center gap-2 mx-auto"
            >
              <Plus size={16} />
              Start First Chat
            </button>
          </div>
        ) : (
          sessions.map((session) => (
            <div
              key={session.id}
              onClick={() => handleSessionClick(session.id)}
              className="p-4 hover:bg-gray-50 cursor-pointer transition-colors group"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3">
                    <div className="bg-blue-100 p-2 rounded-lg">
                      <MessageCircle size={16} className="text-blue-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-gray-900 truncate">
                        {session.name}
                      </h3>
                      <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                        <div className="flex items-center gap-1">
                          <Calendar size={12} />
                          <span>{formatTimestamp(new Date(session.created_at))}</span>
                        </div>
                        {session.message_count && (
                          <span>{session.message_count} messages</span>
                        )}
                      </div>
                      {session.last_message && (
                        <p className="text-sm text-gray-600 truncate mt-1 max-w-md">
                          Last: {session.last_message}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
                <ArrowRight 
                  size={16} 
                  className="text-gray-400 group-hover:text-gray-600 transition-colors" 
                />
              </div>
            </div>
          ))
        )}
      </div>

      {/* Footer */}
      {sessions.length > 0 && (
        <div className="border-t p-4 bg-gray-50">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>{sessions.length} chat session{sessions.length !== 1 ? 's' : ''}</span>
            <button
              onClick={loadChatSessions}
              className="text-blue-600 hover:text-blue-700"
            >
              Refresh
            </button>
          </div>
        </div>
      )}
    </div>
  );
}