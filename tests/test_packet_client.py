import httpx

from packet_capture.client import BackendClient


def test_backend_client_success():
    mock = httpx.MockTransport(lambda request: httpx.Response(201, json={"id": 7}, request=request))
    http = httpx.Client(transport=mock)
    client = BackendClient("http://backend.local/", client=http)
    assert client.endpoint == "http://backend.local/api/traffic"
    assert client.send_traffic({"protocol": "TCP"}) is True
    http.close()


def test_backend_client_failure_is_bounded():
    calls = []
    def unavailable(request):
        calls.append(request)
        return httpx.Response(503, json={"detail": "offline"}, request=request)
    http = httpx.Client(transport=httpx.MockTransport(unavailable))
    client = BackendClient("http://backend.local", retry_count=1, client=http)
    assert client.send_traffic({"protocol": "TCP"}) is False
    assert len(calls) == 2
    http.close()


def test_invalid_success_response_is_rejected():
    mock = httpx.MockTransport(lambda request: httpx.Response(201, json={"unexpected": True}, request=request))
    http = httpx.Client(transport=mock)
    client = BackendClient("http://backend.local", client=http)
    assert client.send_traffic({}) is False
    http.close()
