CREATE TABLE outbox (
    id SERIAL PRIMARY KEY,
    topic TEXT NOT NULL,
    headers JSONB,
    message JSONB NOT NULL,
    is_sent BOOLEAN NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_outbox_is_sent ON outbox (is_sent) WHERE is_sent = false;
