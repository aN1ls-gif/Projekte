-- Find names of all employees who have
-- sold over 30,000 to a single client
USE giraffe
-- my try
SELECT DISTINCT(employee.emp_id), employee.first_name, employee.last_name
FROM employee
JOIN works_with
ON employee.emp_id = works_with.emp_id
WHERE works_with.total_sales > 30000; -- it worked :)

-- the official solution
SELECT employee.first_name, employee.last_name
FROM employee
WHERE employee.emp_id IN (
SELECT works_with.emp_id 
FROM works_with
WHERE works_with.total_sales > 30000); -- the correct emp_id get returned from the query within the IN() statement and
-- used by the WHERE as filtering key.

-- find all clients who are handled by the branch
-- that Micheal Scott manages
-- Assume you know Micheal's ID
SELECT client.client_name as "Micheal Scott's clients"
FROM client
WHERE client.branch_id = (
	SELECT TOP 1 branch.branch_id
	FROM branch
	WHERE branch.mgr_id = 102);