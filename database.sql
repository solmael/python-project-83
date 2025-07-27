DROP TABLE IF EXISTS url_checks CASCADE;
DROP TABLE IF EXISTS urls CASCADE;

CREATE TABLE urls (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL CHECK (name <> ''),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE url_checks (
    id SERIAL PRIMARY KEY,
    url_id INTEGER NOT NULL REFERENCES urls(id),
    status_code INTEGER,
    h1 TEXT,
    title TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
