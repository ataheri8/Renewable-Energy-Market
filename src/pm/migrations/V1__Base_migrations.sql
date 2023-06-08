DROP TABLE IF EXISTS program;
DROP TABLE IF EXISTS service_provider;
DROP TABLE IF EXISTS der_response;
DROP TABLE IF EXISTS der_info;
DROP TABLE IF EXISTS avail_operating_months;
DROP TABLE IF EXISTS avail_service_window;
DROP TABLE IF EXISTS dispatch_notification;
DROP TABLE IF EXISTS dispatch_opt_out;
DROP TABLE IF EXISTS enrollment_request;
DROP TABLE IF EXISTS contract;
DROP TABLE IF EXISTS der_dispatch;
DROP TABLE IF EXISTS contract_constraint_summary;

CREATE TABLE program (
        id SERIAL NOT NULL, 
        name TEXT, 
        program_type VARCHAR(255) NOT NULL, 
        program_category VARCHAR(255), 
        start_date TIMESTAMP WITH TIME ZONE, 
        end_date TIMESTAMP WITH TIME ZONE, 
        program_priority VARCHAR(255), 
        availability_type VARCHAR(255), 
        notification_type VARCHAR(255), 
        resource_eligibility_criteria JSONB, 
        holiday_exclusions JSONB, 
        check_der_eligibility BOOLEAN, 
        define_contractual_target_capacity BOOLEAN, 
        dispatch_constraints JSONB, 
        demand_management_constraints JSONB, 
        status VARCHAR(255) NOT NULL, 
        limit_type VARCHAR(255), 
        control_type VARCHAR(255), 
        calculation_frequency VARCHAR(255), 
        schedule_time_horizon_timeperiod VARCHAR(255), 
        schedule_time_horizon_number INTEGER, 
        schedule_timestep_mins INTEGER, 
        control_options JSONB, 
        dispatch_type VARCHAR(255), 
        track_event BOOLEAN, 
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
        PRIMARY KEY (id)
);

CREATE TABLE service_provider (
        id SERIAL NOT NULL, 
        uuid TEXT NOT NULL, 
        name TEXT NOT NULL, 
        service_provider_type VARCHAR(255) NOT NULL, 
        status VARCHAR(255) NOT NULL, 
        primary_contact JSONB NOT NULL, 
        notification_contact JSONB, 
        address JSONB, 
        deleted BOOLEAN DEFAULT 'false', 
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
        PRIMARY KEY (id), 
        UNIQUE (uuid)
);

CREATE TABLE der_response (
        id SERIAL NOT NULL, 
        der_id TEXT NOT NULL, 
        der_response_status INTEGER NOT NULL, 
        der_response_time TIMESTAMP WITH TIME ZONE NOT NULL, 
        control_id TEXT NOT NULL, 
        is_opt_out BOOLEAN NOT NULL, 
        PRIMARY KEY (id)
);

CREATE TABLE der_info (
        id SERIAL NOT NULL, 
        der_id TEXT NOT NULL, 
        name TEXT NOT NULL, 
        is_deleted BOOLEAN DEFAULT 'false', 
        der_type VARCHAR(255) NOT NULL, 
        nameplate_rating INTEGER NOT NULL, 
        nameplate_rating_unit VARCHAR(255) NOT NULL, 
        resource_type VARCHAR(255) NOT NULL, 
        created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
        updated_at TIMESTAMP WITH TIME ZONE, 
        service_provider_id INTEGER, 
        PRIMARY KEY (id), 
        UNIQUE (der_id), 
        FOREIGN KEY(service_provider_id) REFERENCES service_provider (id)
);

CREATE TABLE avail_operating_months (
        id SERIAL NOT NULL, 
        program_id INTEGER NOT NULL, 
        jan BOOLEAN, 
        feb BOOLEAN, 
        mar BOOLEAN, 
        apr BOOLEAN, 
        may BOOLEAN, 
        jun BOOLEAN, 
        jul BOOLEAN, 
        aug BOOLEAN, 
        sep BOOLEAN, 
        oct BOOLEAN, 
        nov BOOLEAN, 
        dec BOOLEAN, 
        PRIMARY KEY (id), 
        FOREIGN KEY(program_id) REFERENCES program (id)
);

