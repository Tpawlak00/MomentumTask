CREATE TABLE IF NOT EXISTS books (
    id SERIAL PRIMARY KEY,
    serial_num INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    is_borrowed BOOLEAN NOT NULL DEFAULT FALSE,
    borrowed_by INTEGER,
    borrowed_at TIMESTAMP
);
