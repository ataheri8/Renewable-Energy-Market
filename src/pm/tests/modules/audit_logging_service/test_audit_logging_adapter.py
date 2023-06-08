import pytest

from shared.adapters.als import AuditLoggingAdapter


class TestAuditLoggingAdapter:
    @pytest.mark.skip("Need to run audit logging service in ci profile")
    def test_write_audit_log(self):
        actor, action = "user@ge.com", "update"
        adapter = AuditLoggingAdapter()
        resp = adapter.write_log(actor, action)
        assert resp.status_code
