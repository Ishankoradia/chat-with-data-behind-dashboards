'use client';

import { useState, useEffect } from 'react';
import { Dashboard } from '@/types';

interface DashboardSelectorProps {
  selectedDashboard: string;
  onSelectDashboard: (dashboardId: string) => void;
}

// Mock dashboards - replace with actual API call
const mockDashboards: Dashboard[] = [
  {
    id: 'dash_1',
    name: 'Sales Performance',
    description: 'Track revenue, deals, and sales metrics',
    metrics: ['revenue', 'sales_count', 'avg_order_value', 'conversion_rate'],
    dimensions: ['month', 'product_name', 'customer_segment', 'region'],
    widgets: [
      { id: '1', type: 'metric', title: 'Total Revenue', config: { field: 'revenue' } },
      { id: '2', type: 'chart', title: 'Revenue Trend', config: { x: 'month', y: 'revenue' } },
    ],
  },
  {
    id: 'dash_2',
    name: 'Marketing Analytics',
    description: 'Campaign performance and ROI tracking',
    metrics: ['roi', 'cpc', 'impressions', 'clicks', 'conversions'],
    dimensions: ['channel', 'campaign_type', 'audience_segment'],
    widgets: [
      { id: '3', type: 'metric', title: 'Campaign ROI', config: { field: 'roi' } },
      { id: '4', type: 'chart', title: 'Clicks by Channel', config: { x: 'channel', y: 'clicks' } },
    ],
  },
];

export default function DashboardSelector({
  selectedDashboard,
  onSelectDashboard,
}: DashboardSelectorProps) {
  const [dashboards, setDashboards] = useState<Dashboard[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate loading dashboards
    const timer = setTimeout(() => {
      setDashboards(mockDashboards);
      setLoading(false);
    }, 500);

    return () => clearTimeout(timer);
  }, []);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h2 className="text-lg font-semibold mb-4">Select Dashboard</h2>
        <div className="space-y-3">
          {[1, 2].map((i) => (
            <div key={i} className="animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <h2 className="text-lg font-semibold mb-4">Select Dashboard</h2>
      
      <div className="space-y-3">
        {dashboards.map((dashboard) => (
          <button
            key={dashboard.id}
            onClick={() => onSelectDashboard(dashboard.id)}
            className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
              selectedDashboard === dashboard.id
                ? 'border-primary bg-primary/5'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <h3 className="font-medium text-sm mb-1">{dashboard.name}</h3>
            <p className="text-xs text-gray-600 mb-3">{dashboard.description}</p>
            
            <div className="space-y-2">
              <div>
                <span className="text-xs font-medium text-gray-500">Metrics:</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {dashboard.metrics.slice(0, 3).map((metric) => (
                    <span
                      key={metric}
                      className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded"
                    >
                      {metric}
                    </span>
                  ))}
                  {dashboard.metrics.length > 3 && (
                    <span className="text-xs text-gray-500">
                      +{dashboard.metrics.length - 3} more
                    </span>
                  )}
                </div>
              </div>
              
              <div>
                <span className="text-xs font-medium text-gray-500">Dimensions:</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {dashboard.dimensions.slice(0, 3).map((dimension) => (
                    <span
                      key={dimension}
                      className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded"
                    >
                      {dimension}
                    </span>
                  ))}
                  {dashboard.dimensions.length > 3 && (
                    <span className="text-xs text-gray-500">
                      +{dashboard.dimensions.length - 3} more
                    </span>
                  )}
                </div>
              </div>
            </div>
          </button>
        ))}
      </div>

      {selectedDashboard && (
        <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-sm text-green-800">
            Dashboard selected! You can now start asking questions about your data.
          </p>
        </div>
      )}
    </div>
  );
}