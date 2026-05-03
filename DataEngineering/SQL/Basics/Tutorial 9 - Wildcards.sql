USE giraffe
-- find all client's who are an LLC
SELECT *
FROM client
WHERE client_name LIKE '%LLC' ; -- any number of characters and LLC at the end

-- find any branch suppliers who are in the label business
SELECT *
FROM branch_supplier
WHERE supplier_name LIKE '%Label%'; -- any number of characters, Label, any number of characters

-- select any employee bron in October
SELECT *
FROM employee
WHERE birth_date LIKE '____-10%'; -- any 4 digit yearnumber, -10, any characters

-- find any clients who are schools
SELECT *
FROM client
WHERE client_name LIKE '%school%';