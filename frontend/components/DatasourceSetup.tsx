'use client';

import { useState, useEffect } from 'react';
import { Datasource, ConnectionTestRequest, SaveDatasourceRequest } from '@/types';

interface DatasourceSetupProps {
  onDatasourceSelected: (datasource: Datasource) => void;
  existingDatasource?: Datasource | null;
}

export default function DatasourceSetup({ onDatasourceSelected, existingDatasource }: DatasourceSetupProps) {
  const [formData, setFormData] = useState({
    name: '',
    host: 'localhost',
    port: 5432,
    database: '',
    username: '',
    password: '',
    ssl_mode: 'prefer'
  });
  
  const [isTestingConnection, setIsTestingConnection] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [existingDatasources, setExistingDatasources] = useState<Datasource[]>([]);

  useEffect(() => {
    fetchExistingDatasources();
  }, []);

  const fetchExistingDatasources = async () => {
    try {
      const response = await fetch('/api/v1/datasources', {
        headers: { 'x-user-id': 'user_123' }
      });
      if (response.ok) {
        const datasources = await response.json();
        setExistingDatasources(datasources);
      }
    } catch (error) {
      console.error('Failed to fetch datasources:', error);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'port' ? parseInt(value) || 5432 : value
    }));
    setTestResult(null);
  };

  const testConnection = async () => {
    setIsTestingConnection(true);
    setTestResult(null);

    try {
      const testData: ConnectionTestRequest = {
        host: formData.host,
        port: formData.port,
        database: formData.database,
        username: formData.username,
        password: formData.password,
        ssl_mode: formData.ssl_mode
      };

      const response = await fetch('/api/v1/test-connection', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'x-user-id': 'user_123'
        },
        body: JSON.stringify(testData)
      });

      const result = await response.json();
      
      if (response.ok) {
        setTestResult({ success: true, message: 'Connection successful!' });
      } else {
        setTestResult({ success: false, message: result.detail || 'Connection failed' });
      }
    } catch (error) {
      setTestResult({ success: false, message: 'Failed to test connection' });
    } finally {
      setIsTestingConnection(false);
    }
  };

  const saveDatasource = async () => {
    setIsSaving(true);

    try {
      const saveData: SaveDatasourceRequest = {
        name: formData.name,
        host: formData.host,
        port: formData.port,
        database: formData.database,
        username: formData.username,
        password: formData.password,
        ssl_mode: formData.ssl_mode
      };

      const response = await fetch('/api/v1/datasources', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'x-user-id': 'user_123'
        },
        body: JSON.stringify(saveData)
      });

      if (response.ok) {
        const datasource = await response.json();
        onDatasourceSelected(datasource);
      } else {
        const error = await response.json();
        setTestResult({ success: false, message: error.detail || 'Failed to save datasource' });
      }
    } catch (error) {
      setTestResult({ success: false, message: 'Failed to save datasource' });
    } finally {
      setIsSaving(false);
    }
  };

  const selectExistingDatasource = (datasource: Datasource) => {
    onDatasourceSelected(datasource);
  };

  const canTestConnection = formData.host && formData.database && formData.username && formData.password;
  const canSave = testResult?.success && formData.name;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold mb-4">Connect to Database</h2>
        <p className="text-gray-600 mb-6">
          Enter your PostgreSQL database connection details to get started.
        </p>
      </div>

      {/* Existing Datasources */}
      {existingDatasources.length > 0 && (
        <div>
          <h3 className="text-lg font-medium mb-3">Use Existing Connection</h3>
          <div className="grid gap-3 mb-6">
            {existingDatasources.map((datasource) => (
              <button
                key={datasource.id}
                onClick={() => selectExistingDatasource(datasource)}
                className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors text-left"
              >
                <div>
                  <h4 className="font-medium">{datasource.name}</h4>
                  <p className="text-sm text-gray-600">
                    {datasource.host}:{datasource.port}/{datasource.database}
                  </p>
                </div>
                <div className="text-blue-600">→</div>
              </button>
            ))}
          </div>
          <div className="text-center text-gray-500 mb-6">or create a new connection</div>
        </div>
      )}

      {/* New Connection Form */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Connection Name *
          </label>
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleInputChange}
            placeholder="My Database"
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Host *
          </label>
          <input
            type="text"
            name="host"
            value={formData.host}
            onChange={handleInputChange}
            placeholder="localhost"
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Port *
          </label>
          <input
            type="number"
            name="port"
            value={formData.port}
            onChange={handleInputChange}
            placeholder="5432"
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Database Name *
          </label>
          <input
            type="text"
            name="database"
            value={formData.database}
            onChange={handleInputChange}
            placeholder="mydb"
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Username *
          </label>
          <input
            type="text"
            name="username"
            value={formData.username}
            onChange={handleInputChange}
            placeholder="postgres"
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Password *
          </label>
          <input
            type="password"
            name="password"
            value={formData.password}
            onChange={handleInputChange}
            placeholder="••••••••"
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            required
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          SSL Mode
        </label>
        <select
          name="ssl_mode"
          value={formData.ssl_mode}
          onChange={handleInputChange}
          className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="disable">Disable</option>
          <option value="allow">Allow</option>
          <option value="prefer">Prefer</option>
          <option value="require">Require</option>
          <option value="verify-ca">Verify CA</option>
          <option value="verify-full">Verify Full</option>
        </select>
      </div>

      {/* Test Result */}
      {testResult && (
        <div className={`p-4 rounded-lg ${testResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
          <p className={testResult.success ? 'text-green-800' : 'text-red-800'}>
            {testResult.message}
          </p>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-4">
        <button
          onClick={testConnection}
          disabled={!canTestConnection || isTestingConnection}
          className="flex-1 py-3 px-6 border border-blue-600 text-blue-600 font-medium rounded-lg hover:bg-blue-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isTestingConnection ? 'Testing Connection...' : 'Test Connection'}
        </button>

        <button
          onClick={saveDatasource}
          disabled={!canSave || isSaving}
          className="flex-1 py-3 px-6 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isSaving ? 'Saving...' : 'Save & Continue'}
        </button>
      </div>
    </div>
  );
}