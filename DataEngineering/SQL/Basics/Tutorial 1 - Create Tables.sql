create database giraffe; -- in schemas an der Seite auswählen

USE giraffe
CREATE TABLE student (
student_id INT PRIMARY KEY,
name VARCHAR(20),
major VARCHAR(20));
-- or
-- CREATE TABLE student(
-- student_id INT,
-- name VARCHAR(20),
-- major VARCHAR(20),
-- PRIMARY KEY(student_id));

EXEC sp_help student; -- in MySQL, EXEC sp_help is simply 'DESCRIBE'
DROP TABLE student;
CREATE TABLE student (
student_id INT PRIMARY KEY,
name VARCHAR(20),
major VARCHAR(20));
ALTER TABLE student ADD gpa DECIMAL(3, 2);
ALTER TABLE student DROP COLUMN gpa;