from tests.test_traffic import client

def test_empty_statistics_are_database_backed(client):
    result=client.get('/api/statistics/overview')
    assert result.status_code==200
    assert result.json()=={'total_packets':0,'traffic_volume':0,'active_devices':0,'total_alerts':0}

def test_protocol_statistics(client):
    client.post('/api/traffic',json={'source_ip':'10.0.0.1','destination_ip':'10.0.0.2','protocol':'UDP','packet_size':99})
    assert client.get('/api/statistics/protocols').json()==[{'protocol':'UDP','count':1}]
