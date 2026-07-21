import os
from fastapi.testclient import TestClient

# start with clean env
os.environ.pop('ORCH_API_KEYS', None)
os.environ['ORCH_DB_PATH'] = ':memory:'

import orchestrator.api as api_module
from orchestrator.auth import add_key, get_all_keys

client = TestClient(api_module.app)


def test_role_based_keys():
    # no keys initially -> open access
    r = client.get('/health')
    assert r.status_code == 200

    # add an admin key
    add_key('adminkey', 'admin')
    keys = get_all_keys()
    assert 'adminkey' in keys and keys['adminkey'] == 'admin'

    # admin can create user key
    r = client.post('/admin/keys', json={'key': 'userkey', 'role': 'user'}, headers={'X-API-Key': 'adminkey'})
    assert r.status_code == 200

    # user key can call user endpoints
    r2 = client.post('/tasks', json={'description': 'u1'}, headers={'X-API-Key': 'userkey'})
    assert r2.status_code == 200

    # user cannot list admin endpoints
    r3 = client.get('/admin/tasks', headers={'X-API-Key': 'userkey'})
    assert r3.status_code == 403

    # admin can remove key
    r4 = client.delete('/admin/keys/userkey', headers={'X-API-Key': 'adminkey'})
    assert r4.status_code == 200

    # removed key fails
    r5 = client.post('/tasks', json={'description': 'u2'}, headers={'X-API-Key': 'userkey'})
    assert r5.status_code == 401
