CREATE TABLE Family_ (
    family_id SERIAL PRIMARY KEY,
    family_name VARCHAR(50) NOT NULL
);

CREATE TABLE Wallet (
    wallet_id SERIAL PRIMARY KEY,
    balance NUMERIC(12,2) DEFAULT 0,
    max_limit NUMERIC(12,2),
    transaction_limit NUMERIC(12,2)
);

CREATE TABLE User_ (
    national_id VARCHAR(14) PRIMARY KEY,
    name_ VARCHAR(50) NOT NULL,
    phone_number VARCHAR(11) UNIQUE NOT NULL,
    password_ VARCHAR(10) NOT NULL,
    failed_attempts INT DEFAULT 0,
    lock_time TIMESTAMP,
    family_id INT REFERENCES Family_(family_id),
    wallet_id INT REFERENCES Wallet(wallet_id),
    role_ VARCHAR(10) NOT NULL
);
CREATE TABLE Organization (
    organization_id SERIAL PRIMARY KEY,
    name_ VARCHAR(50) NOT NULL,
    type_ VARCHAR(50) NOT NULL,
    wallet_id INT REFERENCES Wallet(wallet_id)
);
CREATE TABLE OrganizationContact (
    organization_id INT REFERENCES Organization(organization_id),
    phone_number VARCHAR(11)
);
CREATE TABLE Transactions (
    transaction_id SERIAL PRIMARY KEY,
    from_wallet INT REFERENCES Wallet(wallet_id),
    to_wallet INT REFERENCES Wallet(wallet_id),
    amount NUMERIC(12,2) NOT NULL,
    type_ VARCHAR(50) NOT NULL,
    date_ TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

