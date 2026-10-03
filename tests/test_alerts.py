from tests.test_traffic import client

def test_create_and_update_alert(client):
    r=client.post('/api/alerts',json={'type':'manual_review','source_ip':'10.0.0.1','description':'Review event','severity':'low'})
    assert r.status_code==201
    updated=client.patch(f"/api/alerts/{r.json()['id']}",json={'status':'resolved'})
    assert updated.status_code==200 and updated.json()['status']=='resolved'

def test_device_operations(client):
    r=client.post('/api/devices',json={'ip_address':'192.168.1.5','hostname':'router'})
    assert r.status_code==201
    assert client.get('/api/devices').json()[0]['hostname']=='router'
    assert client.delete(f"/api/devices/{r.json()['id']}").status_code==204
