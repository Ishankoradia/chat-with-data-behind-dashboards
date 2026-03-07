#!/usr/bin/env python3
"""
Initialize PostgreSQL database tables for Dashboard Chat
Run this script to create the required tables
"""
import asyncio
import os
import sys

# Add the backend directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.postgres_database_service import PostgresDatabaseService
from app.core.config import settings

async def init_database():
    """Initialize the database with required tables"""
    print(f"Initializing PostgreSQL database...")
    print(f"Database URL: {settings.DATABASE_URL}")
    
    try:
        # Create database service
        db_service = PostgresDatabaseService()
        
        # Initialize tables
        await db_service.init_database()
        
        print("✅ Database tables created successfully!")
        print("Tables created:")
        print("  - chat_datasources")
        print("  - chat_dashboard_contexts") 
        print("  - chat_sessions")
        print("  - chat_messages")
        print("  - chat_datasets")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        print(f"Make sure PostgreSQL is running and the credentials in .env are correct")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(init_database())
    if not success:
        sys.exit(1)