import pytest

from pm.restapi import web


@pytest.fixture
def client():
    """Create a test flask client"""
    app = web.create_app()
    yield app.test_client()
