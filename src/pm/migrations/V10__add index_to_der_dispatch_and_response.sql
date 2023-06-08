-- create an index on der id in the contract table
CREATE INDEX idx_der_id ON contract (der_id);

-- create an index on contract_id
CREATE INDEX idx_contract_id ON der_dispatch (contract_id);

-- create an index on control_id
CREATE INDEX idx_control_id ON der_response (control_id);