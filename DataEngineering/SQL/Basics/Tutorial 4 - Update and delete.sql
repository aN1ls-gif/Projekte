USE giraffe
SELECT * FROM student;

UPDATE student SET major = 'Bio' WHERE major = 'Biology'; -- safe UPDATE/DELETE musste dafür deaktiviert werden.alter
UPDATE student SET major = 'Comp Sci' WHERE major = 'Computer Science';
UPDATE student SET major = 'Comp Sci' WHERE student_id = 4;
UPDATE student SET major = 'Biochemistry' WHERE major = 'Bio' OR major = 'undecided';
UPDATE student SET name = 'Tom', major = 'undecided' WHERE student_id = 1;
UPDATE student SET major = 'undecided';

DELETE FROM student WHERE student_id = 5;
DELETE FROM student; -- deletes all rows