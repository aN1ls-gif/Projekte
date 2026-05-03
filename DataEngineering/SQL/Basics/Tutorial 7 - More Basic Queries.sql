Use giraffe
-- Find all employees
SELECT *
FROM employee;

-- Find all clients
SELECT *
FROM client;

-- find all emmployees ordered by salary
SELECT *
FROM employee
ORDER BY salary DESC;

-- find all employees ordered by sex, then name
SELECT *
FROM employee
ORDER BY sex, first_name, last_name;

-- Find the first 5 employees in the table
SELECT TOP 5 *
FROM employee
-- LIMIT 5;

-- FInd first and last name of all employees
SELECT first_name, last_name
FROM employee;

-- Find the fornames and surenames of all employees
SELECT first_name AS forename, last_name AS surename
FROM employee;

-- Find out all the different genders
SELECT DISTINCT sex
FROM employee;