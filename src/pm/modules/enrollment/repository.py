from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from pm.modules.enrollment.enums import EnrollmentRequestStatus
from pm.modules.enrollment.models.enrollment import EnrollmentRequest
from pm.topics import EnrollmentMessage
from shared.exceptions import Error
from shared.repository import SQLRepository


class EnrollmentRequestRepository(SQLRepository):
    def get_all(self) -> Sequence[EnrollmentRequest]:
        stmt = select(EnrollmentRequest).order_by(EnrollmentRequest.id)
        return self.session.execute(stmt).unique().scalars().all()

    def get(self, enrollment_request_id: int) -> Optional[EnrollmentRequest]:
        """Gets the enrollment"""
        stmt = select(EnrollmentRequest).where(EnrollmentRequest.id == enrollment_request_id)
        return self.session.execute(stmt).unique().scalar_one_or_none()

    def get_enrollment_request_or_raise(self, enrollment_request_id: int) -> EnrollmentRequest:
        """Gets the enrollment.
        Raises an error if enrollment is not found
        """
        enrollment = self.get(enrollment_request_id)
        if not enrollment:
            raise EnrollmentNotFound(
                errors={"error": "Not Found"},
                message=f"Enrollment with id {enrollment_request_id} is not found",
            )
        return enrollment

    def save_enrollment_request(self, enrollment: EnrollmentRequest) -> int:
        """Saves a enrollment and publishes on pm.enrollment topic"""
        _id: int
        self.session.add(enrollment)
        self.session.flush()
        EnrollmentMessage.add_to_outbox(self.session, enrollment.to_dict())
        _id = enrollment.id
        return _id

    def get_enrollments_for_report(self, program_id: int) -> Sequence[EnrollmentRequest]:
        """
        Returns a list of enrollment request for the report. Only enrollments with status ACCEPTED
        and REJECTED are included. Also, if more than one enrollment request has the same
        program_id + service_provider_id + der_id combination, we only return the one that was
        added most recently
        """
        stmt = (
            (
                select(EnrollmentRequest)
                .distinct(
                    EnrollmentRequest.program_id,
                    EnrollmentRequest.service_provider_id,
                    EnrollmentRequest.der_id,
                )
                .where(EnrollmentRequest.program_id == program_id)
                .where(
                    EnrollmentRequest.enrollment_status.in_(
                        [EnrollmentRequestStatus.ACCEPTED, EnrollmentRequestStatus.REJECTED]
                    )
                )
                .options(joinedload(EnrollmentRequest.program))
            )
            .order_by(
                EnrollmentRequest.program_id,
                EnrollmentRequest.service_provider_id,
                EnrollmentRequest.der_id,
            )
            .order_by(EnrollmentRequest.created_at.desc())
        )
        return self.session.execute(stmt).unique().scalars().all()


class EnrollmentNotFound(Error):
    pass
