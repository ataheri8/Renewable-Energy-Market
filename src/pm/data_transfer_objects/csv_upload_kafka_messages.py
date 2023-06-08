from __future__ import annotations

from dataclasses import dataclass, field

from dataclasses_json import DataClassJsonMixin, config

from pm.modules.derinfo.repository import DerInfoRepository, DerNotFound
from pm.modules.enrollment.controller import EnrollmentController
from pm.modules.enrollment.enums import EnrollmentRequestStatus
from pm.modules.enrollment.models.enrollment import (
    DemandResponseDict,
    DynamicOperatingEnvelopesDict,
)
from pm.modules.enrollment.services.enrollment import (
    CreateUpdateEnrollmentRequestDict,
    EnrollmentRequestGenericFieldsDict,
    InvalidEnrollmentRequestArgs,
)
from pm.modules.progmgmt.repository import ProgramNotFound
from pm.modules.serviceprovider.controller import DerList, ServiceProviderController
from pm.modules.serviceprovider.enums import ServiceProviderStatus, ServiceProviderType
from pm.modules.serviceprovider.models.service_provider import Address, PrimaryContact
from pm.modules.serviceprovider.repository import ServiceProviderNotFound
from pm.modules.serviceprovider.services.service_provider import (
    CreateUpdateServiceProvider,
    GenericFields,
)
from shared.exceptions import LoggedError
from shared.minio_manager import (
    Message,
    check_value_is_allowed_by_enum,
    convert_strings_to_float,
    logger,
)
from shared.repository import UOW


@dataclass
class EnrollmentRequestMessage(Message, DataClassJsonMixin):
    der_id: str = field(metadata=config(field_name="DER_ID"))
    import_target_capacity: str = field(
        metadata=config(
            field_name="Import Target capacity (kW) (optional)",
        ),
    )
    export_target_capacity: str = field(
        metadata=config(
            field_name="Export Target Capacity (kW) (optional)",
        ),
    )
    import_active_limit: str = field(
        metadata=config(
            field_name="Default Limits - Active Power Import (kW) (optional)",
        ),
    )
    export_active_limit: str = field(
        metadata=config(
            field_name="Default Limits - Active Power Export (kW) (optional)",
        ),
    )
    import_reactive_limit: str = field(
        metadata=config(
            field_name="Default Limits - Reactive Power Import (kW) (optional)",
        ),
    )
    export_reactive_limit: str = field(
        metadata=config(
            field_name="Default Limits - Reactive Power Export (kW) (optional)",
        ),
    )

    @classmethod
    def get_class_label(cls):
        return "EnrollmentRequest"

    class Meta:
        topic = "pm.enrollment_request"

    def process_message(self):
        der_id = self.der_id
        program_id = int(self.headers["program_id"])
        try:
            with UOW() as uow:
                der = DerInfoRepository(uow.session).get_der_or_raise_exception(der_id=der_id)
            service_provider_id = der.service_provider_id
            general_fields = EnrollmentRequestGenericFieldsDict(
                program_id=program_id,
                service_provider_id=service_provider_id,  # type: ignore[typeddict-item]
                der_id=der_id,
                enrollment_status=EnrollmentRequestStatus.PENDING,
                rejection_reason=None,
            )
            dynamic_operating_envelopes = DynamicOperatingEnvelopesDict(
                default_limits_active_power_import_kw=convert_strings_to_float(
                    self.import_active_limit,
                ),  # type: ignore[typeddict-item]
                default_limits_active_power_export_kw=convert_strings_to_float(
                    self.export_active_limit,
                ),  # type: ignore[typeddict-item]
                default_limits_reactive_power_import_kw=convert_strings_to_float(
                    self.import_reactive_limit,
                ),  # type: ignore[typeddict-item]
                default_limits_reactive_power_export_kw=convert_strings_to_float(
                    self.export_reactive_limit,
                ),  # type: ignore[typeddict-item]
            )
            demand_response = DemandResponseDict(
                import_target_capacity=convert_strings_to_float(
                    self.import_target_capacity
                ),  # type: ignore[typeddict-item]
                export_target_capacity=convert_strings_to_float(
                    self.export_target_capacity
                ),  # type: ignore[typeddict-item]
            )
            enrollment_request_data = CreateUpdateEnrollmentRequestDict(
                general_fields=general_fields,
                dynamic_operating_envelopes=dynamic_operating_envelopes,
                demand_response=demand_response,
            )
            result = EnrollmentController().create_enrollment_request(enrollment_request_data)
            return result
        except (DerNotFound, InvalidEnrollmentRequestArgs, ProgramNotFound) as e:
            LoggedError(e)


@dataclass
class ServiceProviderMessage(Message, DataClassJsonMixin):
    """Message object for Service Provider ingest."""

    name: str = field(metadata=config(field_name="Name"))
    service_provider_type: str = field(metadata=config(field_name="Type"))
    primary_contact: str = field(metadata=config(field_name="Primary contact"))
    primary_email: str = field(metadata=config(field_name="Primary email"))
    notification_contact: str = field(metadata=config(field_name="Notification contact"))
    notification_email: str = field(metadata=config(field_name="Notification email"))
    street_address: str = field(metadata=config(field_name="Street Address"))
    apt_unit: str = field(metadata=config(field_name="Apt/unit"))
    city: str = field(metadata=config(field_name="City"))
    state_province_region: str = field(metadata=config(field_name="State/Province/Region"))
    country: str = field(metadata=config(field_name="Country"))
    zip_postal_code: str = field(metadata=config(field_name="ZIP/Postal Code"))
    status: str = field(metadata=config(field_name="Status"))

    def __post_init__(self):
        check_value_is_allowed_by_enum(self.status, ServiceProviderStatus)
        check_value_is_allowed_by_enum(self.service_provider_type, ServiceProviderType)

    @classmethod
    def get_class_label(cls):
        return "ServiceProvider"

    class Meta:
        topic = "pm.service_provider_enrollment"

    def process_message(self):
        try:
            generic_fields = GenericFields(
                name=self.name,
                service_provider_type=self.service_provider_type,  # type: ignore #noqa
                status=self.status,  # type: ignore #noqa
            )
            contact = PrimaryContact(
                email_address=self.primary_email,
                phone_number=self.primary_contact,
            )
            address = Address(
                street=self.street_address,
                city=self.city,
                state=self.state_province_region,
                country=self.country,
                zip_code=self.zip_postal_code,
                apt_unit=self.apt_unit,
            )
            product = CreateUpdateServiceProvider(
                general_fields=generic_fields,
                primary_contact=contact,
                notification_contact=self.notification_contact,  # type: ignore #noqa
                address=address,
            )
            ServiceProviderController().create_service_provider(product)
        except Exception as err:
            logger.error(f"Error: {err}")
            raise err


@dataclass
class ServiceProviderDERAssociateMessage(Message, DataClassJsonMixin):
    """Message object for associating DERs with service provider"""

    der_id: str = field(metadata=config(field_name="der_id"))

    class Meta:
        topic = "pm.service_provider_der_associate"

    @classmethod
    def get_class_label(cls):
        return "ServiceProviderDERAssociation"

    def process_message(self):
        der_object: DerList = dict(
            der_id=str(self.der_id),
        )
        service_provider_id = int(self.headers.get("service_provider_id"))
        try:
            ServiceProviderController().associate_ders(service_provider_id, [der_object])
        except ServiceProviderNotFound as err:
            logger.error(f"Error: {err}")
            raise err
