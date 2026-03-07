"""
DBT tool for interacting with semantic layer
"""
from typing import Optional, Dict, Any, List
from app.services.dbt_service import DBTService
# Removed DashboardContext import - using Dict[str, Any] instead


class DBTTool:
    """Tool for DBT semantic layer operations"""
    
    def __init__(self):
        self.dbt_service = DBTService()
    
    async def query_metrics(
        self,
        query: str,
        available_metrics: List[Dict[str, Any]],
        dashboard_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Query DBT semantic layer for metrics
        """
        return await self.dbt_service.query_metrics(
            query=query,
            available_metrics=available_metrics,
            dashboard_context=dashboard_context,
        )
    
    async def query_dimensions(
        self,
        query: str,
        available_dimensions: List[Dict[str, Any]],
        dashboard_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Query DBT semantic layer for dimensions
        """
        return await self.dbt_service.query_dimensions(
            query=query,
            available_dimensions=available_dimensions,
            dashboard_context=dashboard_context,
        )
    
    async def get_available_metrics(self, dashboard_id: str) -> List[Dict[str, Any]]:
        """
        Get all metrics available for a dashboard
        """
        metrics = await self.dbt_service.get_metrics_for_dashboard(dashboard_id)
        return metrics or []
    
    async def get_available_dimensions(self, dashboard_id: str) -> List[Dict[str, Any]]:
        """
        Get all dimensions available for a dashboard
        """
        dimensions = await self.dbt_service.get_dimensions_for_dashboard(dashboard_id)
        return dimensions or []