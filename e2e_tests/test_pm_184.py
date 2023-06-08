import requests
import xmltodict
import csv
import io
import string
from time import sleep
from uuid import uuid4
from datetime import datetime
import random
import json
import pytest
import os

CURRENT_DATE_TIME = datetime.now()
NEXT_YEAR_DATE_TIME = datetime.now().replace(year=CURRENT_DATE_TIME.year+1)

#TODO: DOE type programs need to have both supportedDoeControlTypeList and supportedControlTypeList generated in XML
PROGRAM_TYPES = ["GENERIC", "DEMAND_MANAGEMENT",] # "DYNAMIC_OPERATING_ENVELOPES"]

class ProgramFactory:
    def __init__(self):
        self.endpoint = "http://localhost:3001/api/program/"

    def get(self):
        all_program_data = requests.get(self.endpoint)
        assert all_program_data.status_code == 200
        return all_program_data.json()

    def post(self, program_type: str):
        prog_resp = requests.post(self.endpoint, json=self.generate_body(program_type))
        assert prog_resp.status_code == 201

    def generate_body(self, program_type: str):
        program_name = "name" + str(random.randint(10, 10000))
        program_body = dict(
            general_fields=dict(
                name=program_name,
                program_type=program_type,
                start_date=CURRENT_DATE_TIME.isoformat(),
                end_date=NEXT_YEAR_DATE_TIME.isoformat(),
                program_priority="P0",
                availability_type="SERVICE_WINDOWS",
                check_der_eligibility=True,
                define_contractual_target_capacity=True,
                notification_type="SMS_EMAIL",
            ),
            avail_operating_months=dict(
                jan=True,
                feb=True,
                mar=True,
                apr=True,
                may=True,
                jun=True,
                jul=True,
                aug=True,
                sep=True,
                oct=True,
                nov=True,
                dec=True,
            ),
            dispatch_constraints=dict(
                event_duration_constraint=dict(
                    min=1,
                    max=60,
                ),
                cumulative_event_duration=dict(
                    MONTH=dict(
                        min=1,
                        max=12,
                    ),
                    DAY=dict(
                        min=1,
                        max=28,
                    ),
                    YEAR=dict(
                        min=1,
                        max=2,
                    )
                ),
                max_number_of_events_per_timeperiod=dict(
                    MONTH=28,
                    DAY=1,
                    YEAR=4,
                ),
            ),
            resource_eligibility_criteria=dict(
                max_real_power_rating=10.0,
                min_real_power_rating=2.0,
            ),
            dispatch_max_opt_outs=[
                dict(
                    timeperiod="DAY",
                    value=10,
                ),
                dict(
                    timeperiod="MONTH",
                    value=10,
                ),
            ],
            dispatch_notifications=[dict(text="test", lead_time=10)],
            avail_service_windows=[
                dict(
                    start_hour=1,
                    end_hour=10,
                    mon=True,
                    tue=True,
                    wed=True,
                    thu=True,
                    fri=True,
                    sat=True,
                    sun=True,
                ),
            ],
        )

        if program_type == "DYNAMIC_OPERATING_ENVELOPES":
            program_body["dynamic_operating_envelope_fields"] = dict(
                limit_type="REACTIVE_POWER",
                calculation_frequency="DAILY",
                control_type="EXPORT_AND_IMPORT_LIMIT",
                schedule_time_horizon_timeperiod="MINUTES",
                schedule_time_horizon_number=10,
                schedule_timestep_mins=10,
            )
        elif program_type == "DEMAND_MANAGEMENT":
            program_body["demand_management_constraints"] = dict(
                max_total_energy_per_timeperiod=20,
                max_total_energy_unit="KWH",
                timeperiod="DAY",
            )
        else:
            program_body["control_options"] = ["OP_MOD_FIXED_VAR", ]

        return program_body


