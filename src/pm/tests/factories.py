import random
from decimal import Decimal

import factory
import pendulum
from factory import Faker, fuzzy

from pm.modules.derinfo.enums import DerAssetType, DerResourceCategory, LimitUnitType
from pm.modules.derinfo.models.der_info import DerInfo
from pm.modules.enrollment.enums import (
    ContractStatus,
    ContractType,
    EnrollmentRequestStatus,
)
from pm.modules.enrollment.models.enrollment import Contract, EnrollmentRequest
from pm.modules.event_tracking.models.contract_constraint_summary import (
    ContractConstraintSummary,
)
from pm.modules.event_tracking.models.der_dispatch import DerDispatch
from pm.modules.event_tracking.models.der_response import DerResponse
from pm.modules.progmgmt.enums import (
    AvailabilityType,
    DispatchTypeEnum,
    DOECalculationFrequency,
    DOELimitType,
    EnergyUnit,
    NotificationType,
    ProgramCategory,
    ProgramStatus,
    ProgramTimePeriod,
    ScheduleTimeperiod,
)
from pm.modules.progmgmt.models.avail_operating_months import AvailOperatingMonths
from pm.modules.progmgmt.models.avail_service_window import AvailServiceWindow
from pm.modules.progmgmt.models.dispatch_notification import DispatchNotification
from pm.modules.progmgmt.models.dispatch_opt_out import DispatchOptOut
from pm.modules.progmgmt.models.program import Constraints, DemandManagementConstraints
from pm.modules.progmgmt.models.program import DemandManagementProgram as DMProgram
from pm.modules.progmgmt.models.program import (
    DynamicOperatingEnvelopesProgram as DOEProgram,
)
from pm.modules.progmgmt.models.program import (
    GenericProgram,
    Program,
    ResourceEligibilityCriteria,
)
from pm.modules.reports.enums import ReportTypeEnum
from pm.modules.reports.models.report import ContractReportDetails, EventDetails, Report
from pm.modules.serviceprovider.enums import ServiceProviderStatus, ServiceProviderType
from pm.modules.serviceprovider.models.service_provider import ServiceProvider
from shared.enums import (
    ControlOptionsEnum,
    DOEControlType,
    ProgramPriority,
    ProgramTypeEnum,
)
from shared.system.database import Session


class BaseMeta:
    sqlalchemy_session = Session
    sqlalchemy_session_persistence = "commit"


