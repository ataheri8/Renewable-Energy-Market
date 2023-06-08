from unittest.mock import patch
from uuid import uuid4

import pytest
from freezegun import freeze_time
from testfixtures import LogCapture
from werkzeug.datastructures import FileStorage

from pm.modules.derinfo.enums import DerAssetType, DerResourceCategory, LimitUnitType
from pm.modules.derinfo.models.der_info import DerInfo
from pm.modules.serviceprovider.controller import (
    DerList,
    InvalidServiceProviderArgs,
    ServiceProviderController,
    ServiceProviderNoDerAssociationFound,
)
from pm.modules.serviceprovider.enums import ServiceProviderStatus, ServiceProviderType
from pm.modules.serviceprovider.models.service_provider import ServiceProvider
from pm.modules.serviceprovider.repository import ServiceProviderNotFound
from pm.modules.serviceprovider.services.service_provider import (
    CreateUpdateServiceProvider,
)
from pm.tests import factories
from pm.tests_acceptance.mixins import TestDataMixin


@pytest.fixture
def service_provider_ders():
    sp = factories.ServiceProviderFactory()
    factories.DerFactory(
        service_provider_id=sp.id,
        der_id=f"{uuid4()}",
        nameplate_rating_unit=LimitUnitType.kW,
        nameplate_rating=100,
        is_deleted=False,
        der_type=DerAssetType.PV,
        resource_category=DerResourceCategory.GENERIC,
    )
    return sp


