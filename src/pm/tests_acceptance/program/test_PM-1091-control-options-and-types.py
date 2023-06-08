from http import HTTPStatus

from pm.modules.progmgmt.models.program import Program
from pm.tests import factories
from pm.tests_acceptance.program.base import TestProgramBase
from shared.enums import ControlOptionsEnum, DOEControlType


class TestPM1091(TestProgramBase):
    """As a user, I want to be able to save a DOE program with control options and types"""

    def test_create_with_control_types_and_options(self, client, db_session):
        """BDD PM-1095

        Given a program does not exist
        When a program is created with control options
          And the selected Control Option is CSIP-AUS
          And there is a selected Control Type
        Then the program should save successfully
        """
        body = {
            "general_fields": {
                "name": "Test Program3",
                "program_type": "DYNAMIC_OPERATING_ENVELOPES",
            },
            "control_options": ["CSIP_AUS"],
            "dynamic_operating_envelope_fields": {"control_type": ["DER_IMPORT_LIMIT"]},
        }
        resp = client.post("/api/program/", json=body)
        assert resp.status_code == HTTPStatus.CREATED
        with db_session() as session:
            program = session.query(Program).filter_by(id=1).first()
            assert program.control_options == [ControlOptionsEnum.CSIP_AUS]
            assert program.control_type == [DOEControlType.DER_IMPORT_LIMIT]

    def test_update_with_control_types_and_options(self, client, db_session):
        """BDD PM-1096

        Given a program exists
        When a program is updated with control options
          And the selected Control Option is CSIP-AUS
          And there is a selected Control Type
        Then the program should save successfully
        """
        factories.DynamicOperatingEnvelopesProgram()
        body = {
            "control_options": ["CSIP_AUS"],
            "dynamic_operating_envelope_fields": {"control_type": ["DER_IMPORT_LIMIT"]},
        }
        resp = client.patch("/api/program/1", json=body)
        assert resp.status_code == HTTPStatus.OK
        with db_session() as session:
            program = session.query(Program).filter_by(id=1).first()
            assert program.control_options == [ControlOptionsEnum.CSIP_AUS]
            assert program.control_type == [DOEControlType.DER_IMPORT_LIMIT]

    def test_create_with_control_types_and_options_error(self, client, db_session):
        """BDD PM-1097

        Given a program does not exist
        When a program is created with control options
          And the selected Control Option is CSIP-AUS
          And there is no selected Control Type
        Then the creation should fail
          And the endpoint should return a 400 BAD REQUEST error
        """
        body = {
            "general_fields": {
                "name": "Test Program3",
                "program_type": "DYNAMIC_OPERATING_ENVELOPES",
            },
            "control_options": ["CSIP_AUS"],
        }

        resp = client.post("/api/program/", json=body)
        assert resp.status_code == HTTPStatus.BAD_REQUEST
        program = self._get_program(db_session, 1)
        assert not program

    def test_update_with_control_types_and_options_error(self, client, db_session):
        """BDD PM-1098

        Given a program exists
        When a program is updated with control options
          And the selected Control Option is CSIP-AUS
          And there is no selected Control Type
        Then the update should fail
          And the endpoint should return a 400 BAD REQUEST error
        """
        factories.DynamicOperatingEnvelopesProgram(control_type=None)
        body = {
            "control_options": ["CSIP_AUS"],
        }
        resp = client.patch("/api/program/1", json=body)
        assert resp.status_code == HTTPStatus.BAD_REQUEST
        with db_session() as session:
            program = session.query(Program).filter_by(id=1).first()
            assert program.control_options is None
            assert program.control_type is None
