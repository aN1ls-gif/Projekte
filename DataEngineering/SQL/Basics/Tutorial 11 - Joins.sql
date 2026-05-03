USE giraffe
-- combine rows of 2 or more tables based of a common column between them
INSERT INTO branch VALUES(4, 'Buffalo', NULL, NULL); -- Needed this extra information for this excercise
SELECT * FROM branch;
 
 -- Find all branches and the names of their managers
 SELECT employee.emp_id, employee.first_name, branch.branch_name
 FROM employee
 JOIN branch -- Only the rows that matched get included for the SELECT
 ON employee.emp_id = branch.mgr_id; 
 
 -- Find all branches and the names of their managers
 SELECT employee.emp_id, employee.first_name, branch.branch_name
 FROM employee
 LEFT JOIN branch -- All of the rows of the LEFT(first) table get included
 ON employee.emp_id = branch.mgr_id; 
 
  -- Find all branches and the names of their managers
 SELECT employee.emp_id, employee.first_name, branch.branch_name
 FROM employee
 RIGHT JOIN branch -- All of the rows of the RIGHT(second) table get included
 ON employee.emp_id = branch.mgr_id; 
 
 