import pytest


@pytest.mark.asyncio
async def test_manual_refresh_usd_rate(client):
    response = await client.post('/api/v1/tasks/refresh_usd_rate')
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_calculate_delivery_cost(client):
    response = await client.post('/api/v1/tasks/calculate_delivery_cost')
    assert response.status_code == 200
