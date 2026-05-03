USE giraffe
CREATE TABLE trigger_test(
	message VARCHAR(100)
);
GO
CREATE TRIGGER my_trigger ON employee
AFTER INSERT
AS INSERT INTO trigger_test VALUES('added new employee')
GO


INSERT INTO employee
VALUES(109, 'Oscar', 'Martinez', '1968-02-19', 'M', 69000, 106, 3);

SELECT * FROM trigger_test;

DROP TRIGGER my_trigger;

EXEC sp_columns employee

GO
CREATE TRIGGER my_trigger ON employee
AFTER INSERT
AS INSERT INTO trigger_test SELECT first_name from inserted
GO

INSERT INTO employee VALUES(110, 'Kevin', 'Malone', '1978-02-19', 'M', 69000, 106, 3);
SELECT * FROM trigger_test;

DROP TRIGGER IF EXISTS my_trigger;

GO
Create TRIGGER my_trigger on employee
AFTER INSERT
AS INSERT INTO trigger_test SELECT
CASE WHEN inserted.sex = 'M' THEN ('added male employee')
	WHEN inserted.sex = 'F' THEN ('added female employee')
	ELSE ('added nonbinary employee')
	END as SEX FROM inserted
GO

INSERT INTO employee VALUES(111, 'Pam', 'Beesly', '1988-02-19', 'F', 69000, 106, 3);

SELECT * FROM trigger_test