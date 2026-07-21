import os
from fastapi.testclient import TestClient

# Ensure API key and DB path are set for tests
os.environ['ORCH_API_KEY'] = 'testkey'
os.environ['ORCH_DB_PATH'] = ':memory:'

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