class TestServiceProviderController(TestDataMixin):
    def _get_all_service_providers(self, db_session) -> list[ServiceProvider]:
        with db_session() as session:
            return session.query(ServiceProvider).all()

    def _get_all_ders(self, db_session) -> list[DerInfo]:
        with db_session() as session:
            return session.query(DerInfo).all()

    @pytest.mark.parametrize(
        "service_provider_args",
        [
            pytest.param(
                CreateUpdateServiceProvider.from_dict(
                    dict(
                        general_fields=dict(
                            name="name",
                            service_provider_type=ServiceProviderType.AGGREGATOR,
                            status=ServiceProviderStatus.ACTIVE,
                        ),
                        primary_contact=dict(
                            email_address="mlh@ge.com",
                            phone_number="905-444-5566",
                        ),
                        address=dict(
                            street="123 Street",
                            city="NoCity",
                            state="NoState",
                            country="NoCountry",
                            zip_code="A1B2C3",
                        ),
                    )
                ),
                id="all-fields",
            ),
            pytest.param(
                CreateUpdateServiceProvider.from_dict(
                    dict(
                        general_fields=dict(
                            name="name",
                            service_provider_type=ServiceProviderType.AGGREGATOR,
                            status=ServiceProviderStatus.ACTIVE,
                        ),
                        primary_contact=dict(
                            email_address="mlh@ge.com",
                            phone_number="905-444-5566",
                        ),
                    )
                ),
                id="minimum-fields",
            ),
        ],
    )
    def test_create_service_provider(self, service_provider_args, db_session):
        ServiceProviderController().create_service_provider(service_provider_args)
        service_providers = self._get_all_service_providers(db_session)
        assert len(service_providers) == 1

    def test_create_service_provider_error(self):
        data = CreateUpdateServiceProvider.from_dict({"general_fields": {"name": "test"}})
        with pytest.raises(InvalidServiceProviderArgs):
            ServiceProviderController().create_service_provider(data)

    def test_audit_log_in_create_service_provider_error(self):
        with LogCapture() as logs:
            data = CreateUpdateServiceProvider.from_dict({"general_fields": {"name": "test"}})
            with pytest.raises(InvalidServiceProviderArgs):
                ServiceProviderController().create_service_provider(data)
        assert "Unable to create service provider" in str(logs)

    def test_update_service_provider(self, db_session, service_provider):
        new_name = "new_name"
        data = CreateUpdateServiceProvider.from_dict({"general_fields": {"name": new_name}})
        ServiceProviderController().update_service_provider(service_provider.id, data)
        service_providers = self._get_all_service_providers(db_session)
        assert service_providers[0].name == new_name

    def test_audit_log_in_update_service_provider(self, db_session, service_provider):
        new_name = "new_name"
        data = CreateUpdateServiceProvider.from_dict({"general_fields": {"name": new_name}})
        with LogCapture() as logs:
            ServiceProviderController().update_service_provider(service_provider.id, data)
        assert "Saved Service Provider" in str(logs)

    def test_enable_service_provider(self, db_session, service_provider):
        service_provider.status = ServiceProviderStatus.INACTIVE
        ServiceProviderController().enable_service_provider(service_provider.id)
        service_providers = self._get_all_service_providers(db_session)
        assert service_providers[0].status == ServiceProviderStatus.ACTIVE

    def test_audit_log_in_enable_service_provider(self, db_session, service_provider):
        service_provider.status = ServiceProviderStatus.INACTIVE
        with LogCapture() as logs:
            ServiceProviderController().enable_service_provider(service_provider.id)
        assert "Enabled Service Provider" in str(logs)

    def test_disable_service_provider(self, db_session, service_provider):
        ServiceProviderController().disable_service_provider(service_provider.id)
        service_providers = self._get_all_service_providers(db_session)
        assert service_providers[0].status == ServiceProviderStatus.INACTIVE

    def test_audit_log_in_disable_service_provider(self, db_session, service_provider):
        with LogCapture() as logs:
            ServiceProviderController().disable_service_provider(service_provider.id)
        assert "Disabled Service Provider" in str(logs)

    def test_delete_service_provider(self, db_session, service_provider_ders):
        assert len(service_provider_ders.ders) == 1
        ServiceProviderController().delete_service_provider(service_provider_ders.id)
        service_providers = self._get_all_service_providers(db_session)
        assert len(service_providers) == 1
        assert service_providers[0].deleted is True
        ders = self._get_all_ders(db_session)
        assert len(ders) == 1
        assert ders[0].service_provider_id is None

    def test_audit_log_in_delete_service_provider(self, db_session, service_provider):
        with LogCapture() as logs:
            ServiceProviderController().delete_service_provider(service_provider.id)
        assert "Deleted Service Provider" in str(logs)

    def test_serviceprovider_has_been_soft_deleted(self, db_session, service_provider):
        service_providers = self._get_all_service_providers(db_session)
        assert len(service_providers) == 1
        assert service_providers[0].deleted is False

        ServiceProviderController().delete_service_provider(service_provider.id)
        service_providers = self._get_all_service_providers(db_session)
        assert len(service_providers) == 1
        assert service_providers[0].deleted is True
        assert service_providers[0] is not None

    def test_get_one_service_provider(self, db_session, service_provider):
        service_provider = ServiceProviderController().get_serviceprovider(service_provider.id)
        assert service_provider

    def test_get_all_service_provider(self, db_session):
        factories.ServiceProviderFactory()
        factories.ServiceProviderFactory()
        service_providers = ServiceProviderController().get_all_serviceproviders()
        assert len(service_providers) == 2

    def test_associate_ders(self, db_session, service_provider):
        # Make a DER without SP_id

        der_uuid = f"{uuid4()}"

        factories.DerFactory(
            der_id=der_uuid,
            name="test",
            nameplate_rating=100,
            nameplate_rating_unit=LimitUnitType.kW,
            der_type=DerAssetType.PV,
            resource_category=DerResourceCategory.GENERIC,
            is_deleted=False,
        )

        ders_list = [
            {
                "der_rdf_id": der_uuid,
            },
        ]
        ServiceProviderController().associate_ders(service_provider.id, ders_list)
        ders = self._get_all_ders(db_session)
        assert len(ders) == 1

    def test_associate_ders_failing_inactive(self, db_session, service_provider):
        der_uuid = f"{uuid4()}"

        ders_list = [
            {
                "der_rdf_id": der_uuid,
            },
        ]
        self._get_all_service_providers(db_session)
        ServiceProviderController().disable_service_provider(service_provider.id)
        with pytest.raises(ServiceProviderNotFound):
            ServiceProviderController().associate_ders(service_provider.id, ders_list)

    def test_delete_ders(self, db_session, service_provider):
        der_uuid = f"{uuid4()}"
        der = factories.DerFactory(
            service_provider_id=service_provider.id,
            der_id=der_uuid,
            name="test",
            nameplate_rating=100,
            nameplate_rating_unit=LimitUnitType.kW,
            der_type=DerAssetType.PV,
            resource_category=DerResourceCategory.GENERIC,
            is_deleted=False,
        )
        ServiceProviderController().delete_der_service_provider(service_provider.id, der.id)
        ders = self._get_all_ders(db_session)
        assert len(ders) == 1
        assert ders[0].service_provider_id is None

    def test_delete_service_provider_automate_deleted_ders(self, db_session, service_provider):
        der_uuid = f"{uuid4()}"
        factories.DerFactory(
            service_provider_id=service_provider.id,
            der_id=der_uuid,
            name="test",
            nameplate_rating=100,
            nameplate_rating_unit=LimitUnitType.kW,
            der_type=DerAssetType.PV,
            resource_category=DerResourceCategory.GENERIC,
            is_deleted=False,
        )
        ServiceProviderController().delete_service_provider(service_provider.id)
        ders = self._get_all_ders(db_session)
        assert len(ders) == 1
        assert ders[0].service_provider_id is None

    @freeze_time("2023-02-24 23:59:00")
    def test_associate_ders_upload_controller(self, db_session):
        with patch("shared.minio_manager.MinioManager.put_filehandle") as mock_minio_manager:
            filename = "valid_service_provider_der_association.csv"
            expected_file_name = (
                "valid_service_provider_der_association.2023-02-24T23-59-00-000000.csv"
            )
            filepath = self._get_test_data_path(filename)
            factories.ServiceProviderFactory(id=1)
            with open(filepath, "rb") as f:
                f_obj = FileStorage(f, filename)
                ServiceProviderController().associate_ders_file_upload(
                    1,
                    f_obj,
                    {"session_id": "session_id_123"},
                )
            mock_minio_manager.assert_called_once()
            args = mock_minio_manager.call_args.kwargs
            assert args["file_name"] == expected_file_name
            assert args["tags"] == {
                "original_file_name": filename,
                "service_provider_id": "1",
                "FILE_TYPE": "ServiceProviderDERAssociation",
                "number_of_rows": "4",
                "session_id": "session_id_123",
            }

    @freeze_time("2023-02-24 23:59:00")
    def test_service_providers_upload_controller(self, db_session):
        with patch("shared.minio_manager.MinioManager.put_filehandle") as mock_minio_manager:
            filename = "valid_service_providers.csv"
            expected_file_name = "valid_service_providers.2023-02-24T23-59-00-000000.csv"
            filepath = self._get_test_data_path(filename)
            with open(filepath, "rb") as f:
                f_obj = FileStorage(f, filename)
                ServiceProviderController().service_providers_file_upload(
                    f_obj,
                    {"session_id": "session_id_123"},
                )
            mock_minio_manager.assert_called_once()
            args = mock_minio_manager.call_args.kwargs
            assert args["file_name"] == expected_file_name
            assert args["tags"] == {
                "original_file_name": filename,
                "FILE_TYPE": "ServiceProvider",
                "number_of_rows": "2",
                "session_id": "session_id_123",
            }

    def test_download_data(self, db_session):
        factories.ServiceProviderFactory(id=1)
        der_uuid_1, der_uuid_2 = f"{uuid4()}", f"{uuid4()}"
        factories.DerFactory(
            der_id=der_uuid_1,
            name="test",
            nameplate_rating=100,
            nameplate_rating_unit=LimitUnitType.kW,
            der_type=DerAssetType.PV,
            resource_category=DerResourceCategory.GENERIC,
            is_deleted=False,
        )

        factories.DerFactory(
            der_id=der_uuid_2,
            name="test2",
            nameplate_rating=120,
            nameplate_rating_unit=LimitUnitType.kW,
            der_type=DerAssetType.WIND_FARM,
            resource_category=DerResourceCategory.GENERIC,
            is_deleted=False,
        )
        der_object_1: DerList = dict(
            der_id=der_uuid_1,
        )
        der_object_2: DerList = dict(
            der_id=der_uuid_2,
        )
        ServiceProviderController().associate_ders(1, [der_object_1, der_object_2])
        value = ServiceProviderController().download_service_provider_data(1)
        data = value.read().decode("utf-8-sig")
        assert der_uuid_1 in data
        assert der_uuid_2 in data

    def test_download_data_no_der_association(self, db_session):
        factories.ServiceProviderFactory(id=1)
        with LogCapture() as logs:
            with pytest.raises(ServiceProviderNoDerAssociationFound):
                ServiceProviderController().download_service_provider_data(1)
        assert "no DERs are associated with service provider" in str(logs)
