"""
DBT Semantic Layer integration service
"""
import httpx
from typing import List, Dict, Any, Optional
from app.core.config import settings
# Removed DashboardContext import - using Dict[str, Any] instead


class DBTService:
    """Service for interacting with DBT Semantic Layer"""
    
    def __init__(self):
        self.base_url = settings.DBT_SEMANTIC_LAYER_URL
        self.api_key = settings.DBT_API_KEY
        self.environment_id = settings.DBT_ENVIRONMENT_ID
        
    async def get_metrics_for_dashboard(self, dashboard_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get relevant DBT metrics for a specific dashboard
        """
        if not self.base_url:
            return None
            
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
                
                # Get all available metrics
                response = await client.get(
                    f"{self.base_url}/api/graphql/",
                    headers=headers,
                    json={
                        "query": """
                        query GetMetrics($environmentId: BigInt!) {
                            metrics(environmentId: $environmentId) {
                                name
                                description
                                type
                                label
                                dimensions
                                requiredDimensions
                            }
                        }
                        """,
                        "variables": {"environmentId": int(self.environment_id)},
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    metrics = data.get("data", {}).get("metrics", [])
                    
                    # Filter metrics relevant to this dashboard
                    # This is where you'd implement logic to match dashboard context
                    return metrics[:10]  # Return first 10 for now
                    
        except Exception as e:
            print(f"Error fetching DBT metrics: {e}")
            
        return None
    
    async def get_dimensions_for_dashboard(self, dashboard_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get relevant DBT dimensions for a specific dashboard
        """
        if not self.base_url:
            return None
            
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
                
                response = await client.get(
                    f"{self.base_url}/api/graphql/",
                    headers=headers,
                    json={
                        "query": """
                        query GetDimensions($environmentId: BigInt!) {
                            dimensions(environmentId: $environmentId) {
                                name
                                description
                                type
                                label
                            }
                        }
                        """,
                        "variables": {"environmentId": int(self.environment_id)},
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    dimensions = data.get("data", {}).get("dimensions", [])
                    return dimensions[:10]  # Return first 10 for now
                    
        except Exception as e:
            print(f"Error fetching DBT dimensions: {e}")
            
        return None
    
    async def query_metrics(
        self, 
        query: str, 
        available_metrics: List[Dict[str, Any]], 
        dashboard_context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Query DBT semantic layer for metric data
        """
        if not self.base_url:
            return None
            
        try:
            # This is a simplified implementation
            # In practice, you'd need to:
            # 1. Parse the natural language query
            # 2. Map it to appropriate DBT metrics and dimensions
            # 3. Construct the semantic layer query
            # 4. Execute and return results
            
            # For now, return a mock response
            return {
                "sql": "SELECT metric_value FROM semantic_layer WHERE condition = 'example'",
                "data": [
                    {"metric": "revenue", "value": 150000, "period": "2024-03"},
                    {"metric": "revenue", "value": 145000, "period": "2024-02"},
                ],
                "columns": ["metric", "value", "period"],
                "row_count": 2,
                "execution_time_ms": 125,
            }
            
        except Exception as e:
            print(f"Error querying DBT metrics: {e}")
            return None
    
    async def query_dimensions(
        self, 
        query: str, 
        available_dimensions: List[Dict[str, Any]], 
        dashboard_context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Query DBT semantic layer for dimension data
        """
        if not self.base_url:
            return None
            
        try:
            # Similar to query_metrics, this would be more complex in practice
            return {
                "sql": "SELECT dimension_value, count FROM semantic_layer GROUP BY dimension_value",
                "data": [
                    {"category": "Product A", "count": 25, "percentage": 45.5},
                    {"category": "Product B", "count": 18, "percentage": 32.7},
                    {"category": "Product C", "count": 12, "percentage": 21.8},
                ],
                "columns": ["category", "count", "percentage"],
                "row_count": 3,
                "execution_time_ms": 89,
            }
            
        except Exception as e:
            print(f"Error querying DBT dimensions: {e}")
            return None
    
    async def validate_connection(self) -> bool:
        """
        Test connection to DBT semantic layer
        """
        if not self.base_url:
            return False
            
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
                
                response = await client.get(
                    f"{self.base_url}/api/graphql/",
                    headers=headers,
                    json={
                        "query": "query { __typename }",
                    }
                )
                
                return response.status_code == 200
                
        except Exception:
            return False