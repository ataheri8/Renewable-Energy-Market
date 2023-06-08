-- Remove unique constaint on combination of (program_id, service_provider_id, der_id)
ALTER TABLE contract DROP CONSTRAINT uc_contract;