CREATE TABLE avail_service_window (
        id SERIAL NOT NULL, 
        program_id INTEGER NOT NULL, 
        start_hour INTEGER, 
        end_hour INTEGER, 
        mon BOOLEAN, 
        tue BOOLEAN, 
        wed BOOLEAN, 
        thu BOOLEAN, 
        fri BOOLEAN, 
        sat BOOLEAN, 
        sun BOOLEAN, 
        PRIMARY KEY (id), 
        FOREIGN KEY(program_id) REFERENCES program (id)
);

CREATE TABLE dispatch_notification (
        id SERIAL NOT NULL, 
        program_id INTEGER NOT NULL, 
        text TEXT, 
        lead_time INTEGER, 
        PRIMARY KEY (id), 
        FOREIGN KEY(program_id) REFERENCES program (id)
);

CREATE TABLE dispatch_opt_out (
        id SERIAL NOT NULL, 
        program_id INTEGER NOT NULL, 
        timeperiod VARCHAR(255) NOT NULL, 
        value INTEGER, 
        PRIMARY KEY (id), 
        FOREIGN KEY(program_id) REFERENCES program (id)
);

CREATE TABLE enrollment_request (
        id SERIAL NOT NULL, 
        program_id INTEGER NOT NULL, 
        service_provider_id INTEGER NOT NULL, 
        der_id TEXT NOT NULL, 
        enrollment_status VARCHAR(255) NOT NULL, 
        dynamic_operating_envelopes JSONB, 
        demand_response JSONB, 
        rejection_reason VARCHAR(255), 
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
        PRIMARY KEY (id), 
        FOREIGN KEY(program_id) REFERENCES program (id), 
        FOREIGN KEY(service_provider_id) REFERENCES service_provider (id), 
        FOREIGN KEY(der_id) REFERENCES der_info (der_id)
);

CREATE TABLE contract (
        id SERIAL NOT NULL, 
        program_id INTEGER NOT NULL, 
        service_provider_id INTEGER NOT NULL, 
        der_id TEXT NOT NULL, 
        contract_status VARCHAR(255) NOT NULL, 
        contract_type VARCHAR(255) NOT NULL, 
        enrollment_request_id INTEGER NOT NULL, 
        dynamic_operating_envelopes JSONB, 
        demand_response JSONB, 
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
        PRIMARY KEY (id), 
        CONSTRAINT uc_contract UNIQUE (program_id, service_provider_id, der_id), 
        FOREIGN KEY(program_id) REFERENCES program (id), 
        FOREIGN KEY(service_provider_id) REFERENCES service_provider (id), 
        FOREIGN KEY(der_id) REFERENCES der_info (der_id), 
        UNIQUE (enrollment_request_id), 
        FOREIGN KEY(enrollment_request_id) REFERENCES enrollment_request (id)
);

CREATE TABLE der_dispatch (
        id SERIAL NOT NULL, 
        event_id TEXT NOT NULL, 
        start_date_time TIMESTAMP WITH TIME ZONE NOT NULL, 
        end_date_time TIMESTAMP WITH TIME ZONE NOT NULL, 
        event_status TEXT NOT NULL, 
        control_id TEXT NOT NULL, 
        control_type TEXT NOT NULL, 
        control_command NUMERIC(20, 4) NOT NULL, 
        contract_id INTEGER NOT NULL, 
        max_total_energy NUMERIC(20, 4) NOT NULL, 
        cumulative_event_duration_mins INTEGER NOT NULL, 
        PRIMARY KEY (id), 
        FOREIGN KEY(contract_id) REFERENCES contract (id)
);

