from fastapi.testclient import TestClient
from orchestrator.api import app

client = TestClient(app)


def test_create_and_list_tasks():
    r = client.post('/tasks', json={'description': 'Order dinner', 'urgency': 5})
    assert r.status_code == 200
    data = r.json()
    assert 'id' in data

    r2 = client.get('/tasks')
    assert r2.status_code == 200
    assert len(r2.json()) >= 1


def test_prioritize_and_route():
    task = {'description': 'Buy groceries', 'urgency': 2, 'preferred_server': 'instamart'}
    r = client.post('/prioritize', json=task)
    assert r.status_code == 200
    assert 'score' in r.json()

    r2 = client.post('/route', json=task)
    assert r2.status_code == 200
    assert r2.json().get('server') == 'instamart'


def test_place_order_mock():
    order = {'item': 'Biryani', 'qty': 1}
    r = client.post('/order', json=order)
    assert r.status_code == 200
    out = r.json()
    assert out.get('mock') is True
