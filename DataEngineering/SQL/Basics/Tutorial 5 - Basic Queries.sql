USE giraffe;
SELECT * FROM student; -- * = All rows

INSERT INTO student VALUES('Jack', 'Biology');
INSERT INTO student VALUES('Claire', 'Chemistry');
INSERT INTO student(name, major) VALUES('Nils', 'NSFW Furry Artist');

SELECT name, major
FROM student;

SELECT student.name, student.major -- Spezifizierung, von welchem df. Wichtig wenn später mit mehreren gearbeitet wird
FROM student;

SELECT name, major
FROM student
ORDER BY name; -- DESC am Schluss für descedning order. Default ist ASC für ascending

SELECT *
FROM student
ORDER BY major, student_id DESC; -- frist by major, then by student_id 

SELECT Top 2 *
FROM student
ORDER BY major, student_id DESC;
-- LIMIT 2; LIMIT x at the end for MYSQL, Top x at the beginning for SMSS

SELECT *
FROM student
WHERE major <> 'Biology'; -- <> ist not equal

SELECT *
FROM student
WHERE name IN ('Claire', 'Nils', 'Daddy');