CREATE TABLE contract_constraint_summary (
        id SERIAL NOT NULL, 
        contract_id INTEGER NOT NULL, 
        cumulative_event_duration_day INTEGER, 
        cumulative_event_duration_day_warning BOOLEAN, 
        cumulative_event_duration_day_violation BOOLEAN, 
        cumulative_event_duration_week INTEGER, 
        cumulative_event_duration_week_warning BOOLEAN, 
        cumulative_event_duration_week_violation BOOLEAN, 
        cumulative_event_duration_month INTEGER, 
        cumulative_event_duration_month_warning BOOLEAN, 
        cumulative_event_duration_month_violation BOOLEAN, 
        cumulative_event_duration_year INTEGER, 
        cumulative_event_duration_year_warning BOOLEAN, 
        cumulative_event_duration_year_violation BOOLEAN, 
        cumulative_event_duration_program_duration INTEGER, 
        cumulative_event_duration_program_duration_warning BOOLEAN, 
        cumulative_event_duration_program_duration_violation BOOLEAN, 
        max_number_of_events_per_timeperiod_day INTEGER, 
        max_number_of_events_per_timeperiod_day_warning BOOLEAN, 
        max_number_of_events_per_timeperiod_day_violation BOOLEAN, 
        max_number_of_events_per_timeperiod_week INTEGER, 
        max_number_of_events_per_timeperiod_week_warning BOOLEAN, 
        max_number_of_events_per_timeperiod_week_violation BOOLEAN, 
        max_number_of_events_per_timeperiod_month INTEGER, 
        max_number_of_events_per_timeperiod_month_warning BOOLEAN, 
        max_number_of_events_per_timeperiod_month_violation BOOLEAN, 
        max_number_of_events_per_timeperiod_year INTEGER, 
        max_number_of_events_per_timeperiod_year_warning BOOLEAN, 
        max_number_of_events_per_timeperiod_year_violation BOOLEAN, 
        max_number_of_events_per_timeperiod_program_duration INTEGER, 
        max_number_of_events_per_timeperiod_program_duration_warning BOOLEAN, 
        max_number_of_events_per_timeperiod_program_duration_violation BOOLEAN, 
        opt_outs_day INTEGER, 
        opt_outs_day_warning BOOLEAN, 
        opt_outs_day_violation BOOLEAN, 
        opt_outs_week INTEGER, 
        opt_outs_week_warning BOOLEAN, 
        opt_outs_week_violation BOOLEAN, 
        opt_outs_month INTEGER, 
        opt_outs_month_warning BOOLEAN, 
        opt_outs_month_violation BOOLEAN, 
        opt_outs_year INTEGER, 
        opt_outs_year_warning BOOLEAN, 
        opt_outs_year_violation BOOLEAN, 
        opt_outs_program_duration INTEGER, 
        opt_outs_program_duration_warning BOOLEAN, 
        opt_outs_program_duration_violation BOOLEAN, 
        max_total_energy_per_timeperiod_day NUMERIC(20, 4), 
        max_total_energy_per_timeperiod_day_warning BOOLEAN, 
        max_total_energy_per_timeperiod_day_violation BOOLEAN, 
        max_total_energy_per_timeperiod_week NUMERIC(20, 4), 
        max_total_energy_per_timeperiod_week_warning BOOLEAN, 
        max_total_energy_per_timeperiod_week_violation BOOLEAN, 
        max_total_energy_per_timeperiod_month NUMERIC(20, 4), 
        max_total_energy_per_timeperiod_month_warning BOOLEAN, 
        max_total_energy_per_timeperiod_month_violation BOOLEAN, 
        max_total_energy_per_timeperiod_year NUMERIC(20, 4), 
        max_total_energy_per_timeperiod_year_warning BOOLEAN, 
        max_total_energy_per_timeperiod_year_violation BOOLEAN, 
        max_total_energy_per_timeperiod_program_duration NUMERIC(20, 4), 
        max_total_energy_per_timeperiod_program_duration_warning BOOLEAN, 
        max_total_energy_per_timeperiod_program_duration_violation BOOLEAN, 
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, 
        PRIMARY KEY (id), 
        UNIQUE (contract_id), 
        FOREIGN KEY(contract_id) REFERENCES contract (id)
);
