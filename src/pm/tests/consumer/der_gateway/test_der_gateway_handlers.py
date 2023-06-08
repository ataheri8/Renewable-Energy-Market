from unittest import mock
from unittest.mock import Mock

from pm.consumers.der_gateway.handlers import handle_der_control, handle_der_response
from pm.modules.event_tracking.controller import EventController
from shared.tasks.consumer import ConsumerMessage


class TestDerGatewayHandlers:
    def _make_der_control_message(self, number: int) -> ConsumerMessage:
        data = {
            "dermControlId": "1",
            "dermDispatchId": "1",
            "controlId": "B94E28E2C65547B3B1F9C096D4F8952B",
            "controlGroupId": "1",
            "initiallyParticipatingDERs": ["9101080001", "9101080002"],
            "creationTime": 1635458197,
            "dermUserId": "John Doe",
            "startTime": 1635489900,
            "endTime": 1635497100,
            "controlType": "kW % Rated Capacity",
            "controlSetpoint": "77.77",
            "controlEventStatus": "scheduled",
        }
        messages = []
        for i in range(number):
            data["controlGroupId"] = str(i)
            messages.append(Mock(spec=ConsumerMessage, headers={}, value=data))
        return messages

    def _assert_handles_messages(self, expected_count: int, messages: ConsumerMessage):
        controller_mock = Mock(spec=EventController)
        with mock.patch("pm.consumers.der_gateway.handlers.EventController", controller_mock):
            handle_der_control(messages)
            instance = controller_mock.return_value
            assert instance.create_der_dispatch.call_count == 1
            args = instance.create_der_dispatch.call_args[0][0]
            assert len(args) == expected_count

    def test_der_control(self):
        messages_number = 500
        messages = self._make_der_control_message(messages_number)
        self._assert_handles_messages(messages_number, messages)

    def test_der_control_skip_bad_data(self):
        messages_number = 498
        messages = self._make_der_control_message(messages_number)
        messages += [
            Mock(
                spec=ConsumerMessage,
                headers={},
                value={
                    "dermControlId": "1",
                    "dermDispatchId": "1",
                    "controlId": "B94E28E2C65547B3B1F9C096D4F8952B",
                    "controlGroupId": "1",
                    "initiallyParticipatingDERs": ["9101080001", "9101080002"],
                    "creationTime": 1635458197,
                    "dermUserId": "John Doe",
                    "startTime": 1635489900,
                    "endTime": "not a timestamp",
                    "controlType": "kW % Rated Capacity",
                    "controlSetpoint": "77.77",
                    "controlEventStatus": "scheduled",
                },
            ),
            Mock(
                spec=ConsumerMessage,
                headers={},
                value={},
            ),
        ]
        self._assert_handles_messages(messages_number, messages)

    def _make_der_response_message(self, number: int) -> ConsumerMessage:
        data = {
            "controlId": "1234",
            "edevId": "",
            "status": "4",
            "time": 1635489900,
        }
        messages = []
        for i in range(number):
            data["der_id"] = str(i)
            messages.append(Mock(spec=ConsumerMessage, headers={}, value=data))
        return messages

    def _assert_handles_messages_response(self, expected_count: int, messages: ConsumerMessage):
        controller_mock = Mock(spec=EventController)
        with mock.patch("pm.consumers.der_gateway.handlers.EventController", controller_mock):
            handle_der_response(messages)
            instance = controller_mock.return_value
            assert instance.create_der_response.call_count == 1
            args = instance.create_der_response.call_args[0][0]
            assert len(args) == expected_count

    def test_der_response(self):
        messages_number = 500
        messages = self._make_der_response_message(messages_number)
        self._assert_handles_messages_response(messages_number, messages)

    def test_der_response_skips_bad_data(self):
        messages_number = 498
        messages = self._make_der_response_message(messages_number)
        messages += [
            Mock(
                spec=ConsumerMessage,
                headers={},
                value={
                    # missing "der_id"
                    "controlId": "1234",
                    "status": "4",
                    "time": 1635489900,
                },
            ),
            Mock(
                spec=ConsumerMessage,
                headers={},
                value={
                    "edevId": "fakeder",
                    "controlId": "1234",
                    "status": "not an int",
                    "time": 1635489900,
                },
            ),
        ]
        self._assert_handles_messages_response(messages_number, messages)
