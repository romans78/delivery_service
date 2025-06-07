import pytest
from httpx import AsyncClient, ASGITransport

from main import app
from utils.session import get_db, get_session_id


@pytest.fixture
async def client(db):
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_session_id] = lambda: 'test_session_id'

    async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url='http://test'
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_register_package(client):
    package_data = {
        'name': 'Test Package',
        'weight': 5.5,
        'type_name': 'одежда',
        'content_value_usd': 100.0
    }
    response = await client.post('/api/v1/package', json=package_data)
    assert response.status_code == 200
    assert 'id' in response.json()


@pytest.mark.asyncio
async def test_register_package_invalid_type(client):
    package_data = {
        'name': 'Invalid Package',
        'weight': 10.0,
        'type_name': 'invalid_type',
        'content_value_usd': 50.0
    }
    response = await client.post('/api/v1/package', json=package_data)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_package_types(client):
    response = await client.get('/api/v1/package_types')
    assert response.status_code == 200
    types = response.json()
    assert len(types) >= 3
    assert any(t['type_name'] == 'одежда' for t in types)


@pytest.mark.asyncio
async def test_get_packages_with_filters(client):
    packages = [
        {'name': 'Package1', 'weight': 1.0, 'type_name': 'одежда', 'content_value_usd': 10},
        {'name': 'Package2', 'weight': 5.0, 'type_name': 'электроника', 'content_value_usd': 50},
        {'name': 'Package3', 'weight': 7.0, 'type_name': 'разное', 'content_value_usd': 100}
    ]
    for pkg in packages:
        await client.post('/api/v1/package', json=pkg)

    # Without filters
    response = await client.get('/api/v1/packages?page=1&size=3')
    assert response.status_code == 200
    data = response.json()
    assert len(data['items']) == 3

    # Filter by type
    response = await client.get('/api/v1/packages?page=1&size=10&type_name=электроника')
    data = response.json()
    assert data['items'][0]['type_name'] == 'электроника'


@pytest.mark.asyncio
async def test_get_package_by_id(client):
    package = {
        'name': 'Test Package',
        'weight': 2.5,
        'type_name': 'разное',
        'content_value_usd': 200.0
    }
    create_resp = await client.post('/api/v1/package', json=package)
    package_id = create_resp.json()['id']

    response = await client.get(f'/api/v1/package/{package_id}')
    assert response.status_code == 200
    data = response.json()
    assert data['name'] == 'Test Package'
    assert data['delivery_cost'] == 'Не рассчитано'


@pytest.mark.asyncio
async def test_get_nonexistent_package(client):
    response = await client.get('/api/v1/package/9999')
    assert response.status_code == 200
    assert response.json()['message'] == 'No package for id 9999'
