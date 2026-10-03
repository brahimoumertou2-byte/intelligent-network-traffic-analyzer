import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.database import Base, get_db
from backend.main import app

@pytest.fixture
def client():
    engine=create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool)
    Base.metadata.create_all(engine); session=sessionmaker(bind=engine,expire_on_commit=False)
    def override():
        db=session()
        try: yield db
        finally: db.close()
    app.dependency_overrides[get_db]=override
    with TestClient(app) as c: yield c
    app.dependency_overrides.clear(); Base.metadata.drop_all(engine)

def test_create_and_list_traffic(client):
    r=client.post('/api/traffic',json={'source_ip':'192.168.1.10','destination_ip':'192.168.1.1','protocol':'tcp','source_port':52341,'destination_port':443,'packet_size':850,'timestamp':'2026-10-03T12:00:00Z'})
    assert r.status_code==201 and r.json()['protocol']=='TCP'
    assert len(client.get('/api/traffic').json())==1

def test_invalid_ip_rejected(client):
    r=client.post('/api/traffic',json={'source_ip':'invalid','destination_ip':'192.168.1.1','protocol':'TCP','packet_size':1})
    assert r.status_code==422

def test_missing_traffic_is_404(client): assert client.get('/api/traffic/999').status_code==404
