'use client';

import { useState, useEffect } from 'react';
import { Plus, Database, MessageSquare, Calendar, ArrowRight, Trash2, AlertCircle } from 'lucide-react';

interface DashboardContextData {
  id: string;
  name: string;
  description?: string;
  datasource_id: string;
  text_context?: string;
  json_context?: string;
  additional_instructions?: string;
  created_at: string;
  updated_at: string;
}

interface DashboardContextListProps {
  onSelectContext: (context: DashboardContextData) => void;
  onCreateNew: () => void;
}

export default function DashboardContextList({ onSelectContext, onCreateNew }: DashboardContextListProps) {
  const [contexts, setContexts] = useState<DashboardContextData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingContext, setDeletingContext] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);

  useEffect(() => {
    fetchDashboardContexts();
  }, []);

  const fetchDashboardContexts = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await fetch('/api/v1/dashboard-contexts/');
      if (response.ok) {
        const contextData = await response.json();
        setContexts(contextData);
      } else {
        setError('Failed to fetch dashboard contexts');
      }
    } catch (error) {
      setError('Failed to connect to server');
    } finally {
      setIsLoading(false);
    }
  };

  const deleteContext = async (contextId: string) => {
    try {
      setDeletingContext(contextId);
      setError(null);

      const response = await fetch(`/api/v1/dashboard-contexts/${contextId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        // Remove the context from the list
        setContexts(prev => prev.filter(context => context.id !== contextId));
        setShowDeleteConfirm(null);
      } else {
        setError('Failed to delete dashboard context');
      }
    } catch (error) {
      setError('Failed to connect to server');
    } finally {
      setDeletingContext(null);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return 'Unknown date';
    }
  };

  if (isLoading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading your dashboard contexts...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-4">
          <p className="text-red-800">{error}</p>
        </div>
        <button
          onClick={fetchDashboardContexts}
          className="py-2 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">Dashboard Chat</h1>
        <p className="text-lg text-gray-600 mb-6">
          Continue with an existing dashboard context or create a new one
        </p>
      </div>

      {/* Create New Button */}
      <div className="text-center mb-8">
        <button
          onClick={onCreateNew}
          className="inline-flex items-center gap-3 py-3 px-6 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus size={20} />
          Create New Dashboard Context
        </button>
      </div>

      {/* Contexts List */}
      {contexts.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <Database size={48} className="mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Dashboard Contexts Yet</h3>
          <p className="text-gray-600 mb-4">
            Create your first dashboard context to start chatting with your data
          </p>
          <button
            onClick={onCreateNew}
            className="inline-flex items-center gap-2 py-2 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus size={16} />
            Get Started
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-900">Your Dashboard Contexts</h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {contexts.map((context) => (
              <div
                key={context.id}
                className="bg-white border border-gray-200 rounded-lg p-6 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer relative"
                onClick={() => onSelectContext(context)}
              >
                <div className="flex items-start justify-between mb-3">
                  <h3 className="font-medium text-gray-900 truncate flex-1 mr-2">{context.name}</h3>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowDeleteConfirm(context.id);
                      }}
                      className="p-1 text-red-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                      disabled={deletingContext === context.id}
                      title="Delete dashboard context"
                    >
                      <Trash2 size={14} />
                    </button>
                    <ArrowRight size={16} className="text-gray-400" />
                  </div>
                </div>
                
                {context.description && (
                  <p className="text-sm text-gray-600 mb-3 line-clamp-2">{context.description}</p>
                )}

                <div className="space-y-2 mb-4">
                  {context.text_context && (
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <MessageSquare size={12} />
                      <span>Business context added</span>
                    </div>
                  )}
                  {context.json_context && (
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <Database size={12} />
                      <span>Structured metadata added</span>
                    </div>
                  )}
                  {context.additional_instructions && (
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <MessageSquare size={12} />
                      <span>AI instructions added</span>
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-between text-xs text-gray-400">
                  <div className="flex items-center gap-1">
                    <Calendar size={12} />
                    <span>{formatDate(context.updated_at)}</span>
                  </div>
                  <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                    Start Chat
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center gap-3 mb-4">
              <AlertCircle size={24} className="text-red-500" />
              <h3 className="text-lg font-semibold text-gray-900">Delete Dashboard Context</h3>
            </div>
            <p className="text-gray-600 mb-6">
              Are you sure you want to delete this dashboard context? This action cannot be undone and will also delete all associated chat sessions.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowDeleteConfirm(null)}
                className="px-4 py-2 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                disabled={deletingContext === showDeleteConfirm}
              >
                Cancel
              </button>
              <button
                onClick={() => deleteContext(showDeleteConfirm)}
                disabled={deletingContext === showDeleteConfirm}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
              >
                {deletingContext === showDeleteConfirm ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}