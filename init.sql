CREATE TABLE IF NOT EXISTS logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP,
    service VARCHAR(50),
    request_id VARCHAR(100),
    action VARCHAR(50),
    status VARCHAR(50),
    source VARCHAR(50)
);