class ServiceProviderFactory:
    def __init__(self):
        self.endpoint = "http://localhost:3001/api/serviceprovider/"
        self.sp_id = None

    def post(self):
        sp_resp = requests.post(self.endpoint, json=self.generate_body())
        assert sp_resp.status_code == 201
        self.sp_id = sp_resp.json()["Created Service provider with id"]
        return self.sp_id

    def create_association(self, der_id, sp_id):
        file_name = 'der_association.csv'
        file_path = os.path.dirname(os.path.abspath(__file__)) + f"/{file_name}"

        with open(file_name, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            field = ['der_rdf_id']

            writer.writerow(field)
            writer.writerow([der_id])

        resp = requests.post(
            self.endpoint + f"{sp_id}/upload",
            data={},
            files=[
                ('file', (file_name, open(file_path, 'rb'), 'text/csv')),
            ],
            headers={
                'accept': 'application/json',
            },
        )
        assert resp.status_code == 202
        os.remove("der_association.csv")

    def get_by_id(self):
        sp_id = requests.get(self.endpoint + str(self.sp_id))
        assert sp_id.status_code == 200
        return sp_id.json()["id"]

    def generate_body(self):
        sp_body = {
            "notification_contact": {"email_address": "user@example.com", "phone_number": "8199151234"},
            "primary_contact": {"email_address": "user@example.com", "phone_number": "8199151234"},
            "address": {
                "city": "CityVille",
                "country": "Republic Of Countryton",
                "zip_code": "123-HI",
                "street": "LaRue Street",
                "state": "ME",
            },
            "general_fields": {
                "status": "ACTIVE",
                "name": "Service Provider",
                "service_provider_type": "AGGREGATOR",
            },
        }

        return sp_body


class DerFactory:
    def __init__(self):
        self.endpoint = "http://localhost:3002/api/der/"

    def post(self, der_id: str):
        der_resp = requests.post(
            self.endpoint,
            headers={'Content-Type': 'application/json'},
            json=self.generate_body(der_id)
        )
        assert der_resp.status_code == 201

    def get_all_available_ders(self):
        ders = requests.get("http://localhost:3001/api/der/available_ders")
        assert ders.status_code == 200
        return ders.json()

    def generate_body(self, der_id: str):
        sp_body = {
            "der_id": der_id,
            "name": self.create_random_string(),
            "der_type": "DR",
            "resource_category": "RES",
            "nameplate_rating": 10,
            "nameplate_rating_unit": "kW",
            "extra": {},
        }
        return sp_body

    def create_random_string(self):
        return "".join(random.choices(string.ascii_letters + string.digits, k=10))


class ContractFactory:
    def __init__(self):
        self.enrollment_endpoint = "http://localhost:3001/api/enrollment/"
        self.contract_endpoint = "http://localhost:3001/api/contract/"
        self.sp_id = None
        self.der_id = None
        self.program_id = None

    def get_all_contracts(self):
        contracts = requests.post(self.contract_endpoint)
        assert contracts.status_code == 200
        return contracts.json()

    def post(self, sp_id: int, der_id: str, program_id: int):
        self.sp_id = sp_id
        self.der_id = der_id
        self.program_id = program_id
        contract_resp = requests.post(self.enrollment_endpoint, json=self.generate_body())
        assert contract_resp.status_code == 201

    def delete_contract(self, contract_id: int):
        requests.delete(self.contract_endpoint + str(contract_id))

    def generate_body(self):
        contract_body = [
            dict(
                general_fields=dict(
                    program_id=self.program_id,
                    service_provider_id=self.sp_id,
                    der_id=self.der_id,
                ),
                dynamic_operating_envelopes=dict(
                    default_limits_active_power_import_kw=50,
                    default_limits_active_power_export_kw=50,
                    default_limits_reactive_power_import_kw=50,
                    default_limits_reactive_power_export_kw=50,
                ),
                demand_response=dict(
                    import_target_capacity=300.01,
                    export_target_capacity=30.01,
                ),
            ),
        ]
        return contract_body


class DER_Gateway_API:
    def __init__(self):
        self.wsid = "REGISTRATION"
        self.enrollment_endpoint = f"http://127.0.0.1:8075/api/v2/reg/ws/{self.wsid}/enrollment/program/"
        self.program_endpoint = f"http://127.0.0.1:8075/api/v2/reg/ws/{self.wsid}/program/"

    def get_enrollment(self, contract_id: int):
        enrollment = requests.get(self.enrollment_endpoint + str(contract_id))
        assert enrollment.status_code == 200
        enrollment_dict = xmltodict.parse(enrollment.text)
        return enrollment_dict

    def get_program(self, contract_id: int):
        program = requests.get(self.program_endpoint + str(contract_id))  # is this ok?
        assert program.status_code == 200
        program_dict = xmltodict.parse(program.text)
        return program_dict


def test_create_program(program_type: str):
    # CREATE PROGRAM AND GET PROGRAM ID
    program = ProgramFactory()
    program.post(program_type)

    prog_list = program.get()
    assert prog_list["results"][-1]["id"]
    program_id = prog_list["results"][-1]["id"]
    return program_id

def test_create_service_provider() -> int:
    # CREATE SERVICE PROVIDER AND GET SERVICE PROVIDER ID
    sp = ServiceProviderFactory()
    sp_id = sp.post()

    assert sp_id == sp.get_by_id()
    return sp_id

def test_create_der(der_id: str):
    der = DerFactory()
    der.post(der_id)

def test_create_der_association(der_id: str, service_provider_id: int):
    service_provider = ServiceProviderFactory()
    service_provider.create_association(der_id, service_provider_id)
    # let system have time to sync up before comparing der and service provider
    sleep(2)

def test_create_service_provider_and_der() -> tuple[int, str]:
    der_id = f"{uuid4()}"
    test_create_der(der_id)
    # let kafka catch up
    sleep(5)
    service_provider_id = test_create_service_provider()
    test_create_der_association(der_id, service_provider_id)
    return service_provider_id, der_id

def test_get_first_der_by_service_provider(service_provider_id: int):
    ders = DerFactory()
    ders = ders.get_all_available_ders()

    for der in ders:
        if der["service_provider_id"] == service_provider_id:
            return der["der_id"]

    raise Exception(f"Cannot find der with service_provider_id: {service_provider_id}")

def test_create_contract_e2e(sp_id: int, der_id: str, program_id: int):
    # CREATE CONTRACT USING SP, DER, PROGRAM ID'S AND LET KAFKA EMIT CHANGES VIA A MSG
    contract = ContractFactory()
    contract.post(sp_id, der_id, program_id)
    # Let Kafka Catchup
    sleep(5)

def test_get_enrollment_program(contract_id: int):
    der_gw = DER_Gateway_API()
    return der_gw.get_enrollment(contract_id), der_gw.get_program(contract_id)

def get_applicable_contract(der_id: str, sp_id: int, program_id: int):
    contracts = ContractFactory()
    all_contracts = contracts.get_all_contracts()

    for contract in all_contracts:
        if (
                contract["der_id"] == der_id and
                contract["program_id"] == program_id and
                contract["service_provider_id"] == sp_id
        ):
            return contract
        else:
            raise Exception("Cannot find applicable Contract")

# currently there is no good way of testing contract modification in our system
# The only values that der gateway really cares about are the contract constraints and demand management constraints
# See PM-1050 for updates
# def test_modify_contract(der_id, sp_id, program_id):
#     required_contract = get_applicable_contract(der_id, sp_id, program_id)
#     required_program = requests.get(f"http://localhost:3001/api/program/{program_id}").json()
#
#     required_program['program_priority'] = "P1"
#
#     requests.post(f"http://localhost:3001/api/program/{required_program['id']}", json=required_program)
#
#     # let kafka catch up
#     sleep(5)
#
#     # test der gateway has the values needed
#     _, program_dict = test_get_enrollment_program(required_contract["id"]) # check program_dict structure
#
#     # assert program has the updated value of default limits active power export kw
#     assert program_dict["some_value"] == required_contract["default_limits_active_power_export_kw"]
#     return required_contract["id"]

def test_cancel_contract(contract_id: int):
    contract = ContractFactory()
    contract.delete_contract(contract_id)

    # let kafka catch up
    sleep(5)

    # test der gateway has the values needed
    enrollment_dict, program_dict = test_get_enrollment_program(contract_id) # check program_dict structure

    assert program_dict["ProgramData"]["programLifeCycleStatus"] == "terminating" # check for exact value as needed
    assert (
            enrollment_dict["DERProgramEnrollmentList"]["DERProgramEnrollment"]["enrollmentLifeCycleStatus"]
            == "terminating"
    )
@pytest.mark.skip(reason="will be tested in the another container")
def test_e2e():

    """
    Create Programs and Enrollments in DER GW
    Given Three types of programs (Generic, DOE, Demand Management)
    When a Program is made with each of the three program types
    Given Service provider created in PMM,
    Given DER is created in DER_WH,
    Given DER is assigned to service provider via association,
    When Contracts are created in PMM,
    Then Kafka produces Enrollment data,
        And Program data,
        And Action is create
    Then der_gateway_relay consumes Kafka message,
        And creates XML for Programs
        And creates XML for Enrollments
    Then der_gateway_relay posts created XML via http to DER Gateway
    """

    """
    Update Programs and Enrollments in DER GW
    Given Three types of programs (Generic, DOE, Demand Management)
    When a Program is updated with each of the three program types
    Then Contracts are updated in PMM,
    Then Kafka produces Enrollment data,
        And Program data,
        And Action is update
    Then der_gateway_relay consumes Kafka message,
        And creates XML for Programs
        And creates XML for Enrollments
    Then der_gateway_relay posts created XML via http to DER Gateway
    """

    """
    Remove Programs and Enrollments in DER GW
    Given Contracts are Deleted in PMM,
    Then Kafka produces Enrollment data,
        And Program data,
        And Action is remove
    Then der_gateway_relay consumes Kafka message,
        And creates XML for Programs
        And creates XML for Enrollments
    Then der_gateway_relay posts created XML via http to DER Gateway
    """

    for program in PROGRAM_TYPES:
        # create program on PMM
        program_id = test_create_program(program)

        # create service provider
        # upload ders
        # create program with DER, SP, Association between SP/DER, and contract
        sp_id, der_id = test_create_service_provider_and_der()

        # get der for contract
        check_der_id = test_get_first_der_by_service_provider(sp_id)

        assert der_id == check_der_id

        # create contract and ensure it exists in der gateway
        test_create_contract_e2e(sp_id, der_id, program_id)
        sleep(5)

        # modify contract
        # contract_id = test_modify_contract(der_id, sp_id, program_id)
        # sleep(5)

        contract_id = sp_id # can remove this once modify contract is operational

        # cancel contract
        test_cancel_contract(contract_id)