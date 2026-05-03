USE giraffe;
CREATE TABLE employee(
emp_id INT PRIMARY KEY,
first_name VARCHAR(40),
last_name VARCHAr(40),
birth_date DATE,
sex VARCHAR(1),
salary INT,
super_id INT DEFAULT NULL, -- foreign key
branch_id int -- foreign key
);
-- the foreign keys can not yet be set as such, as employee table and branch table don't exist yet.
CREATE TABLE branch(
branch_id INT PRIMARY KEY,
branch_name VARCHAR(40),
mgr_id INT,
mgr_start_date DATE,
FOREIGN KEY(mgr_id) REFERENCES employee(emp_id) ON DELETE SET NULL -- always when creating foreign key
);

-- EXEC sp_help branch
-- ALTER TABLE branch DROP CONSTRAINT FK__branch__mgr_id__151B244E
-- DROP TABLE branch

-- EXEC sp_help employee
-- ALTER TABLE employee DROP CONSTRAINT FK__employee__branch__0D7A0286
-- DROP TABLE employee

ALTER TABLE employee
ADD FOREIGN KEY(branch_id)
REFERENCES branch(branch_id) ON DELETE SET NULL;
GO -- Signals the end of a batch of statements. Important here, becaue CREATE TRIGGER must be the first statement of a batch, so we start a new one

-- ALTER TABLE employee
-- ADD FOREIGN KEY(super_id)
-- REFERENCES employee(emp_id) ON DELETE NO ACTION; 
-- SQL Server Limitation, cant 'ON DELETE SET NULL' fora foreign key that references a column in the same table.
-- Apparently this would require SSMS to perform two action at once at the same table which SSMS is not capable/ fond of
-- Solution: Build my own trigger? (See Tutorial 14)
CREATE TRIGGER employee_Parent_emp_id_Child_super_id_ON_DELETE_SET_NULL
ON employee
AFTER DELETE
AS UPDATE employee SET super_id = NULL WHERE super_id NOT IN (SELECT emp_id FROM employee)
GO-- SIGNALS end of a batch. Now, it marks taht the trigger is finished and taht what follows after is not part of the trigger anymore
-- DELETE FROM employee WHERE emp_id = 102
-- SELECT * FROM employee

CREATE TABLE client (
client_id INT PRIMARY KEY,
client_name VARCHAR(40),
branch_id INT,
FOREIGN KEY(branch_id) REFERENCES branch(branch_id) ON DELETE SET NULL
);

CREATE TABLE works_with(
emp_id INT,
client_id INT,
total_sales INT,
PRIMARY KEY(emp_id, client_id),
FOREIGN KEY(emp_id) REFERENCES employee(emp_id) ON DELETE CASCADE,
FOREIGN KEY(client_id) REFERENCES client(client_id) ON DELETE CASCADE 
);

CREATE TABLE branch_supplier (
branch_id INT,
supplier_name VARCHAR(40),
supply_type VARCHAR(40),
PRIMARY KEY(branch_id, supplier_name),
FOREIGN KEY(branch_id) REFERENCES branch(branch_id) ON DELETE CASCADE
);

-- Corporate
INSERT INTO employee VALUES(100, 'David', 'Wallace', '1967-11-17', 'M', 250000, NULL, NULL); -- corporate branch hasn't been created yet

INSERT INTO branch VALUES(1, 'Corporate', 100, '2006-02-09'); 

UPDATE employee
SET branch_id = 1
WHERE emp_id = 100; -- jetzt, wo die branch existiert, kann sie auch im employee table gesetzt werden

INSERT INTO employee VALUES(101, 'Jan', 'Levinson', '1961-05-11', 'F', 110000, 100, 1);

-- Scranton
INSERT INTO employee VALUES(102, 'Michael', 'Scott', '1964-03-15', 'M', 75000, 100, NULL);

INSERT INTO branch VALUES(2, 'Scranton', 102, '1992-04-06');

UPDATE employee
SET branch_id = 2
WHERE emp_id = 102;

INSERT INTO employee VALUES(103, 'Angela', 'Martin', '1971-06-25', 'F', 63000, 102, 2);
INSERT INTO employee VALUES(104, 'Kelly', 'Kapoor', '1980-02-05', 'F', 55000, 102, 2);
INSERT INTO employee VALUES(105, 'Stanley', 'Hudson', '1958-02-19', 'M', 69000, 102, 2);

-- Stamford
INSERT INTO employee VALUES(106, 'Josh', 'Porter', '1969-09-05', 'M', 78000, 100, NULL);

INSERT INTO branch VALUES(3, 'Stamford', 106, '1998-02-13');

UPDATE employee
SET branch_id = 3
WHERE emp_id = 106;

INSERT INTO employee VALUES(107, 'Andy', 'Bernard', '1973-07-22', 'M', 65000, 106, 3);
INSERT INTO employee VALUES(108, 'Jim', 'Halpert', '1978-10-01', 'M', 71000, 106, 3);


-- BRANCH SUPPLIER
INSERT INTO branch_supplier VALUES(2, 'Hammer Mill', 'Paper');
INSERT INTO branch_supplier VALUES(2, 'Uni-ball', 'Writing Utensils');
INSERT INTO branch_supplier VALUES(3, 'Patriot Paper', 'Paper');
INSERT INTO branch_supplier VALUES(2, 'J.T. Forms & Labels', 'Custom Forms');
INSERT INTO branch_supplier VALUES(3, 'Uni-ball', 'Writing Utensils');
INSERT INTO branch_supplier VALUES(3, 'Hammer Mill', 'Paper');
INSERT INTO branch_supplier VALUES(3, 'Stamford Lables', 'Custom Forms');

-- CLIENT
INSERT INTO client VALUES(400, 'Dunmore Highschool', 2);
INSERT INTO client VALUES(401, 'Lackawana Country', 2);
INSERT INTO client VALUES(402, 'FedEx', 3);
INSERT INTO client VALUES(403, 'John Daly Law, LLC', 3);
INSERT INTO client VALUES(404, 'Scranton Whitepages', 2);
INSERT INTO client VALUES(405, 'Times Newspaper', 3);
INSERT INTO client VALUES(406, 'FedEx', 2);

-- WORKS_WITH
INSERT INTO works_with VALUES(105, 400, 55000);
INSERT INTO works_with VALUES(102, 401, 267000);
INSERT INTO works_with VALUES(108, 402, 22500);
INSERT INTO works_with VALUES(107, 403, 5000);
INSERT INTO works_with VALUES(108, 403, 12000);
INSERT INTO works_with VALUES(105, 404, 33000);
INSERT INTO works_with VALUES(107, 405, 26000);
INSERT INTO works_with VALUES(102, 406, 15000);
INSERT INTO works_with VALUES(105, 406, 130000);

SELECT * FROM employee;

-- TEst if the Trigger replacing the ON DELTE SET NULL statement has worked
DELETE FROM employee where emp_id = 102
SELECT * FROM employee;