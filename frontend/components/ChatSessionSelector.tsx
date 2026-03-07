'use client';

import { useState, useEffect } from 'react';
import { MessageCircle, Plus, Calendar, ArrowRight, Edit2, Trash2, Check, X } from 'lucide-react';
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
  const [editingSession, setEditingSession] = useState<string | null>(null);
  const [editingName, setEditingName] = useState('');
  const [deletingSession, setDeletingSession] = useState<string | null>(null);

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

  const startEditing = (session: ChatSession, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingSession(session.id);
    setEditingName(session.name);
  };

  const cancelEditing = () => {
    setEditingSession(null);
    setEditingName('');
  };

  const saveSessionName = async (sessionId: string) => {
    if (!editingName.trim()) {
      cancelEditing();
      return;
    }

    try {
      const response = await fetch(`/api/v1/chat-sessions/${sessionId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'x-user-id': 'user_123'
        },
        body: JSON.stringify({
          name: editingName.trim()
        })
      });

      if (!response.ok) {
        throw new Error('Failed to update session name');
      }

      // Update local state
      setSessions(prev => prev.map(session => 
        session.id === sessionId 
          ? { ...session, name: editingName.trim() }
          : session
      ));

      cancelEditing();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update session name');
    }
  };

  const confirmDelete = (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setDeletingSession(sessionId);
  };

  const cancelDelete = () => {
    setDeletingSession(null);
  };

  const deleteSession = async (sessionId: string) => {
    try {
      const response = await fetch(`/api/v1/chat-sessions/${sessionId}`, {
        method: 'DELETE',
        headers: {
          'x-user-id': 'user_123'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to delete session');
      }

      // Remove from local state
      setSessions(prev => prev.filter(session => session.id !== sessionId));
      setDeletingSession(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete session');
      setDeletingSession(null);
    }
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
            <div key={session.id} className="p-4 hover:bg-gray-50 transition-colors group">
              {deletingSession === session.id ? (
                // Delete confirmation UI
                <div className="flex items-center justify-between bg-red-50 p-4 rounded-lg border border-red-200">
                  <div>
                    <p className="text-red-800 font-medium">Delete this chat session?</p>
                    <p className="text-red-600 text-sm">This action cannot be undone.</p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => deleteSession(session.id)}
                      className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                    >
                      Delete
                    </button>
                    <button
                      onClick={cancelDelete}
                      className="bg-gray-300 text-gray-700 px-3 py-1 rounded text-sm hover:bg-gray-400"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                // Normal session display
                <div
                  onClick={() => handleSessionClick(session.id)}
                  className="cursor-pointer"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3">
                        <div className="bg-blue-100 p-2 rounded-lg">
                          <MessageCircle size={16} className="text-blue-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          {editingSession === session.id ? (
                            // Edit name input
                            <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                              <input
                                type="text"
                                value={editingName}
                                onChange={(e) => setEditingName(e.target.value)}
                                onKeyDown={(e) => {
                                  if (e.key === 'Enter') saveSessionName(session.id);
                                  if (e.key === 'Escape') cancelEditing();
                                }}
                                className="flex-1 px-2 py-1 border border-blue-300 rounded text-sm focus:outline-none focus:border-blue-500"
                                autoFocus
                              />
                              <button
                                onClick={() => saveSessionName(session.id)}
                                className="text-green-600 hover:text-green-700 p-1"
                              >
                                <Check size={14} />
                              </button>
                              <button
                                onClick={cancelEditing}
                                className="text-gray-400 hover:text-gray-600 p-1"
                              >
                                <X size={14} />
                              </button>
                            </div>
                          ) : (
                            <>
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
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    {editingSession !== session.id && (
                      <div className="flex items-center gap-1">
                        <button
                          onClick={(e) => startEditing(session, e)}
                          className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-blue-600 p-2 transition-all"
                          title="Edit name"
                        >
                          <Edit2 size={14} />
                        </button>
                        <button
                          onClick={(e) => confirmDelete(session.id, e)}
                          className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-600 p-2 transition-all"
                          title="Delete session"
                        >
                          <Trash2 size={14} />
                        </button>
                        <ArrowRight 
                          size={16} 
                          className="text-gray-400 group-hover:text-gray-600 transition-colors ml-2" 
                        />
                      </div>
                    )}
                  </div>
                </div>
              )}
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