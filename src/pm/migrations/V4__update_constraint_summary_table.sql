--  Add a new date column 'day' to the table
ALTER TABLE contract_constraint_summary ADD column day DATE;

-- Remove unique index on contract_id
ALTER TABLE contract_constraint_summary DROP CONSTRAINT contract_constraint_summary_contract_id_key;

-- Create unique index on contract_id and day
CREATE UNIQUE INDEX contract_constraint_summary_day_contract_id ON contract_constraint_summary (day, contract_id);