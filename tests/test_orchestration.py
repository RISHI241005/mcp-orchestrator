import os
from fastapi.testclient import TestClient

# ensure env for tests
os.environ['ORCH_API_KEY'] = 'testkey'
os.environ['ORCH_DB_PATH'] = ':memory:'

from orchestrator.api import app

client = TestClient(app)
HEADERS = {'X-API-Key': os.environ.get('ORCH_API_KEY')}


def test_create_and_list_tasks():
    r = client.post('/tasks', json={'description': 'Order dinner', 'urgency': 5}, headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert 'id' in data

    r2 = client.get('/tasks', headers=HEADERS)
    assert r2.status_code == 200
    assert len(r2.json()) >= 1


def test_prioritize_and_route():
    task = {'description': 'Buy groceries', 'urgency': 2, 'preferred_server': 'instamart'}
    r = client.post('/prioritize', json=task, headers=HEADERS)
    assert r.status_code == 200
    assert 'score' in r.json()

    r2 = client.post('/route', json=task, headers=HEADERS)
    assert r2.status_code == 200
    assert r2.json().get('server') == 'instamart'


def test_place_order_mock():
    order = {'item': 'Biryani', 'qty': 1}
    r = client.post('/order', json=order, headers=HEADERS)
    assert r.status_code == 200
    out = r.json()
    assert out.get('mock') is True
