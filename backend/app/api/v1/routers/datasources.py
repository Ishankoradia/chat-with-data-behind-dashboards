"""
Datasource management API endpoints
"""
from typing import List
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.datasource import (
    DatasourceConnection, 
    TableInfo
)
from app.services.datasource_service import DatasourceService
from app.core.database import get_db

router = APIRouter()


class TestConnectionRequest(BaseModel):
    """Request model for testing database connection"""
    host: str
    port: int = 5432
    database: str
    username: str
    password: str
    ssl_mode: str = "prefer"


class SaveDatasourceRequest(BaseModel):
    """Request model for saving datasource"""
    name: str
    host: str
    port: int = 5432
    database: str
    username: str
    password: str
    ssl_mode: str = "prefer"




@router.post("/test-connection")
async def test_connection(
    request: TestConnectionRequest,
    x_user_id: str = Header(default="user_123"),
    db: AsyncSession = Depends(get_db)
):
    """Test database connection before saving"""
    connection = DatasourceConnection(
        name="test",  # Temporary name for testing
        host=request.host,
        port=request.port,
        database=request.database,
        username=request.username,
        password=request.password,
        ssl_mode=request.ssl_mode,
    )
    
    service = DatasourceService(db_session=db)
    result = await service.test_connection(connection)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.post("/datasources")
async def create_datasource(
    request: SaveDatasourceRequest,
    x_user_id: str = Header(default="user_123"),
    db: AsyncSession = Depends(get_db)
):
    """Save a new datasource"""
    connection = DatasourceConnection(
        name=request.name,
        host=request.host,
        port=request.port,
        database=request.database,
        username=request.username,
        password=request.password,
        ssl_mode=request.ssl_mode,
    )
    
    service = DatasourceService(db_session=db)
    
    # Test connection first
    test_result = await service.test_connection(connection)
    if not test_result["success"]:
        raise HTTPException(status_code=400, detail=f"Connection test failed: {test_result['message']}")
    
    # Save if successful
    datasource_id = await service.save_datasource(connection, x_user_id)
    
    return {
        "id": datasource_id,
        "name": connection.name,
        "message": "Datasource created successfully"
    }


@router.get("/datasources")
async def list_datasources(
    x_user_id: str = Header(default="user_123"),
    db: AsyncSession = Depends(get_db)
) -> List[dict]:
    """List user's datasources"""
    service = DatasourceService(db_session=db)
    datasources = await service.list_user_datasources(x_user_id)
    
    # Return safe info (no passwords)
    return [
        {
            "id": ds.id,
            "name": ds.name,
            "type": ds.type,
            "host": ds.host,
            "port": ds.port,
            "database": ds.database,
            "username": ds.username,
        }
        for ds in datasources
    ]


@router.get("/datasources/{datasource_id}/tables")
async def discover_tables(
    datasource_id: str,
    x_user_id: str = Header(default="user_123"),
    db: AsyncSession = Depends(get_db)
) -> List[TableInfo]:
    """Discover tables in a datasource"""
    service = DatasourceService(db_session=db)
    
    try:
        tables = await service.discover_tables(datasource_id, x_user_id)
        return tables
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to discover tables: {str(e)}")


