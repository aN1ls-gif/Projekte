USE giraffe
-- find the number of employees
SELECT COUNT(emp_id)
FROM employee;

-- find number of supervisors
SELECT COUNT(super_id)
FROM employee;

-- find the number of female employees born after 1970
SELECT COUNT(emp_id)
FROM employee
WHERE sex = 'F' AND birth_date >= '1970-01-01'; 

-- find the AVERAGE off all employees salaries
SELECT AVG(salary)
FROM employee;

-- find the SUM of all employees salaries
SELECT SUM(salary)
FROM employee;

-- find out how many males and females there are
SELECT COUNT(sex), sex
FROM employee
GROUP BY sex;

-- find the total sales of each salesman
SELECT SUM(total_sales), emp_id
FROM works_with
GROUP BY emp_id;

-- find the total expense of each client
SELECT SUM(total_sales), client_id
FROM works_with
GROUP BY client_id;