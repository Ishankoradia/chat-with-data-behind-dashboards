"""
API routes for dashboard context management
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.models.datasource import DashboardContext, Dataset
from app.services.postgres_database_service import PostgresDatabaseService, get_postgres_db_service
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/dashboard-contexts", tags=["dashboard-contexts"])

# Request/Response models
class CreateDashboardContextRequest(BaseModel):
    name: str
    description: Optional[str] = None
    datasource_id: str
    text_context: Optional[str] = None
    json_context: Optional[str] = None
    additional_instructions: Optional[str] = None
    datasets: List[Dataset] = []

class UpdateDashboardContextRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    text_context: Optional[str] = None
    json_context: Optional[str] = None
    additional_instructions: Optional[str] = None
    datasets: Optional[List[Dataset]] = None

class DashboardContextResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str]
    datasource_id: str
    text_context: Optional[str]
    json_context: Optional[str]
    additional_instructions: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    datasets: List[Dataset] = []

# Mock user ID function (replace with proper auth)
async def get_current_user_id() -> str:
    return "user_123"  # Temporary hardcoded user ID

@router.post("/", response_model=DashboardContextResponse)
async def create_dashboard_context(
    request: CreateDashboardContextRequest,
    user_id: str = Depends(get_current_user_id),
    db_session: AsyncSession = Depends(get_db)
):
    """Create a new dashboard context"""
    context_id = str(uuid.uuid4())
    
    context = DashboardContext(
        id=context_id,
        user_id=user_id,
        name=request.name,
        description=request.description,
        datasource_id=request.datasource_id,
        text_context=request.text_context,
        json_context=request.json_context,
        additional_instructions=request.additional_instructions
    )
    
    # Create database service with session
    db_service = await get_postgres_db_service(db_session)
    saved_id = await db_service.save_dashboard_context(context, user_id)
    
    # Save associated datasets with column metadata
    if request.datasets:
        # Fetch column metadata for each dataset
        from app.services.datasource_service import DatasourceService
        datasource_service = DatasourceService(db_session=db_session)
        
        enriched_datasets = []
        for dataset in request.datasets:
            try:
                # Fetch column information for this table
                columns = await datasource_service.get_table_columns(
                    request.datasource_id, user_id, dataset.table_schema, dataset.table_name
                )
                # Remove sample values to save storage space
                for col in columns:
                    col.sample_values = None
                dataset.columns = columns
                print(f"✅ Fetched {len(columns)} columns for {dataset.table_schema}.{dataset.table_name}")
            except Exception as e:
                print(f"⚠️ Failed to fetch columns for {dataset.table_schema}.{dataset.table_name}: {e}")
                dataset.columns = []
            
            enriched_datasets.append(dataset)
        
        await db_service.save_datasets_for_context(saved_id, enriched_datasets)
    
    # Return the created context with datasets
    saved_context = await db_service.get_dashboard_context(saved_id, user_id)
    datasets = await db_service.get_datasets_for_context(saved_id)
    
    return DashboardContextResponse(
        id=saved_context.id,
        user_id=saved_context.user_id,
        name=saved_context.name,
        description=saved_context.description,
        datasource_id=saved_context.datasource_id,
        text_context=saved_context.text_context,
        json_context=saved_context.json_context,
        additional_instructions=saved_context.additional_instructions,
        created_at=str(saved_context.created_at) if saved_context.created_at else None,
        updated_at=str(saved_context.updated_at) if saved_context.updated_at else None,
        datasets=datasets
    )

@router.get("/", response_model=List[DashboardContextResponse])
async def list_dashboard_contexts(
    user_id: str = Depends(get_current_user_id),
    db_session: AsyncSession = Depends(get_db)
):
    """List all dashboard contexts for the current user"""
    db_service = await get_postgres_db_service(db_session)
    contexts = await db_service.list_dashboard_contexts(user_id)
    
    result = []
    for context in contexts:
        datasets = await db_service.get_datasets_for_context(context.id)
        result.append(DashboardContextResponse(
            id=context.id,
            user_id=context.user_id,
            name=context.name,
            description=context.description,
            datasource_id=context.datasource_id,
            text_context=context.text_context,
            json_context=context.json_context,
            additional_instructions=context.additional_instructions,
            created_at=str(context.created_at) if context.created_at else None,
            updated_at=str(context.updated_at) if context.updated_at else None,
            datasets=datasets
        ))
    
    return result

@router.get("/{context_id}", response_model=DashboardContextResponse)
async def get_dashboard_context(
    context_id: str,
    user_id: str = Depends(get_current_user_id),
    db_session: AsyncSession = Depends(get_db)
):
    """Get a specific dashboard context"""
    db_service = await get_postgres_db_service(db_session)
    context = await db_service.get_dashboard_context(context_id, user_id)
    
    if not context:
        raise HTTPException(status_code=404, detail="Dashboard context not found")
    
    datasets = await db_service.get_datasets_for_context(context_id)
    
    return DashboardContextResponse(
        id=context.id,
        user_id=context.user_id,
        name=context.name,
        description=context.description,
        datasource_id=context.datasource_id,
        text_context=context.text_context,
        json_context=context.json_context,
        additional_instructions=context.additional_instructions,
        created_at=str(context.created_at) if context.created_at else None,
        updated_at=str(context.updated_at) if context.updated_at else None,
        datasets=datasets
    )

@router.put("/{context_id}", response_model=DashboardContextResponse)
async def update_dashboard_context(
    context_id: str,
    request: UpdateDashboardContextRequest,
    user_id: str = Depends(get_current_user_id),
    db_session: AsyncSession = Depends(get_db)
):
    """Update an existing dashboard context"""
    # db_service is now injected via dependency
    
    db_service = await get_postgres_db_service(db_session)
    # Get existing context
    existing_context = await db_service.get_dashboard_context(context_id, user_id)
    if not existing_context:
        raise HTTPException(status_code=404, detail="Dashboard context not found")
    
    # Update fields
    updated_context = DashboardContext(
        id=context_id,
        user_id=user_id,
        name=request.name if request.name is not None else existing_context.name,
        description=request.description if request.description is not None else existing_context.description,
        datasource_id=existing_context.datasource_id,  # Don't allow changing datasource
        text_context=request.text_context if request.text_context is not None else existing_context.text_context,
        json_context=request.json_context if request.json_context is not None else existing_context.json_context,
        additional_instructions=request.additional_instructions if request.additional_instructions is not None else existing_context.additional_instructions
    )
    
    await db_service.save_dashboard_context(updated_context, user_id)
    
    # Update datasets if provided
    if request.datasets is not None:
        # Fetch column metadata for each dataset
        from app.services.datasource_service import DatasourceService
        datasource_service = DatasourceService(db_session=db_session)
        
        enriched_datasets = []
        for dataset in request.datasets:
            try:
                # Fetch column information for this table
                columns = await datasource_service.get_table_columns(
                    existing_context.datasource_id, user_id, dataset.table_schema, dataset.table_name
                )
                # Remove sample values to save storage space
                for col in columns:
                    col.sample_values = None
                dataset.columns = columns
                print(f"✅ Updated: Fetched {len(columns)} columns for {dataset.table_schema}.{dataset.table_name}")
            except Exception as e:
                print(f"⚠️ Update: Failed to fetch columns for {dataset.table_schema}.{dataset.table_name}: {e}")
                dataset.columns = []
            
            enriched_datasets.append(dataset)
        
        await db_service.save_datasets_for_context(context_id, enriched_datasets)
    
    # Return updated context
    saved_context = await db_service.get_dashboard_context(context_id, user_id)
    datasets = await db_service.get_datasets_for_context(context_id)
    
    return DashboardContextResponse(
        id=saved_context.id,
        user_id=saved_context.user_id,
        name=saved_context.name,
        description=saved_context.description,
        datasource_id=saved_context.datasource_id,
        text_context=saved_context.text_context,
        json_context=saved_context.json_context,
        additional_instructions=saved_context.additional_instructions,
        created_at=str(saved_context.created_at) if saved_context.created_at else None,
        updated_at=str(saved_context.updated_at) if saved_context.updated_at else None,
        datasets=datasets
    )

@router.delete("/{context_id}")
async def delete_dashboard_context(
    context_id: str,
    user_id: str = Depends(get_current_user_id),
    db_session: AsyncSession = Depends(get_db)
):
    """Delete a dashboard context and all related data"""
    db_service = await get_postgres_db_service(db_session)
    
    deleted = await db_service.delete_dashboard_context(context_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Dashboard context not found")
    
    return {"message": "Dashboard context deleted successfully"}