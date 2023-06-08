from sqlalchemy import select

from pm.modules.enrollment.models.enrollment import EnrollmentRequest


class EnrollmentMixin:
    """Some helper methods for enrollment tests."""

    def _get_enrollment_body(self, program_id: int, service_provider_id: int, der_id: str):
        return [
            dict(
                general_fields=dict(
                    program_id=program_id,
                    service_provider_id=service_provider_id,
                    der_id=der_id,
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

    def _get_enrollment_request_from_db(self, db_session, enrollment_request_id):
        with db_session() as session:
            stmt = select(EnrollmentRequest).where(EnrollmentRequest.id == enrollment_request_id)
            return session.execute(stmt).unique().scalar_one()
