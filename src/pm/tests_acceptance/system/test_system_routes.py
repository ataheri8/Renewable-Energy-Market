class TestHealthCheck:
    def test_health_check(self, client):
        resp = client.get("/api/system/health-check")
        assert resp.status_code == 200
        assert resp.json["message"] == "online"
