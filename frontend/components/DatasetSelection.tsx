'use client';

import { useState, useEffect } from 'react';
import { Datasource, TableInfo, Dataset, DashboardContext } from '@/types';

interface DatasetSelectionProps {
  datasource: Datasource;
  onDatasetsSelected: (context: DashboardContext) => void;
  onBack: () => void;
  selectedDatasets: string[];
}

export default function DatasetSelection({ 
  datasource, 
  onDatasetsSelected, 
  onBack,
  selectedDatasets 
}: DatasetSelectionProps) {
  const [tables, setTables] = useState<TableInfo[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedTableNames, setSelectedTableNames] = useState<string[]>([]);  // Start with empty selection
  const [textContext, setTextContext] = useState('');
  const [jsonContext, setJsonContext] = useState('');
  const [additionalInstructions, setAdditionalInstructions] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedTable, setExpandedTable] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredTables, setFilteredTables] = useState<TableInfo[]>([]);

  useEffect(() => {
    fetchTables();
    fetchExistingDatasets();
  }, [datasource.id]);

  // Filter tables based on search term
  useEffect(() => {
    if (!searchTerm.trim()) {
      setFilteredTables(tables);
    } else {
      const filtered = tables.filter(table => {
        const matchesName = table.name.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesSchema = table.schema.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesFullName = table.full_name?.toLowerCase().includes(searchTerm.toLowerCase());
        return matchesName || matchesSchema || matchesFullName;
      });
      setFilteredTables(filtered);
    }
  }, [tables, searchTerm]);

  // Initialize with fresh state - avoid prop conflicts
  useEffect(() => {
    setSelectedTableNames([]);
  }, [datasource.id]); // Reset when datasource changes

  const fetchTables = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`/api/v1/datasources/${datasource.id}/tables`, {
        headers: { 'x-user-id': 'user_123' }
      });
      
      if (response.ok) {
        const tablesData = await response.json();
        setTables(tablesData);
        // Initialize filtered tables immediately
        setFilteredTables(tablesData);
      } else {
        setError('Failed to fetch tables from database');
      }
    } catch (error) {
      setError('Failed to connect to database');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchExistingDatasets = async () => {
    // Note: In the new architecture, datasets are created fresh each time
    // We no longer fetch existing datasets from the datasource
    // Instead, we start with empty selection and let users configure their dashboard context
  };

  const toggleTableSelection = (tableFullName: string) => {
    setSelectedTableNames(prev => {
      const isCurrentlySelected = prev.includes(tableFullName);
      if (isCurrentlySelected) {
        return prev.filter(name => name !== tableFullName);
      } else {
        return [...prev, tableFullName];
      }
    });
  };

  const saveDatasets = async () => {
    setIsSaving(true);

    try {
      // Prepare datasets for the dashboard context
      const datasetsToSave = selectedTableNames.map(fullName => {
        const table = tables.find(t => t.full_name === fullName);
        return {
          dashboard_context_id: '', // Will be set by the backend
          table_name: table?.name || '',
          table_schema: table?.schema || '',
          is_enabled: true
        };
      });

      // Generate a name for the dashboard context
      const contextName = `Dashboard - ${datasource.name}`;
      
      // Create dashboard context request
      const dashboardContextRequest = {
        name: contextName,
        description: textContext.trim() || `Dashboard context for ${datasource.name} with ${selectedTableNames.length} tables`,
        datasource_id: datasource.id,
        text_context: textContext.trim() || undefined,
        json_context: jsonContext.trim() || undefined,
        additional_instructions: additionalInstructions.trim() || undefined,
        datasets: datasetsToSave
      };

      console.log('Creating dashboard context with request:', dashboardContextRequest);
      console.log('Number of datasets to save:', datasetsToSave.length);

      const response = await fetch(`/api/v1/dashboard-contexts/`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'x-user-id': 'user_123'
        },
        body: JSON.stringify(dashboardContextRequest)
      });

      if (response.ok) {
        const savedContext = await response.json();
        console.log('Saved context response:', savedContext);
        console.log('Datasets in response:', savedContext.datasets?.length || 0);
        
        // Create local dashboard context with backend ID
        const dashboardContext: DashboardContext = {
          id: savedContext.id,
          selectedTables: selectedTableNames,
          textContext: textContext.trim() || undefined,
          jsonContext: jsonContext.trim() || undefined,
          additionalInstructions: additionalInstructions.trim() || undefined,
        };
        onDatasetsSelected(dashboardContext);
      } else {
        const errorData = await response.text();
        console.error('Failed to create dashboard context:', errorData);
        setError('Failed to save dashboard context');
      }
    } catch (error) {
      console.error('Error creating dashboard context:', error);
      setError('Failed to save dashboard context');
    } finally {
      setIsSaving(false);
    }
  };

  const toggleTableDetails = (tableFullName: string) => {
    setExpandedTable(expandedTable === tableFullName ? null : tableFullName);
  };

  if (isLoading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Discovering tables in your database...</p>
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
          onClick={onBack}
          className="py-2 px-4 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
        >
          Back to Connection
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold mb-2">Dashboard Context</h2>
          <p className="text-gray-600">
            Configure the context for your dashboard by selecting tables and adding additional information from <strong>{datasource.name}</strong>
          </p>
        </div>
        <button
          onClick={onBack}
          className="py-2 px-4 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
        >
          Back
        </button>
      </div>

      {tables.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-600">No tables found in this database.</p>
        </div>
      ) : (
        <>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-blue-800 text-sm">
              <strong>Tip:</strong> Select tables that contain the data you want to analyze. 
              You can always come back and modify your selection later.
            </p>
          </div>

          {/* Search and Table Stats */}
          <div className="space-y-4">
            {/* Search Input */}
            <div>
              <label htmlFor="table-search" className="block text-sm font-medium text-gray-700 mb-2">
                Search Tables and Schemas
              </label>
              <input
                id="table-search"
                type="text"
                placeholder="Search by table name or schema..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* Stats */}
            <div className="flex items-center justify-between text-sm text-gray-600">
              <span>
                {searchTerm ? `${filteredTables.length} of ${tables.length} tables` : `${tables.length} tables found`}
                {searchTerm && ` (searching: "${searchTerm}")`}
              </span>
              <span>{selectedTableNames.length} selected</span>
            </div>

            {/* Scrollable Table List */}
            <div className="max-h-96 overflow-y-auto border rounded-lg bg-gray-50 p-4">
              <div className="space-y-3">
                {filteredTables.map((table, index) => {
              // Create a truly unique key by combining multiple properties
              const uniqueKey = `${table.schema}__${table.name}__${index}`;
              const isSelected = selectedTableNames.includes(table.full_name);
              const isExpanded = expandedTable === table.full_name;

              return (
                <div
                  key={uniqueKey}
                  className={`border rounded-lg transition-colors ${
                    isSelected 
                      ? 'border-blue-300 bg-blue-50' 
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="p-4">
                    <div className="flex items-start space-x-3">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={(e) => {
                          e.stopPropagation();
                          toggleTableSelection(table.full_name);
                        }}
                        className="mt-1 w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      />
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <h4 className="font-medium text-gray-900">{table.name}</h4>
                            <p className="text-sm text-gray-600">
                              Schema: {table.schema}
                              {table.row_count && (
                                <span> • {table.row_count.toLocaleString()} rows</span>
                              )}
                            </p>
                            {table.description && (
                              <p className="text-sm text-gray-500 mt-1">{table.description}</p>
                            )}
                          </div>
                          
                          <button
                            onClick={() => toggleTableDetails(table.full_name)}
                            className="text-blue-600 hover:text-blue-800 text-sm ml-4"
                          >
                            {isExpanded ? 'Hide Details' : 'View Details'}
                          </button>
                        </div>

                        {isExpanded && table.columns.length > 0 && (
                          <div className="mt-4 border-t pt-4">
                            <h5 className="text-sm font-medium text-gray-900 mb-3">
                              Columns ({table.columns.length})
                            </h5>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                              {table.columns.map((column) => (
                                <div key={column.name} className="text-sm">
                                  <div className="flex items-center justify-between">
                                    <span className="font-medium text-gray-900">{column.name}</span>
                                    <span className="text-gray-500 text-xs">{column.data_type}</span>
                                  </div>
                                  {column.description && (
                                    <p className="text-gray-600 text-xs mt-1">{column.description}</p>
                                  )}
                                  {column.sample_values && column.sample_values.length > 0 && (
                                    <p className="text-gray-500 text-xs mt-1">
                                      Sample: {column.sample_values.slice(0, 3).join(', ')}
                                      {column.sample_values.length > 3 && '...'}
                                    </p>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
              </div>
            </div>
          </div>

          {/* Additional Context Section */}
          <div className="border-t pt-6 mt-6">
            <h3 className="text-lg font-medium mb-4">Additional Dashboard Context</h3>
            <p className="text-gray-600 mb-4">
              Provide extra context that will help the AI understand your dashboard and generate better answers.
            </p>
            
            <div className="space-y-4">
              {/* Text Context */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Business Context (Text)
                </label>
                <textarea
                  value={textContext}
                  onChange={(e) => setTextContext(e.target.value)}
                  placeholder="Describe your business context, KPIs, or any relevant information about the data..."
                  rows={3}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              {/* JSON Context */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Structured Context (JSON)
                </label>
                <textarea
                  value={jsonContext}
                  onChange={(e) => setJsonContext(e.target.value)}
                  placeholder={`Example:\n{\n  "metrics": ["revenue", "users", "conversion_rate"],\n  "dimensions": ["date", "region", "product_category"],\n  "filters": ["active_users_only"]\n}`}
                  rows={6}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                />
              </div>

              {/* Additional Instructions */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Additional Instructions
                </label>
                <textarea
                  value={additionalInstructions}
                  onChange={(e) => setAdditionalInstructions(e.target.value)}
                  placeholder="Any specific instructions for how the AI should analyze or present your data..."
                  rows={2}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
          </div>

          <div className="flex gap-4 pt-4">
            <button
              onClick={() => {
                // Select all filtered tables
                const filteredTableNames = filteredTables.map(t => t.full_name);
                const newSelection = [...new Set([...selectedTableNames, ...filteredTableNames])];
                setSelectedTableNames(newSelection);
              }}
              className="py-2 px-4 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              disabled={filteredTables.every(table => selectedTableNames.includes(table.full_name))}
            >
              Select {searchTerm ? 'Filtered' : 'All'} ({filteredTables.length})
            </button>
            
            <button
              onClick={() => {
                // Clear all filtered tables from selection
                const filteredTableNames = filteredTables.map(t => t.full_name);
                const newSelection = selectedTableNames.filter(name => !filteredTableNames.includes(name));
                setSelectedTableNames(newSelection);
              }}
              className="py-2 px-4 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              disabled={!filteredTables.some(table => selectedTableNames.includes(table.full_name))}
            >
              Clear {searchTerm ? 'Filtered' : 'All'}
            </button>

            <div className="flex-1"></div>

            <button
              onClick={saveDatasets}
              disabled={selectedTableNames.length === 0 || isSaving}
              className="py-3 px-6 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSaving ? 'Saving...' : `Continue with ${selectedTableNames.length} Tables`}
            </button>
          </div>
        </>
      )}
    </div>
  );
}