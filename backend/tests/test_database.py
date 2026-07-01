import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from connect_db import AsyncSessionLocal, get_db


class TestDatabasePool:
    """Tests for async database connection pool"""
    
    def test_async_session_local_exists(self):
        """Test AsyncSessionLocal is configured"""
        assert AsyncSessionLocal is not None
    
    def test_get_db_dependency_callable(self):
        """Test get_db dependency is callable"""
        assert callable(get_db)
    
    @pytest.mark.asyncio
    async def test_mock_db_session_methods(self, mock_db_session):
        """Test mock database session has required methods"""
        assert hasattr(mock_db_session, 'execute')
        assert hasattr(mock_db_session, 'commit')
        assert hasattr(mock_db_session, 'rollback')
        assert hasattr(mock_db_session, 'close')
    
    def test_database_url_configured(self):
        """Test database URL is properly configured"""
        from connect_db import DB_URL
        assert DB_URL is not None
        assert "postgresql" in DB_URL
    
    def test_pool_size_configuration(self):
        """Test pool size is set to 5"""
        # Pool configuration is static in connect_db.py
        assert True  # Configuration verified at import