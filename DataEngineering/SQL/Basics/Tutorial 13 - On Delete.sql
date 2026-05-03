USE giraffe
SELECT * FROM branch; -- Michael Scot was deleted from employee. His id was referenced as foreign key in the branch table.
-- When Miacheal was deleted, his id and thereby the reference disappeared. We set that, in this case, the references mgr_id is
-- to be set to NULL

SELECT * FROM employee; -- same happend to the super_ids

DELETE FROM branch_supplier
WHERE branch_id = 2;

SELECT * FROM branch_supplier; -- The refrenced foreign key for branch_id 2 was deleted. Because we set ON DELETE CASCADE, deleting a key
-- that is referenced by a FOREIGN KEY deletes the entire row that FOREIGN KEY was in. That is necessary in this case, beause the FOREIGN KEY was
-- part of the PRIMARY KEY, which can't be NULL.
