"""
Main orchestrator that ties everything together
"""
import json
import uuid
import asyncio
import logging
from decimal import Decimal
from typing import Optional, AsyncGenerator, Dict, Any
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage

from app.models.chat import ChatResponse
from app.agents.graph import dashboard_chat_graph
from app.agents.types import AgentState
from app.services.postgres_database_service import get_postgres_db_service
from app.models.datasource import ChatMessage

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def serialize_query_result(query_result):
    """Serialize query result to JSON, handling Decimal objects"""
    if not query_result:
        return None
    
    def decimal_serializer(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        raise TypeError
    
    try:
        return json.dumps(query_result, default=decimal_serializer)
    except Exception as e:
        logger.error(f"Failed to serialize query result: {e}")
        return None


class DashboardChatOrchestrator:
    """Main orchestrator for dashboard chat interactions"""
    
    def __init__(self, db_service=None):
        self.graph = dashboard_chat_graph
        self.db_service = db_service
    
    
    async def process_session_message(
        self,
        message: str,
        chat_session_id: str,
        user_id: str,
    ) -> ChatResponse:
        """
        Process a message in the context of a chat session
        """
        db_service = self.db_service
        if not db_service:
            raise ValueError("Database service not provided to orchestrator")
        
        # Get session and dashboard context
        session = await db_service.get_chat_session(chat_session_id, user_id)
        if not session:
            raise ValueError("Chat session not found")
        
        dashboard_context = await db_service.get_dashboard_context(session.dashboard_context_id, user_id)
        if not dashboard_context:
            raise ValueError("Dashboard context not found")
        
        # Get datasource and datasets for context
        from app.services.datasource_service import DatasourceService
        datasource_service = DatasourceService(db_session=db_service.session)
        datasource = await datasource_service.get_datasource(dashboard_context.datasource_id, user_id)
        datasets = await db_service.get_datasets_for_context(dashboard_context.id)
        # Debug column metadata loading
        for i, dataset in enumerate(datasets):
            column_count = len(dataset.columns) if hasattr(dataset, 'columns') and dataset.columns else 0
            print(f"🔍 ORCHESTRATOR: Dataset {i}: {dataset.table_schema}.{dataset.table_name} has {column_count} columns loaded")
        
        # Save user message
        user_message_id = str(uuid.uuid4())
        user_message = ChatMessage(
            id=user_message_id,
            chat_session_id=chat_session_id,
            role="user",
            content=message
        )
        await db_service.save_chat_message(user_message)
        
        # Build state for enhanced graph processing
        state: AgentState = {
            "messages": [HumanMessage(content=message)],
            "user_query": message,
            "user_id": user_id,
            "datasource_id": dashboard_context.datasource_id,
            "dashboard_context": {
                "datasource": datasource,
                "datasets": datasets,
                "text_context": dashboard_context.text_context,
                "json_context": dashboard_context.json_context,
                "additional_instructions": dashboard_context.additional_instructions
            },
        }
        
        config = RunnableConfig(
            metadata={
                "user_id": user_id,
                "chat_session_id": chat_session_id,
                "dashboard_context_id": dashboard_context.id,
            }
        )
        
        try:
            final_state = await self.graph.ainvoke(state, config=config)
            
            # Save assistant message with enhanced data
            assistant_message_id = str(uuid.uuid4())
            
            # Extract enhanced response data
            response_content = final_state.get("final_response", "I couldn't process your request.")
            sql_query = None
            query_result = None
            
            if final_state.get("sql_query_result"):
                sql_result = final_state["sql_query_result"]
                sql_query = sql_result.generated_sql
                
                # Extract column names from first row if available
                columns = list(sql_result.full_results[0].keys()) if sql_result.full_results else []
                
                query_result = {
                    "sql": sql_result.generated_sql,
                    "data": sql_result.full_results,
                    "columns": columns,
                    "row_count": sql_result.row_count,
                    "execution_time_ms": sql_result.execution_time_ms
                }
            
            # Include thinking process in reasoning
            reasoning_content = None
            if final_state.get("thinking_process"):
                thinking_process = final_state["thinking_process"]
                reasoning_content = f"Query Understanding: {thinking_process.query_understanding}\n"
                reasoning_content += f"Decision Rationale: {thinking_process.decision_rationale}\n"
                reasoning_content += f"Execution Summary: {thinking_process.execution_summary}"
            
            assistant_message = ChatMessage(
                id=assistant_message_id,
                chat_session_id=chat_session_id,
                role="assistant",
                content=response_content,
                sql_query=sql_query,
                query_result=serialize_query_result(query_result),
                reasoning=reasoning_content
            )
            await db_service.save_chat_message(assistant_message)
            
            return ChatResponse(
                response=response_content,
                query_result=query_result,
                chat_session_id=chat_session_id,
                message_id=assistant_message_id,
                reasoning=reasoning_content,
            )
            
        except Exception as e:
            # Save error message
            error_message_id = str(uuid.uuid4())
            error_message = ChatMessage(
                id=error_message_id,
                chat_session_id=chat_session_id,
                role="assistant",
                content=f"I encountered an error: {str(e)}",
                reasoning=f"Error: {str(e)}"
            )
            await db_service.save_chat_message(error_message)
            
            return ChatResponse(
                response=f"I encountered an error: {str(e)}",
                query_result=None,
                chat_session_id=chat_session_id,
                message_id=error_message_id,
                reasoning=f"Error: {str(e)}",
            )
    
    async def stream_session_response(
        self,
        message: str,
        chat_session_id: str,
        user_id: str,
    ) -> AsyncGenerator[str, None]:
        """
        Stream response for a session message as Server-Sent Events
        """
        logger.debug(f"Stream function called with message: {message}")
        db_service = self.db_service
        if not db_service:
            raise ValueError("Database service not provided to orchestrator")
        logger.debug("Got PostgreSQL db_service")
        
        # Get session and dashboard context with PostgreSQL
        logger.debug(f"Getting chat session with ID={chat_session_id}, user_id={user_id}")
        try:
            session = await asyncio.wait_for(
                db_service.get_chat_session(chat_session_id, user_id),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            logger.error("Chat session lookup timed out")
            yield f"data: {{\"error\": \"Chat session lookup timed out\", \"final\": true}}\n\n"
            return
        except Exception as e:
            logger.error(f"Chat session lookup failed: {e}")
            yield f"data: {{\"error\": \"Chat session lookup failed: {str(e)}\", \"final\": true}}\n\n"
            return
        if not session:
            logger.debug("Chat session not found")
            yield f"data: {{\"error\": \"Chat session not found\", \"final\": true}}\n\n"
            return
        logger.debug(f"Got session: {session.id}")
        
        logger.debug("Getting dashboard context...")
        try:
            dashboard_context = await asyncio.wait_for(
                db_service.get_dashboard_context(session.dashboard_context_id, user_id),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            logger.error("Dashboard context lookup timed out")
            yield f"data: {{\"error\": \"Dashboard context lookup timed out\", \"final\": true}}\n\n"
            return
        except Exception as e:
            logger.error(f"Dashboard context lookup failed: {e}")
            yield f"data: {{\"error\": \"Dashboard context lookup failed: {str(e)}\", \"final\": true}}\n\n"
            return
        if not dashboard_context:
            logger.debug("Dashboard context not found")
            yield f"data: {{\"error\": \"Dashboard context not found\", \"final\": true}}\n\n"
            return
        logger.debug(f"Got dashboard context: {dashboard_context.id}")
        
        try:
            logger.debug("Getting datasource and datasets...")
            from app.services.datasource_service import DatasourceService
            datasource_service = DatasourceService(db_session=db_service.session)
            datasource = await datasource_service.get_datasource(dashboard_context.datasource_id, user_id)
            logger.debug(f"Got datasource: {datasource.name if datasource else 'None'}")
            datasets = await db_service.get_datasets_for_context(dashboard_context.id)
            logger.debug(f"Got {len(datasets)} datasets")
            # Debug column metadata loading
            for i, dataset in enumerate(datasets):
                column_count = len(dataset.columns) if hasattr(dataset, 'columns') and dataset.columns else 0
                print(f"🔍 ORCHESTRATOR: Dataset {i}: {dataset.table_schema}.{dataset.table_name} has {column_count} columns loaded")
        except Exception as e:
            logger.error(f"Datasource/datasets lookup failed: {e}")
            yield f"data: {{\"error\": \"Datasource lookup failed: {str(e)}\", \"final\": true}}\n\n"
            return
            
        # Save user message
        user_message_id = str(uuid.uuid4())
        user_message = ChatMessage(
            id=user_message_id,
            chat_session_id=chat_session_id,
            role="user",
            content=message
        )
        await db_service.save_chat_message(user_message)
            
        # Build state for enhanced graph processing
        state: AgentState = {
            "messages": [HumanMessage(content=message)],
            "user_query": message,
            "user_id": user_id,
            "datasource_id": dashboard_context.datasource_id,
            "dashboard_context": {
                "datasource": datasource,
                "datasets": datasets,
                "text_context": dashboard_context.text_context,
                "json_context": dashboard_context.json_context,
                "additional_instructions": dashboard_context.additional_instructions
            },
        }
            
        config = RunnableConfig(
            metadata={
                "user_id": user_id,
                "chat_session_id": chat_session_id,
                "dashboard_context_id": dashboard_context.id,
            }
        )
            
        assistant_message_id = str(uuid.uuid4())
        
        # Execute enhanced graph with debugging
        try:
            logger.debug("About to yield first message")
            yield f"data: {{\"status\": \"processing\", \"step\": \"🧠 Starting enhanced analysis\"}}\n\n"
            logger.debug("First message yielded")
            
            try:
                logger.debug(f"About to execute graph with state keys: {list(state.keys())}")
                logger.debug(f"Graph type: {type(self.graph)}")
                # Add 120 second timeout to give graph more time
                final_state = await asyncio.wait_for(
                    self.graph.ainvoke(state, config=config),
                    timeout=120.0
                )
                logger.debug("Graph execution completed successfully")
                logger.debug(f"Final state keys: {list(final_state.keys()) if final_state else 'None'}")
                logger.debug(f"Final response: {final_state.get('final_response', 'NONE')}")
                logger.debug(f"Query result exists: {final_state.get('query_result') is not None}")
                logger.debug(f"SQL query result exists: {final_state.get('sql_query_result') is not None}")
                logger.debug(f"Generated insights exists: {final_state.get('generated_insights') is not None}")
                yield f"data: {{\"status\": \"processing\", \"step\": \"✅ Enhanced analysis complete\"}}\n\n"
            except asyncio.TimeoutError:
                logger.error("Graph execution timed out after 120 seconds")
                yield f"data: {{\"status\": \"error\", \"step\": \"❌ Graph execution timed out after 120 seconds\"}}\n\n"
                # Fallback response  
                final_state = {
                    "final_response": "The enhanced system timed out during execution. This suggests an infinite loop or deadlock in the agent graph. Using fallback response: Your datasource is connected and contains multiple tables for analysis.",
                    "sql_query_result": None,
                    "thinking_process": None
                }
            except Exception as graph_error:
                logger.error(f"Graph execution failed: {graph_error}")
                yield f"data: {{\"status\": \"error\", \"step\": \"❌ Graph execution failed: {str(graph_error)}\"}}\n\n"
                # Fallback response
                final_state = {
                    "final_response": f"Enhanced system encountered an error: {str(graph_error)}. However, I can tell you that your datasource appears to be properly connected with multiple tables available for analysis.",
                    "sql_query_result": None,
                    "thinking_process": None
                }
                
            # Extract enhanced response data
            response_content = final_state.get("final_response", "I couldn't process your request.")
            query_result = None
            sql_query = None
            
            if final_state.get("sql_query_result"):
                sql_result = final_state["sql_query_result"]
                sql_query = sql_result.generated_sql
                
                # Extract column names from first row if available
                columns = list(sql_result.full_results[0].keys()) if sql_result.full_results else []
                
                query_result = {
                    "sql": sql_result.generated_sql,
                    "data": sql_result.full_results,
                    "columns": columns,
                    "row_count": sql_result.row_count,
                    "execution_time_ms": sql_result.execution_time_ms
                }
            
            # Include thinking process in reasoning
            reasoning_content = None
            if final_state.get("thinking_process"):
                thinking_process = final_state["thinking_process"]
                reasoning_content = f"Query Understanding: {thinking_process.query_understanding}\n"
                reasoning_content += f"Decision Rationale: {thinking_process.decision_rationale}\n" 
                reasoning_content += f"Execution Summary: {thinking_process.execution_summary}"
                
            # Save assistant message
            assistant_message = ChatMessage(
                id=assistant_message_id,
                chat_session_id=chat_session_id,
                role="assistant",
                content=response_content,
                sql_query=sql_query,
                query_result=serialize_query_result(query_result),
                reasoning=reasoning_content
            )
            await db_service.save_chat_message(assistant_message)
            
            # Final response
            response_json = {
                "response": response_content,
                "query_result": query_result,
                "message_id": assistant_message_id,
                "reasoning": reasoning_content,
                "final": True
            }
            import json
            yield f"data: {json.dumps(response_json)}\n\n"
                
        except Exception as stream_error:
            yield f"data: {{\"error\": \"Streaming error: {str(stream_error)}\", \"final\": true}}\n\n"
                        
        except Exception as e:
            # Save error message
            error_message_id = str(uuid.uuid4())
            error_message = ChatMessage(
                id=error_message_id,
                chat_session_id=chat_session_id,
                role="assistant",
                content=f"I encountered an error: {str(e)}",
                reasoning=f"Error: {str(e)}"
            )
            await db_service.save_chat_message(error_message)
            
            yield f"data: {{\"error\": \"{str(e)}\", \"message_id\": \"{error_message_id}\", \"final\": true}}\n\n"