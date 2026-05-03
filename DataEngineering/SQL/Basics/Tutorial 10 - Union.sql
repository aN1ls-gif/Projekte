USE giraffe
-- find a lost of employee and branch names
SELECT first_name
FROM employee;

SELECT branch_name
FROM branch;

SELECT employee.first_name, branch.branch_name
FROM employee, branch; -- war meine Idee. Klappt technisch, aber kombiniert alles mit allem

SELECT first_name -- this is used as column name
FROM employee
UNION
SELECT branch_name
FROM branch; -- everything is returned in a single column, no doubles, no combinations  

-- each SELECT must call the same amount of columns for UNION to work
-- The data must have the same datatypes

SELECT first_name AS names
FROM employee
UNION
SELECT branch_name
FROM branch
UNION
SELECT client_name
FROM client;

-- find a list of all clients and branch suppliers' names
SELECT client_name, client.branch_id -- makes it more readble. 
FROM client
UNION
SELECT supplier_name, branch_supplier.branch_id
FROM branch_supplier;

-- find a list of all money spent or earned by the company
SELECT salary, emp_id
FROM employee
UNION
SELECT total_sales, emp_id
FROM works_with;
