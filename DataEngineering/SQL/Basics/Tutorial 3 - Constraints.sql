USE giraffe;

EXEC sp_help student;
SELECT * FROM student;   -- alles noch drin
INSERT INTO student VALUES(4, 'Mike', 'Computer Science');
DROP TABLE student;
CREATE TABLE student (
student_id INT,
name VARCHAR(20) NOT NULL, -- np NULL allowed for name
major VARCHAR(20) UNIQUE, -- each major only ones allowed
PRIMARY KEY(student_id)); -- NOT NULL + UNIQUE

INSERT INTO student VALUES(1, 'Jack', 'Biology');
INSERT INTO student VALUES(2, 'Kate', 'Sociology');
INSERT INTO student(student_id, name) VALUES(3, 'Claire');
INSERT INTO student VALUES(4, 'Jack', 'Biology'); -- Führt nun zu einem Fehler, da Biology doppelt wäre
INSERT INTO student VALUES(5, 'Mike', 'Computer Science');

DROP TABLE student;
CREATE TABLE student (
student_id INT,
name VARCHAR(20), 
major VARCHAR(20) DEFAULT 'undecided', 
PRIMARY KEY(student_id)); 
INSERT INTO student VALUES(1, 'Jack', 'Biology');
INSERT INTO student VALUES(2, 'Kate', 'Sociology');
INSERT INTO student(student_id, name) VALUES(3, 'Claire');
-- INSERT INTO student VALUES(4, 'Jack', 'Biology'); -- Führt nun zu einem Fehler, da Biology doppelt wäre
INSERT INTO student VALUES(5, 'Mike', 'Computer Science');


DROP TABLE student;
CREATE TABLE student (
student_id INT IDENTITY, -- IDENTIY isn MySQL is Auto_Icrement
name VARCHAR(20), 
major VARCHAR(20) DEFAULT 'undecided', 
PRIMARY KEY(student_id)); 
INSERT INTO student(name, major) VALUES('Jack', 'Biology');
INSERT INTO student(name, major) VALUES('Kate', 'Sociology');
INSERT INTO student(name) VALUES('Claire');
-- INSERT INTO student(name, major) VALUES('Jack', 'Biology'); -- Führt nun zu einem Fehler, da Biology doppelt wäre
INSERT INTO student(name, major) VALUES('Mike', 'Computer Science');

