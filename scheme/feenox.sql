DROP SCHEMA IF EXISTS feenox CASCADE;
CREATE SCHEMA IF NOT EXISTS feenox;

CREATE TABLE IF NOT EXISTS feenox.toll_group (
    id INTEGER GENERATED ALWAYS AS IDENTITY,
    code VARCHAR(255) NOT NULL,
    description VARCHAR(255) NOT NULL,
    CONSTRAINT pk_toll_group_id
        PRIMARY KEY (id),
    CONSTRAINT uq_toll_group_code
        UNIQUE (code)
)
;

CREATE TABLE IF NOT EXISTS feenox.toll (
    id CHAR(36) NOT NULL,
    toll_country CHAR(2) NOT NULL,
    toll_group VARCHAR(255) NOT NULL,
    toll_genre CHAR(1) NOT NULL,
    toll_source VARCHAR(255),
    acquisition_date TIMESTAMP NOT NULL,
    customer_code VARCHAR(255) NOT NULL,
    contract_code VARCHAR(255) NOT NULL,
    sign_of_transaction CHAR(1) NOT NULL,
    net_amount NUMERIC(11, 5) NOT NULL,
    gross_amount NUMERIC(11, 5) NOT NULL,
    vat_rate NUMERIC(4, 2) NOT NULL,
    currency_code CHAR(3) NOT NULL,
    exchange_rate NUMERIC(11, 5),
    network_code VARCHAR(255),
    entry_gate_code VARCHAR(255),
    entry_gate_description VARCHAR(255),
    entry_date TIMESTAMP,
    exit_gate_code VARCHAR(255) NOT NULL,
    exit_gate_description VARCHAR(255) NOT NULL,
    exit_date TIMESTAMP NOT NULL,
    distance NUMERIC(7, 2),
    device_type VARCHAR(255) NOT NULL,
    device_serial_number VARCHAR(255) NOT NULL,
    device_service_pan VARCHAR(255),
    vehicle_plate VARCHAR(255) NOT NULL,
    vehicle_country CHAR(2) NOT NULL,
    vehicle_euro_class VARCHAR(255),
    tariff_class VARCHAR(255),
    invoice_article VARCHAR(255),
    invoice_number VARCHAR(255),
    invoice_date TIMESTAMP,
    global_identifier VARCHAR(255) NOT NULL,
    recording_date TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_toll_id
        PRIMARY KEY (id),
    CONSTRAINT fk_toll_toll_group
        FOREIGN KEY (toll_group)
        REFERENCES feenox.toll_group (code)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,
    CONSTRAINT chk_toll_sign_of_transaction
        CHECK (sign_of_transaction IN ('+', '-')),
    CONSTRAINT chk_toll_vat_rate
        CHECK (vat_rate >= 0),
    CONSTRAINT chk_toll_distance
        CHECK (distance >= 0),
    CONSTRAINT uq_toll_global_identifier
        UNIQUE (global_identifier)
)
;

CREATE UNIQUE INDEX idx_toll_global_identifier
    ON feenox.toll (global_identifier)
;

CREATE TABLE IF NOT EXISTS feenox.document (
    id CHAR(36) NOT NULL,
    customer_code VARCHAR(255) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    document_date DATE NOT NULL,
    publication_date DATE NOT NULL,
    document_type VARCHAR(255) NOT NULL,
    document_category VARCHAR(255),
    recording_date TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_document_id
        PRIMARY KEY (id),
    CONSTRAINT uq_document_filename
        UNIQUE (filename)
)
;

CREATE UNIQUE INDEX idx_document_filename
    ON feenox.document (filename)
;

REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA feenox FROM feenox;
ALTER DEFAULT PRIVILEGES IN SCHEMA feenox REVOKE SELECT, INSERT, UPDATE ON TABLES FROM feenox;
REVOKE ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA feenox FROM feenox;
ALTER DEFAULT PRIVILEGES IN SCHEMA feenox REVOKE EXECUTE ON FUNCTIONS FROM feenox;
REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA feenox FROM feenox;
ALTER DEFAULT PRIVILEGES IN SCHEMA feenox REVOKE USAGE, SELECT ON SEQUENCES FROM feenox;
DROP USER IF EXISTS feenox;

CREATE USER feenox WITH PASSWORD 'Feenox!2025';
GRANT USAGE ON SCHEMA feenox TO feenox;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA feenox TO feenox;
ALTER DEFAULT PRIVILEGES IN SCHEMA feenox GRANT SELECT, INSERT, UPDATE ON TABLES TO feenox;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA feenox TO feenox;
ALTER DEFAULT PRIVILEGES IN SCHEMA feenox GRANT EXECUTE ON FUNCTIONS TO feenox;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA feenox TO feenox;
ALTER DEFAULT PRIVILEGES IN SCHEMA feenox GRANT USAGE, SELECT ON SEQUENCES TO feenox;
