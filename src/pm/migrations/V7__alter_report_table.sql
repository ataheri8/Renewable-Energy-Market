ALTER TABLE contract_details RENAME TO contract_report_details;
ALTER TABLE report ALTER report_details DROP NOT NULL;
ALTER TABLE report ALTER user_id DROP NOT NULL;
ALTER TABLE report ALTER created_at DROP NOT NULL;
ALTER TABLE report ALTER updated_at DROP NOT NULL;
ALTER TABLE report ALTER total_events DROP NOT NULL;
ALTER TABLE report ALTER average_event_duration DROP NOT NULL;
ALTER TABLE report ALTER dispatched_der DROP NOT NULL;
ALTER TABLE report ALTER total_der_in_program DROP NOT NULL;
ALTER TABLE report ALTER avail_flexibility_up DROP NOT NULL;
ALTER TABLE report ALTER avail_flexibility_down DROP NOT NULL;
ALTER TABLE report ALTER constraint_violations DROP NOT NULL;
ALTER TABLE report ALTER constraint_warnings DROP NOT NULL;
