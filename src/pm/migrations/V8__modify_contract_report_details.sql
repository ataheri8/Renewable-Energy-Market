ALTER TABLE contract_report_details DROP COLUMN der_id;
ALTER TABLE contract_report_details ADD COLUMN der_id TEXT;
ALTER TABLE contract_report_details DROP COLUMN report_id;
ALTER TABLE event_details DROP COLUMN report_id;
ALTER TABLE report DROP COLUMN id;
ALTER TABLE report ADD COLUMN id SERIAL PRIMARY KEY;
ALTER TABLE contract_report_details DROP COLUMN id;
ALTER TABLE contract_report_details ADD COLUMN id SERIAL PRIMARY KEY;
ALTER TABLE event_details DROP COLUMN id;
ALTER TABLE event_details ADD COLUMN id SERIAL PRIMARY KEY;
ALTER TABLE contract_report_details ADD COLUMN report_id INTEGER;
ALTER TABLE contract_report_details ADD CONSTRAINT fk_report_id FOREIGN KEY (report_id) REFERENCES report(id);
ALTER TABLE event_details ADD COLUMN report_id INTEGER;
ALTER TABLE event_details ADD CONSTRAINT fk_report_id FOREIGN KEY (report_id) REFERENCES report(id);
