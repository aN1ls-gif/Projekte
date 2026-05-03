USE WorldEvents

------ First 5 Events in Chronological Order
GO
SELECT
TOP 5
E.EventName AS 'What',
E.EventDetails AS 'Details'
FROM tblEvent AS E
ORDER BY E.EventDate ASC