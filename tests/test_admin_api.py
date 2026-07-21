import os
from fastapi.testclient import TestClient

# ensure env for tests
os.environ['ORCH_API_KEY'] = 'adminkey'
os.environ['ORCH_DB_PATH'] = ':memory:'

from orchestrator.api import app, tasks, memory

client = TestClient(app)
HEADERS = {'X-API-Key': 'adminkey'}


def test_admin_tasks_and_memory():
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
    memory.set('k1', {'v': 1})
    r3 = client.get('/admin/memory', headers=HEADERS)
    assert r3.status_code == 200
    assert r3.json().get('k1') == {'v': 1}
