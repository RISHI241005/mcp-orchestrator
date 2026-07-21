import os
from fastapi.testclient import TestClient
import importlib

import orchestrator.api as api_module
from orchestrator.tasks import TaskStore
from orchestrator.memory import MemoryStore


def _prepare_client(api_key: str = 'testkey'):
    os.environ['ORCH_API_KEY'] = api_key
    os.environ['ORCH_DB_PATH'] = ':memory:'
    # replace stores with fresh in-memory instances
    api_module.tasks = TaskStore(db_path=':memory:')
    api_module.memory = MemoryStore(path=':memory:')
    client = TestClient(api_module.app)
    headers = {'X-API-Key': os.environ.get('ORCH_API_KEY')}
    return client, headers


def test_create_and_list_tasks():
    client, headers = _prepare_client()
    r = client.post('/tasks', json={'description': 'Order dinner', 'urgency': 5}, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert 'id' in data

    r2 = client.get('/tasks', headers=headers)
    assert r2.status_code == 200
    assert len(r2.json()) >= 1


def test_prioritize_and_route():
    client, headers = _prepare_client()
    task = {'description': 'Buy groceries', 'urgency': 2, 'preferred_server': 'instamart'}
    r = client.post('/prioritize', json=task, headers=headers)
    assert r.status_code == 200
    assert 'score' in r.json()

    r2 = client.post('/route', json=task, headers=headers)
    assert r2.status_code == 200
    assert r2.json().get('server') == 'instamart'


def test_place_order_mock():
    client, headers = _prepare_client()
    order = {'item': 'Biryani', 'qty': 1}
    r = client.post('/order', json=order, headers=headers)
    assert r.status_code == 200
    out = r.json()
    assert out.get('mock') is True
