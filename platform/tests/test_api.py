import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import service

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"

@pytest.mark.asyncio
async def test_auth_register_no_body(client):
    resp = await client.post("/auth/register", json={})
    assert resp.status_code == 422

@pytest.mark.asyncio
async def test_auth_login_no_body(client):
    resp = await client.post("/auth/login", json={})
    assert resp.status_code == 422

@pytest.mark.asyncio
async def test_homes_requires_auth(client):
    resp = await client.get("/homes")
    assert resp.status_code in (401, 403)

@pytest.mark.asyncio
async def test_devices_requires_auth(client):
    resp = await client.post("/devices/pair", json={"gateway_id": "test", "firmware_ver": "0.1"})
    assert resp.status_code in (401, 403)

@pytest.mark.asyncio
async def test_events_requires_auth(client):
    resp = await client.get("/events/00000000-0000-0000-0000-000000000000")
    assert resp.status_code in (401, 403)

@pytest.mark.asyncio
async def test_export_requires_auth(client):
    resp = await client.get("/export/00000000-0000-0000-0000-000000000000/csv")
    assert resp.status_code in (401, 403)

@pytest.mark.asyncio
async def test_arming_requires_auth(client):
    resp = await client.get("/arming/schedule")
    assert resp.status_code in (401, 403)

@pytest.mark.asyncio
async def test_wellness_requires_auth(client):
    resp = await client.get("/wellness/00000000-0000-0000-0000-000000000000/breathing")
    assert resp.status_code in (401, 403)

@pytest.mark.asyncio
async def test_api_keys_requires_auth(client):
    resp = await client.get("/api-keys")
    assert resp.status_code in (401, 403)

@pytest.mark.asyncio
async def test_settings_requires_auth(client):
    resp = await client.get("/settings/profile")
    assert resp.status_code in (401, 403)

@pytest.mark.asyncio
async def test_push_subscribe_requires_auth(client):
    resp = await client.post("/push/subscribe", json={"endpoint": "https://test", "keys": {"p256dh": "a", "auth": "b"}, "home_id": "00000000-0000-0000-0000-000000000000"})
    assert resp.status_code in (401, 403)

@pytest.mark.asyncio
async def test_zones_requires_auth(client):
    resp = await client.get("/zones/00000000-0000-0000-0000-000000000000")
    assert resp.status_code in (401, 403)

@pytest.mark.asyncio
async def test_subscriptions_requires_auth(client):
    resp = await client.get("/subscriptions")
    assert resp.status_code in (401, 403)

@pytest.mark.asyncio
async def test_agent_requires_auth(client):
    resp = await client.post("/agent/query", json={"query": "test"})
    assert resp.status_code in (401, 403)

@pytest.mark.asyncio
async def test_webhooks_requires_auth(client):
    resp = await client.get("/webhooks/00000000-0000-0000-0000-000000000000")
    assert resp.status_code in (401, 403)

@pytest.mark.asyncio
async def test_events_count(client):
    resp = await client.get("/events/00000000-0000-0000-0000-000000000000/count")
    assert resp.status_code in (401, 403)


@pytest.fixture
def override_auth_admin():
    """Override auth to return admin user for ops endpoints."""
    from app.middleware.auth import get_current_user
    async def mock_admin():
        return {"sub": "admin-user-id", "email": "admin@test.com", "role": "admin"}
    app.dependency_overrides[get_current_user] = mock_admin
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def override_auth_consumer():
    """Override auth to return consumer user for home endpoints."""
    from app.middleware.auth import get_current_user
    from app.middleware.ownership import verify_home_ownership
    async def mock_consumer():
        return {"sub": "test-user-id", "email": "test@test.com", "role": "consumer"}
    async def mock_verify(home_id: str, payload: dict = None):
        return home_id
    app.dependency_overrides[get_current_user] = mock_consumer
    app.dependency_overrides[verify_home_ownership] = mock_verify
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_ops_health_returns_status(client, override_auth_admin):
    with patch("app.routers.health.service.table") as mock_table:
        mock_users = MagicMock()
        mock_users.data = [{"role": "admin"}]
        mock_execute = MagicMock()
        mock_execute.data = []
        mock_execute.count = 5
        mock_execute2 = MagicMock()
        mock_execute2.count = 3

        def mock_chain(table_name):
            m = MagicMock()
            m.select.return_value = m
            m.eq.return_value = m
            m.gte.return_value = m
            m.limit.return_value = m
            m.order.return_value = m
            if table_name == "users":
                m.execute.return_value = mock_users
            elif table_name == "homes":
                m.execute.return_value = mock_execute2
            elif table_name == "events":
                m.execute.return_value = mock_execute
            else:
                m.execute.return_value = MagicMock(data=[])
            return m

        mock_table.side_effect = mock_chain
        resp = await client.get("/health/ops/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "supabase" in data
        assert "active_homes" in data
        assert "events_last_5min" in data


@pytest.mark.asyncio
async def test_ops_health_requires_admin(client):
    from app.middleware.auth import get_current_user
    async def mock_consumer():
        return {"sub": "user-id", "email": "user@test.com", "role": "consumer"}
    app.dependency_overrides[get_current_user] = mock_consumer
    with patch("app.routers.health.service.table") as mock_table:
        mock_users = MagicMock()
        mock_users.data = [{"role": "consumer"}]
        m = MagicMock()
        m.select.return_value = m
        m.eq.return_value = m
        m.execute.return_value = mock_users
        mock_table.return_value = m
        resp = await client.get("/health/ops/health")
    app.dependency_overrides.clear()
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_baseline_returns_valid_structure(client, override_auth_consumer):
    resp = await client.get("/health/00000000-0000-0000-0000-000000000000/baseline")
    assert resp.status_code == 200
    data = resp.json()
    assert data["home_id"] == "00000000-0000-0000-0000-000000000000"
    assert "learning" in data
    assert "days_remaining" in data
    assert "samples_collected" in data
    assert "baseline_computed" in data
    assert "learning_start" in data
    assert "learning_days" in data