# Program Factories
class ProgramFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Program with minimum allowed fields"""

    class Meta(BaseMeta):
        model = Program

    name = fuzzy.FuzzyText(length=30)
    program_type = ProgramTypeEnum.GENERIC
    status = ProgramStatus.PUBLISHED


class AvailOperatingMonthsFactory(factory.alchemy.SQLAlchemyModelFactory):
    """AvailOperatingMonths with minimum allowed fields"""

    class Meta(BaseMeta):
        model = AvailOperatingMonths

    jan = True
    feb = False
    mar = False
    apr = False
    may = False
    jun = False
    jul = False
    aug = False
    sep = False
    oct = False
    nov = False
    dec = False


class AvailServiceWindowFactory(factory.alchemy.SQLAlchemyModelFactory):
    """AvailServiceWindow with minimum allowed fields"""

    class Meta(BaseMeta):
        model = AvailServiceWindow

    start_hour = 1
    end_hour = 10
    mon = True
    tue = True
    wed = True
    thu = True
    fri = True
    sat = True
    sun = True


class DispatchNotificationFactory(factory.alchemy.SQLAlchemyModelFactory):
    """DispatchNotification with minimum allowed fields"""

    class Meta(BaseMeta):
        model = DispatchNotification

    text = fuzzy.FuzzyText(length=30)
    lead_time = 10


class DispatchOptOutFactory(factory.alchemy.SQLAlchemyModelFactory):
    """DispatchOptOut with minimum allowed fields"""

    class Meta(BaseMeta):
        model = DispatchOptOut

    timeperiod = ProgramTimePeriod.DAY
    value = 10


class SharedFieldsProgramFactory(ProgramFactory):
    """Program with all shared fields"""

    program_category = ProgramCategory.GENERIC
    start_date = pendulum.now()
    end_date = pendulum.now().add(months=1)
    program_priority = ProgramPriority.P0
    availability_type = AvailabilityType.SERVICE_WINDOWS
    check_der_eligibility = True
    define_contractual_target_capacity = True
    notification_type = NotificationType.SMS_EMAIL
    resource_eligibility_criteria = ResourceEligibilityCriteria(
        max_real_power_rating=10.0,
        min_real_power_rating=2.0,
    )
    status = ProgramStatus.PUBLISHED
    holiday_exclusions = {
        "calendars": [
            {
                "mrid": "system",
                "timezone": "Europe/Paris",
                "year": 2023,
                "events": [
                    {
                        "startDate": "2023-01-01",
                        "endDate": "2023-01-01",
                        "name": "New year",
                        "category": "holiday",
                        "substitutionDate": "2022-01-01",
                    },
                    {
                        "startDate": "2023-04-02",
                        "endDate": "2023-04-02",
                        "name": "Easter Monday",
                        "category": "holiday",
                        "substitutionDate": "2023-05-01",
                    },
                    {
                        "startDate": "2023-05-01",
                        "endDate": "2023-05-01",
                        "name": "Labour Day",
                        "category": "holiday",
                    },
                ],
            }
        ]
    }

    @factory.post_generation
    def create_related(self, create, extracted, **kwargs):
        """Create the related objects for the program"""
        AvailOperatingMonthsFactory(program_id=self.id)
        DispatchNotificationFactory(program_id=self.id)
        DispatchOptOutFactory(program_id=self.id)
        if self.availability_type == AvailabilityType.SERVICE_WINDOWS:
            AvailServiceWindowFactory(program_id=self.id, start_hour=1, end_hour=10)
            AvailServiceWindowFactory(program_id=self.id, start_hour=10, end_hour=12)


dispatch_constraints_dict = Constraints.from_dict(
    dict(
        event_duration_constraint=dict(
            min=1,
            max=2,
        ),
        cumulative_event_duration=dict(
            MONTH=dict(
                min=None,
                max=20,
            ),
            DAY=dict(
                min=5,
                max=None,
            ),
        ),
        max_number_of_events_per_timeperiod=dict(
            MONTH=2,
            DAY=10,
        ),
    )
)


class GenericProgramFactory(SharedFieldsProgramFactory):
    class Meta(BaseMeta):
        model = GenericProgram

    control_options = [ControlOptionsEnum.OP_MOD_CONNECT]
    dispatch_type = DispatchTypeEnum.DER_GATEWAY
    track_event = True
    dispatch_constraints = dispatch_constraints_dict


class DemandManagementProgramFactory(SharedFieldsProgramFactory):
    class Meta(BaseMeta):
        model = DMProgram

    demand_management_constraints = DemandManagementConstraints(
        max_total_energy_per_timeperiod=20.5,
        max_total_energy_unit=EnergyUnit.KWH,
        timeperiod=ProgramTimePeriod.MONTH,
    )
    dispatch_constraints = dispatch_constraints_dict
    program_type = ProgramTypeEnum.DEMAND_MANAGEMENT


class DynamicOperatingEnvelopesProgram(SharedFieldsProgramFactory):
    class Meta(BaseMeta):
        model = DOEProgram

    limit_type = DOELimitType.REAL_POWER
    calculation_frequency = DOECalculationFrequency.EVERY_30_MINUTES
    control_type = [DOEControlType.DER_EXPORT_LIMIT]
    schedule_time_horizon_timeperiod = ScheduleTimeperiod.DAYS
    schedule_time_horizon_number = 10
    schedule_timestep_mins = 15
    program_type = ProgramTypeEnum.DYNAMIC_OPERATING_ENVELOPES


# Service Provider Factories
class DerFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta(BaseMeta):
        model = DerInfo

    id = fuzzy.FuzzyInteger(1, 1000000, step=1)
    der_id = Faker("uuid4")
    name = fuzzy.FuzzyText(length=30)
    der_type = random.choice(list(DerAssetType))
    resource_category = random.choice(list(DerResourceCategory))
    nameplate_rating_unit = random.choice(list(LimitUnitType))
    nameplate_rating = 100.123
    is_deleted = False
    service_provider_id = None


class ServiceProviderFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta(BaseMeta):
        model = ServiceProvider

    id = fuzzy.FuzzyInteger(1, 1000000, step=1)
    name = fuzzy.FuzzyText(length=30)
    uuid = Faker("uuid4")
    service_provider_type = ServiceProviderType.AGGREGATOR
    status = ServiceProviderStatus.ACTIVE
    primary_contact = {
        "email_address": "totallyrealemail@something.com",
        "phone_number": "905-444-5566",
    }
    address = {
        "street": "123 Which Street",
        "city": "NoCity",
        "state": "NoState",
        "country": "NoCountry",
        "zip_code": "A1B2C3",
    }


# Enrollment Factories
class EnrollmentRequestFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta(BaseMeta):
        model = EnrollmentRequest

    id = fuzzy.FuzzyInteger(1, 1000000, step=1)
    der = factory.SubFactory(DerFactory)
    enrollment_status = EnrollmentRequestStatus.PENDING
    program = factory.SubFactory(ProgramFactory)
    service_provider = factory.SubFactory(ServiceProviderFactory)


class EnrollmentRequestFactoryWithProgramAndServiceProvider(factory.alchemy.SQLAlchemyModelFactory):
    class Meta(BaseMeta):
        model = EnrollmentRequest

    id = fuzzy.FuzzyInteger(1, 1000000, step=1)
    der_id = Faker("uuid4")
    enrollment_status = EnrollmentRequestStatus.PENDING
    program_id = fuzzy.FuzzyInteger(1, 1000000, step=1)
    service_provider_id = fuzzy.FuzzyInteger(1, 1000000, step=1)


class ContractFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta(BaseMeta):
        model = Contract

    id = fuzzy.FuzzyInteger(1, 1000000, step=1)
    program = factory.SubFactory(ProgramFactory)
    service_provider = factory.SubFactory(ServiceProviderFactory)
    der = factory.SubFactory(DerFactory)
    contract_status = ContractStatus.ACCEPTED
    contract_type = ContractType.ENROLLMENT_CONTRACT
    enrollment_request = factory.SubFactory(EnrollmentRequestFactory)


class DerDispatchFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta(BaseMeta):
        model = DerDispatch

    event_id = "event1"
    start_date_time = pendulum.now().subtract(hours=1)
    end_date_time = pendulum.now()
    event_status = "scheduled"
    control_id = "control-1"
    control_type = "scheduled"
    control_command = Decimal(10)
    contract_id = fuzzy.FuzzyInteger(1, 1000000, step=1)


class DerResponseFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta(BaseMeta):
        model = DerResponse

    id = fuzzy.FuzzyInteger(1, 1000000, step=1)
    der_id = Faker("uuid4")
    der_response_status = 2
    der_response_time = pendulum.now()
    control_id = "control-1"
    is_opt_out = False


class ContractConstraintSummaryFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta(BaseMeta):
        model = ContractConstraintSummary

    id = fuzzy.FuzzyInteger(1, 1000000, step=1)
    contract_id = fuzzy.FuzzyInteger(1, 1000000, step=1)


class ReportFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta(BaseMeta):
        model = Report

    id = fuzzy.FuzzyInteger(1, 1000000, step=1)
    created_at = pendulum.now()
    updated_at = pendulum.now()
    report_type = ReportTypeEnum.INDIVIDUAL_PROGRAM
    program_id = fuzzy.FuzzyInteger(1, 1000000, step=1)
    service_provider_id = fuzzy.FuzzyInteger(1, 1000000, step=1)
    start_report_date = pendulum.now().subtract(hours=1)
    end_report_date = pendulum.now()
    created_by = "Mike Jones III"


class ContractReportDetailsFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta(BaseMeta):
        model = ContractReportDetails

    id = fuzzy.FuzzyInteger(1, 1000000, step=1)
    enrollment_date = pendulum.now()
    report_id = fuzzy.FuzzyInteger(1, 1000000, step=1)
    der_id = fuzzy.FuzzyInteger(1, 1000000, step=1)
    service_provider_id = fuzzy.FuzzyInteger(1, 1000000, step=1)
    contract_constraint_id = fuzzy.FuzzyInteger(1, 1000000, step=1)


class EventDetailsFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta(BaseMeta):
        model = EventDetails

    id = fuzzy.FuzzyInteger(1, 1000000, step=1)
    report_id = fuzzy.FuzzyInteger(1, 1000000, step=1)
    dispatch_id = fuzzy.FuzzyInteger(1, 1000000, step=1)
    event_start = pendulum.now().subtract(hours=1)
    event_end = pendulum.now()
    number_of_dispatched_der = fuzzy.FuzzyInteger(1, 1000000, step=1)
    number_of_opted_out_der = fuzzy.FuzzyInteger(1, 1000000, step=1)
    requested_capacity = Decimal(10)
    dispatched_capacity = Decimal(10)
    event_status = "accepted"
