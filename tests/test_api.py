from fastapi.testclient import TestClient
from orchestrator.api import app

client = TestClient(app)


def test_health():
    r = client.get('/health')
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_search_mock():
    r = client.get('/search', params={'q': 'biryani'})
    assert r.status_code == 200
    data = r.json()
    assert data.get('mock') is True
