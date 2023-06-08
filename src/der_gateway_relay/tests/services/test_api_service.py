import pytest
import requests_mock

from der_gateway_relay.services.api_service import ApiService


class TestApiService:
    def test_post_program(self, config):
        with requests_mock.Mocker() as m:
            url = f"{config.DER_GATEWAY_URL}/registration/ws/staging/programs"
            m.register_uri("POST", url, status_code=200)
            api_service = ApiService()
            api_service.PROGRAM_ENDPOINT = url
            api_service.post_program("test data")

    def test_post_enrollment(self, config):
        with requests_mock.Mocker() as m:
            url = f"{config.DER_GATEWAY_URL}/registration/ws/staging/enrollment"
            m.register_uri("POST", url, status_code=200)
            api_service = ApiService()
            api_service.ENROLLMENT_ENDPOINT = url
            api_service.post_enrollment("test data")

    def test_post_provision(self, config):
        with requests_mock.Mocker() as m:
            url = f"{config.DER_GATEWAY_URL}/provision/programs"
            m.register_uri("POST", url, status_code=200)
            api_service = ApiService()
            api_service.ENROLLMENT_ENDPOINT = url
            api_service.post_enrollment("test data")

    @pytest.mark.skip(reason="Takes a while, will be a system e2e test")
    def test_post_program_failure(self, config):
        with requests_mock.Mocker() as m:
            url = f"{config.DER_GATEWAY_URL}/registration/ws/staging/programs"
            m.register_uri("POST", url, status_code=500)
            api_service = ApiService()
            api_service.PROGRAM_ENDPOINT = url
            try:
                api_service.post_program("test data")
            except Exception as e:
                assert e.response.status_code == 500

    @pytest.mark.skip(reason="Takes a while, will be a system e2e test")
    def test_post_enrollment_failure(self, config):
        with requests_mock.Mocker() as m:
            url = f"{config.DER_GATEWAY_URL}/registration/ws/staging/enrollment"
            m.register_uri("POST", url, status_code=500)
            api_service = ApiService()
            api_service.ENROLLMENT_ENDPOINT = url
            try:
                api_service.post_enrollment("test data")
            except Exception as e:
                assert e.response.status_code == 500
