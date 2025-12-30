"""
Supabase client module for database operations.
Provides a singleton Supabase client instance.
"""

from supabase import create_client, Client
from config import settings
import logging

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Singleton Supabase client manager."""

    _instance: Client = None

    @classmethod
    def get_client(cls) -> Client:
        """
        Get or create Supabase client instance.

        Returns:
            Client: Supabase client instance
        """
        if cls._instance is None:
            try:
                cls._instance = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_KEY
                )
                logger.info("Supabase client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                raise

        return cls._instance


# Convenience function to get client
def get_supabase() -> Client:
    """
    Get Supabase client instance.

    Returns:
        Client: Supabase client instance
    """
    return SupabaseClient.get_client()
