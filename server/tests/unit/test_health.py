"""Basic tests for health check and app setup."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test the health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    """Test the root endpoint."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert data["docs"] == "/docs"


@pytest.mark.asyncio
async def test_nonexistent_endpoint(client: AsyncClient):
    """Test 404 for nonexistent endpoints."""
    response = await client.get("/api/nonexistent")
    assert response.status_code == 404
