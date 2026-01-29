#!/usr/bin/env python3
"""
Script to initialize test user and API key for Jarilo authentication system.
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from orm.db import db_manager
from orm.models import User, APIKey
import uuid


async def create_test_user():
    """Create a test user and API key for development."""
    await db_manager.init_db()

    try:
        async with db_manager.async_session_maker() as session:
            # Create test user
            test_user = User(
                id=str(uuid.uuid4()),
                name="Test User",
                email="test@example.com"
            )
            session.add(test_user)
            await session.commit()
            await session.refresh(test_user)

            print(f"Created test user: {test_user.id} - {test_user.name}")

            # Create API key for the user
            api_key_value = "test-api-key-12345"  # In production, use secure random key
            test_api_key = APIKey(
                id=str(uuid.uuid4()),
                user_id=test_user.id,
                api_key=api_key_value,
                name="Test API Key"
            )
            session.add(test_api_key)
            await session.commit()

            print(f"Created API key: {api_key_value}")
            print(f"User ID: {test_user.id}")
            print("\nUse this API key in Authorization header:")
            print(f"Authorization: Bearer {api_key_value}")

    except Exception as e:
        print(f"Error creating test user: {e}")
        await session.rollback()
    finally:
        await db_manager.close_db()


if __name__ == "__main__":
    asyncio.run(create_test_user())