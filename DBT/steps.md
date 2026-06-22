***1. Create new role, Password and database and connect to it***

***1.1 New Role and ist Password:***

&#x09;CREATE ROLE dbt\_user WITH LOGIN PASSWORD 'dbt\_password';

1.2 New Database and its owner:

&#x09;CREATE DATABASE dbt\_tutorial OWNER dbt\_user;

1.3 Connect to the Databse:

&#x09;\\c dbt\_tutorial



***2. Create Schemas and grant permissions.***

***2.1***

&#x09;CREATE SCHEMA IF NOT EXISTS raw AUTHORIZATION dbt\_user;

&#x09;CREATE SCHEMA IF NOT EXISTS analytics AUTHORIZATION dbt\_user;



***2.2 Grants (simple approach for local dev).***  ***Important; These only grant permission to use the Schema in General or create new tables/views in the Schema. It does not grant any privilages for the tables/ views once they are created***

&#x09;GRANT USAGE ON SCHEMA raw, analytics TO dbt\_user;

&#x09;GRANT CREATE ON SCHEMA analytics TO dbt\_user; -- dbt builds models here



**2.3 Change Default permissions for all tables in a Schema. This applies to all tables that will be created from now on, but does not affect any tables/views that have already been created**

&#x09;ALTER DEFAULT PRIVILEGES IN SCHEMA raw GRANT SELECT ON TABLES TO dbt\_user;

&#x09;ALTER DEFAULT PRIVILEGES IN SCHEMA analytics GRANT SELECT ON TABLES TO dbt\_user;



&#x09;

***3. Create Tables and enter data (raw data, start of the Pipeline)***

***3.1 Raw tables***

&#x09;CREATE TABLE IF NOT EXISTS raw.customers (

&#x20;   		id            INTEGER PRIMARY KEY,

&#x20;   		first\_name    TEXT,

&#x20;   		last\_name     TEXT,

&#x20;   		email         TEXT,

&#x20;   		created\_at    TIMESTAMP WITHOUT TIME ZONE

&#x09;);



&#x09;CREATE TABLE IF NOT EXISTS raw.orders (

&#x20;   		id            INTEGER PRIMARY KEY,

&#x20;   		user\_id       INTEGER NOT NULL REFERENCES raw.customers(id),

&#x20;   		order\_date    TIMESTAMP WITHOUT TIME ZONE,

&#x20;   		status        TEXT, -- e.g., placed, shipped, completed, returned, cancelled

&#x20;   		total\_amount  NUMERIC(10,2)

&#x09;);



&#x09;CREATE TABLE IF NOT EXISTS raw.payments (

&#x20;   		id            INTEGER PRIMARY KEY,

&#x20;   		order\_id      INTEGER NOT NULL REFERENCES raw.orders(id),

&#x20;   		payment\_method TEXT, -- e.g., credit\_card, bank\_transfer, coupon, gift\_card

&#x20;   		amount        NUMERIC(10,2) NOT NULL,

&#x20;   		paid\_at       TIMESTAMP WITHOUT TIME ZONE

&#x09;);



***3.2 Fill the tables with data***

&#x09;INSERT INTO raw.customers (id, first\_name, last\_name, email, created\_at) VALUES

&#x20;   		(1, 'Alice',   'Nguyen',  'alice@example.com',   '2023-01-05 10:00:00'),

&#x20;   		(2, 'Brian',   'Smith',   'brian@example.com',   '2023-02-10 09:13:00'),

&#x20;   		(3, 'Carla',   'Lopez',   'carla@example.com',   '2023-03-21 15:45:00'),

&#x20;   		(4, 'Diego',   'Martins', 'diego@example.com',   '2023-04-12 08:05:00'),

&#x20;   		(5, 'Emily',   'Zhao',    'emily@example.com',   '2023-05-30 20:30:00')

&#x09;ON CONFLICT DO NOTHING;



&#x09;INSERT INTO raw.orders (id, user\_id, order\_date, status, total\_amount) VALUES

&#x20;   		(100, 1, '2023-06-01 10:15:00', 'placed',    100.00),

&#x20;   		(101, 1, '2023-06-02 13:00:00', 'completed',  60.00),

&#x20;   		(102, 2, '2023-06-03 16:20:00', 'returned',   35.00),

&#x20;   		(103, 3, '2023-06-04 18:40:00', 'placed',     75.00),

&#x20;   		(104, 5, '2023-06-05 08:05:00', 'cancelled', 150.00)

&#x09;ON CONFLICT DO NOTHING;



&#x09;INSERT INTO raw.payments (id, order\_id, payment\_method, amount, paid\_at) VALUES

&#x20;   		(1000, 100, 'credit\_card',  60.00, '2023-06-01 10:20:00'),

&#x20;   		(1001, 100, 'gift\_card',    40.00, '2023-06-01 10:21:00'),

&#x20;   		(1002, 101, 'credit\_card',  60.00, '2023-06-02 13:05:00'),

&#x20;   		(1003, 102, 'credit\_card',  35.00, '2023-06-03 16:25:00'),

&#x20;   		(1004, 104, 'credit\_card', 150.00, '2023-06-05 08:07:00')

&#x09;ON CONFLICT DO NOTHING;

