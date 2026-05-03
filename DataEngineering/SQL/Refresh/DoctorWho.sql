USE DoctorWho

------- Create table containing only episodes featuring Karen Gillan as Amy Pond and/or those written by Steven Moffat.
GO
WITH 
Best_Table(EpisodeID, Title, SeriesNumber, EpisodeNumber, Why) AS 
(
SELECT E.EpisodeId, E.Title, E.SeriesNumber, E.EpisodeNumber, A.AuthorName AS 'Why' FROM tblEpisode as E
JOIN tblAuthor as A ON A.AuthorId = E.AuthorId
WHERE A.AuthorName = 'Steven Moffat'
UNION
SELECT E.EpisodeId, E.Title, E.SeriesNumber, E.EpisodeNumber, C.CompanionName FROM tblEpisode as E
JOIN tblEpisodeCompanion AS EC ON EC.EpisodeId = E.EpisodeId
JOIN tblCompanion AS C ON C.CompanionId = EC.CompanionId
WHERE C.CompanionName = 'Amy Pond'
)
SELECT Top 15 Title, Count(Title) AS 'Number of Mentions' FROM Best_Table
GROUP BY Title
ORDER BY Title ASC

------- Create a stored procedure that creates two tables:
------- 1. Most frequently-appearning companions (by episode)
------- 2. Most frequently-appearning enemies (by episode)

GO
DROP PROCEDURE IF EXISTS spMostFrequentAppearance

GO
CREATE PROCEDURE spMostFrequentAppearance
AS
SELECT TOP 3 C.CompanionName, Count(E.EpisodeId) AS Episodes FROM tblEpisode as E
JOIN tblEpisodeCompanion AS EC ON EC.EpisodeId = E.EpisodeId
JOIN tblCompanion as C ON C.CompanionId = EC.CompanionId
GROUP BY C.CompanionName
ORDER BY Episodes DESC

SELECT TOP 3 EN.EnemyName, Count(E.EpisodeId) AS Episodes FROM tblEpisode as E
JOIN tblEpisodeEnemy AS EE ON EE.EpisodeId = E.EpisodeId
JOIN tblEnemy as EN ON EN.EnemyId = EE.EnemyId
GROUP BY EN.EnemyName
ORDER BY Episodes DESC
GO

EXECUTE spMostFrequentAppearance
GO

------------ Create a table-valued function
------------ Table of Episodes for a series number and author

DROP FUNCTION IF EXISTS fnChosenEpisodes

GO
CREATE FUNCTION fnChosenEpisodes(
@SeriesNumber int,
@AuthorName varchar(100)
)
RETURNS TABLE
AS
RETURN
SELECT E.Title AS 'Title', A.AuthorName AS 'Author', D.DoctorName AS 'Doctor' FROM tblEpisode AS E
JOIN tblAuthor AS A ON A.AuthorId = E.AuthorId
JOIN tblDoctor AS D On D.DoctorId = E.DoctorId
WHERE E.SeriesNumber = @SeriesNumber AND A.AuthorName LIKE '%' + @AuthorName + '%'

GO
SELECT * FROM dbo.fnChosenEpisodes(1, 'russel')


---------------- Create a table containing the names of all Stored Procedure and Created Functions

GO
WITH
SYSTEM_TABLE_CTE (ObjectType, ObjectName, DateCreated)
AS(
	SELECT SYSTEM_TABLE.type_desc,
	SYSTEM_TABLE.name, 
	SYSTEM_TABLE.create_date
	FROM sys.objects AS SYSTEM_TABLE
	WHERE  SYSTEM_TABLE.type_desc LIKE 'SQL%FUNCTION' OR SYSTEM_TABLE.type_desc = 'SQL_STORED_PROCEDURE'
)
SELECT
CASE
	WHEN STC.ObjectType = 'SQL_SCALAR_FUNCTION' THEN 'Scalar Function'
	WHEN STC.ObjectType = 'SQL_STORED_PROCEDURE' THEN 'Stored Procedure'
	ELSE 'Table Function'
END AS 'ObjectType',
STC.ObjectName,
FORMAT(STC.DateCreated, 'yyyy-MM-dd') AS 'DateCreated'
FROM SYSTEM_TABLE_CTE AS STC
ORDER BY STC.ObjectType