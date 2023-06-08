DROP TABLE IF EXISTS report;
DROP TABLE IF EXISTS contract_details;
DROP TABLE IF EXISTS event_details;

CREATE TABLE report (
    id INTEGER,
    report_type VARCHAR(100) NOT NULL,
    report_details VARCHAR(100) NOT NULL,
    program_id INTEGER NOT NULL,
    service_provider_id INTEGER NOT NULL,
    start_report_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    end_report_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by VARCHAR(100) NOT NULL,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    total_events INTEGER NOT NULL,
    average_event_duration FLOAT NOT NULL,
    dispatched_der INTEGER NOT NULL,
    total_der_in_program INTEGER NOT NULL,
    avail_flexibility_up FLOAT NOT NULL,
    avail_flexibility_down FLOAT NOT NULL,
    constraint_violations INTEGER NOT NULL,
    constraint_warnings INTEGER NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE contract_details (
    id INTEGER,
    report_id INTEGER NOT NULL,
    der_id INTEGER NOT NULL,
    service_provider_id INTEGER NOT NULL,
    enrollment_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    contract_constraint_id INTEGER NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (report_id) REFERENCES report (id),
    FOREIGN KEY (contract_constraint_id) REFERENCES contract_constraint_summary (id),
    FOREIGN KEY (der_id) REFERENCES der_info (id),
    FOREIGN KEY (service_provider_id) REFERENCES service_provider (id)
);

CREATE TABLE event_details (
    id INTEGER,
    report_id INTEGER,
    dispatch_id VARCHAR(100) NOT NULL,
    event_start TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    event_end TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    number_of_dispatched_der INTEGER NOT NULL,
    number_of_opted_out_der INTEGER NOT NULL,
    requested_capacity NUMERIC(20, 4) NOT NULL,
    dispatched_capacity NUMERIC(20, 4) NOT NULL,
    event_status VARCHAR(100) NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (report_id) REFERENCES report (id)
);
