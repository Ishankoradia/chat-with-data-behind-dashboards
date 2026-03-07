'use client';

import { useState, useEffect } from 'react';
import DatasourceSetup from '@/components/DatasourceSetup';
import DatasetSelection from '@/components/DatasetSelection';
import ChatInterface from '@/components/ChatInterface';
import DashboardContextList from '@/components/DashboardContextList';
import { Datasource, DashboardContext } from '@/types';

type Step = 'landing' | 'datasource' | 'datasets' | 'chat';

interface FullDashboardContext extends DashboardContext {
  datasource_id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  text_context?: string;
  json_context?: string;
  additional_instructions?: string;
}

export default function Home() {
  const [currentStep, setCurrentStep] = useState<Step>('landing');
  const [selectedDatasource, setSelectedDatasource] = useState<Datasource | null>(null);
  const [dashboardContext, setDashboardContext] = useState<DashboardContext | null>(null);
  const [selectedFullContext, setSelectedFullContext] = useState<FullDashboardContext | null>(null);

  // Load saved state from localStorage on initial load
  useEffect(() => {
    const savedDatasource = localStorage.getItem('selectedDatasource');
    const savedContext = localStorage.getItem('dashboardContext');
    
    // Only auto-navigate if we have complete saved state
    if (savedDatasource && savedContext) {
      const parsedContext = JSON.parse(savedContext);
      if (parsedContext.id) {
        // We have a complete saved context, go directly to chat
        setSelectedDatasource(JSON.parse(savedDatasource));
        setDashboardContext(parsedContext);
        setCurrentStep('chat');
        return;
      }
    }
    
    // Otherwise, start at the landing page
    setCurrentStep('landing');
  }, []);

  const handleDatasourceSelected = (datasource: Datasource) => {
    setSelectedDatasource(datasource);
    localStorage.setItem('selectedDatasource', JSON.stringify(datasource));
    setCurrentStep('datasets');
  };

  const handleDashboardContextSelected = (context: DashboardContext) => {
    setDashboardContext(context);
    localStorage.setItem('dashboardContext', JSON.stringify(context));
    setCurrentStep('chat');
  };

  const handleExistingContextSelected = async (context: FullDashboardContext) => {
    // Fetch the datasource for this context
    try {
      const response = await fetch(`/api/v1/datasources`, {
        headers: { 'x-user-id': 'user_123' }
      });
      if (response.ok) {
        const datasources = await response.json();
        const datasource = datasources.find((ds: Datasource) => ds.id === context.datasource_id);
        if (datasource) {
          setSelectedDatasource(datasource);
          setDashboardContext({
            id: context.id,
            selectedTables: [], // We'll load this from the backend context
            textContext: context.text_context,
            jsonContext: context.json_context,
            additionalInstructions: context.additional_instructions,
          });
          setSelectedFullContext(context);
          
          // Save to localStorage
          localStorage.setItem('selectedDatasource', JSON.stringify(datasource));
          localStorage.setItem('dashboardContext', JSON.stringify({
            id: context.id,
            selectedTables: [],
            textContext: context.text_context,
            jsonContext: context.json_context,
            additionalInstructions: context.additional_instructions,
          }));
          
          setCurrentStep('chat');
        }
      }
    } catch (error) {
      console.error('Error loading datasource for context:', error);
    }
  };

  const handleCreateNewContext = () => {
    setCurrentStep('datasource');
  };

  const resetToStart = () => {
    setCurrentStep('landing');
    setSelectedDatasource(null);
    setDashboardContext(null);
    setSelectedFullContext(null);
    localStorage.removeItem('selectedDatasource');
    localStorage.removeItem('dashboardContext');
  };

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          {/* Landing Page */}
          {currentStep === 'landing' && (
            <DashboardContextList
              onSelectContext={handleExistingContextSelected}
              onCreateNew={handleCreateNewContext}
            />
          )}

          {/* Create New Flow */}
          {currentStep !== 'landing' && (
            <>
              <header className="text-center mb-8">
                <h1 className="text-4xl font-bold text-gray-900 mb-4">
                  Create Dashboard Context
                </h1>
                <p className="text-lg text-gray-600 mb-6">
                  Set up a new dashboard context to chat with your data
                </p>
                
                {/* Progress Steps */}
                <div className="flex justify-center items-center space-x-4 mb-8">
                  <div className={`flex items-center ${currentStep === 'datasource' ? 'text-blue-600' : currentStep === 'datasets' || currentStep === 'chat' ? 'text-green-600' : 'text-gray-400'}`}>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${currentStep === 'datasource' ? 'bg-blue-100' : currentStep === 'datasets' || currentStep === 'chat' ? 'bg-green-100' : 'bg-gray-100'}`}>
                      1
                    </div>
                    <span className="ml-2 text-sm font-medium">Connect Database</span>
                  </div>
                  
                  <div className={`w-8 h-1 ${currentStep === 'datasets' || currentStep === 'chat' ? 'bg-green-200' : 'bg-gray-200'}`}></div>
                  
                  <div className={`flex items-center ${currentStep === 'datasets' ? 'text-blue-600' : currentStep === 'chat' ? 'text-green-600' : 'text-gray-400'}`}>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${currentStep === 'datasets' ? 'bg-blue-100' : currentStep === 'chat' ? 'bg-green-100' : 'bg-gray-100'}`}>
                      2
                    </div>
                    <span className="ml-2 text-sm font-medium">Dashboard Context</span>
                  </div>
                  
                  <div className={`w-8 h-1 ${currentStep === 'chat' ? 'bg-green-200' : 'bg-gray-200'}`}></div>
                  
                  <div className={`flex items-center ${currentStep === 'chat' ? 'text-blue-600' : 'text-gray-400'}`}>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${currentStep === 'chat' ? 'bg-blue-100' : 'bg-gray-100'}`}>
                      3
                    </div>
                    <span className="ml-2 text-sm font-medium">Start Chatting</span>
                  </div>
                </div>
              </header>

              <div className="bg-white rounded-lg shadow-sm border p-8">
                {currentStep === 'datasource' && (
                  <DatasourceSetup 
                    onDatasourceSelected={handleDatasourceSelected}
                    existingDatasource={selectedDatasource}
                  />
                )}
                
                {currentStep === 'datasets' && selectedDatasource && (
                  <DatasetSelection
                    datasource={selectedDatasource}
                    onDatasetsSelected={handleDashboardContextSelected}
                    onBack={() => setCurrentStep('datasource')}
                    selectedDatasets={dashboardContext?.selectedTables || []}
                  />
                )}
                
                {currentStep === 'chat' && selectedDatasource && (
                  <div className="space-y-6">
                    {/* Current Setup Summary */}
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h3 className="font-medium mb-2">Current Setup:</h3>
                      <div className="text-sm text-gray-600 space-y-1">
                        <p><strong>Database:</strong> {selectedDatasource.name} ({selectedDatasource.database})</p>
                        <p><strong>Tables:</strong> {dashboardContext?.selectedTables.length || 0} selected</p>
                        {dashboardContext?.textContext && (
                          <p><strong>Business Context:</strong> Added</p>
                        )}
                        {dashboardContext?.jsonContext && (
                          <p><strong>Structured Context:</strong> Added</p>
                        )}
                        {dashboardContext?.additionalInstructions && (
                          <p><strong>Additional Instructions:</strong> Added</p>
                        )}
                        <div className="flex gap-2 mt-2">
                          <button
                            onClick={() => setCurrentStep('datasets')}
                            className="text-blue-600 hover:text-blue-800 text-sm"
                          >
                            Change Context
                          </button>
                          <button
                            onClick={resetToStart}
                            className="text-red-600 hover:text-red-800 text-sm"
                          >
                            Back to Home
                          </button>
                        </div>
                      </div>
                    </div>
                    
                    <ChatInterface 
                      dashboardContextId={dashboardContext?.id || ''}
                      disabled={!dashboardContext?.selectedTables.length || !dashboardContext?.id}
                    />
                  </div>
                )}
                
                {/* Back to Home Button - Show on non-landing steps */}
                {currentStep !== 'landing' && currentStep !== 'chat' && (
                  <div className="text-center mt-6">
                    <button
                      onClick={resetToStart}
                      className="text-gray-600 hover:text-gray-800 text-sm"
                    >
                      ← Back to Dashboard Contexts
                    </button>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </main>
  );
}