import os
import importlib
from fastapi.testclient import TestClient

import orchestrator.api as api_module
from orchestrator.tasks import TaskStore
from orchestrator.memory import MemoryStore


def test_admin_tasks_and_memory():
    # set env per-test and rebuild in-memory stores to avoid interference between test modules
    os.environ['ORCH_API_KEY'] = 'adminkey'
    os.environ['ORCH_DB_PATH'] = ':memory:'

    # replace app-level stores with fresh in-memory instances
    api_module.tasks = TaskStore(db_path=':memory:')
    api_module.memory = MemoryStore(path=':memory:')

    client = TestClient(api_module.app)
    HEADERS = {'X-API-Key': os.environ.get('ORCH_API_KEY')}

    # create a task
    r = client.post('/tasks', json={'description': 'Admin task'}, headers=HEADERS)
    assert r.status_code == 200
    tid = r.json().get('id')
    assert tid

    # admin list tasks
    r2 = client.get('/admin/tasks', headers=HEADERS)
    assert r2.status_code == 200
    assert any(t.get('id') == tid for t in r2.json())

    # set memory
    api_module.memory.set('k1', {'v': 1})
    r3 = client.get('/admin/memory', headers=HEADERS)
    assert r3.status_code == 200
    assert r3.json().get('k1') == {'v': 1}
