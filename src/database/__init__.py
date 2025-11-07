"""
Database package for Supabase integration.

Exports:
- SupabaseClient: Main database client
- Database models (Pydantic)
- Query functions
"""

from .supabase_client import SupabaseClient, get_supabase_client

__all__ = [
    "SupabaseClient",
    "get_supabase_client",
]
