-------------------------------------
-- Basic Select statement utilizing (inner) joins and the HAVING statement
USE DoctorWho

SELECT a.AuthorName, d.DoctorName, COUNT(*) AS 'Episodes'
FROM tblAuthor AS a
INNER JOIN tblEpisode AS e ON a.AuthorId = e.AuthorId
INNER JOIN tblDoctor AS d ON e.DoctorId = d.DoctorId
GROUP BY a.AuthorName, d.DoctorName
HAVING COUNT(*) > 5
ORDER BY Episodes DESC

--------------------------------------------------------------
-- Function to determine difference in days between start and enddate
DROP FUNCTION IF EXISTS fnReign
GO
CREATE FUNCTION fnReign(@StartDate date, @EndDate date)
RETURNS int
AS
BEGIN 
	RETURN DateDiff(day, @StartDate,ISNULL(@EndDate, GetDate()))
END;
GO

SELECT tblDoctor.DoctorName, dbo.fnReign(tblDoctor.FirstEpisodeDate, tblDoctor.LastEpisodeDate) as Reign FROM tblDoctor
ORDER BY Reign DESC

SELECT * FROM tblDoctor WHERE tblDoctor.DoctorName = 'Peter Capaldi'  

------------------------------------
-- Simple query using joins
Use WorldEvents
-- Number of events by country and contintent
SELECT tblContinent.ContinentName as Continent, tblCountry.CountryName as Country, COUNT(*) as 'Events'
FROM tblContinent
INNER JOIN tblCountry ON tblContinent.ContinentID = tblCountry.ContinentID
INNER JOIN tblEvent ON tblCountry.CountryID = tblEvent.CountryID
GROUP BY tblContinent.ContinentName, tblCountry.CountryName
ORDER BY tblCountry.CountryName

-- With WHERE condition
-- Same as before but now ignoring Europe
SELECT tblContinent.ContinentName as Continent, tblCountry.CountryName as Country, COUNT(*) as 'Events'
FROM tblContinent
INNER JOIN tblCountry ON tblContinent.ContinentID = tblCountry.ContinentID
INNER JOIN tblEvent ON tblCountry.CountryID = tblEvent.CountryID
WHERE tblContinent.ContinentName != 'Europe'
GROUP BY tblContinent.ContinentName, tblCountry.CountryName
ORDER BY tblCountry.CountryName

-- Same as before but now ignoring Europe and only for combinations with more than 5 events
SELECT tblContinent.ContinentName as Continent, tblCountry.CountryName as Country, COUNT(*) as 'Events'
FROM tblContinent
INNER JOIN tblCountry ON tblContinent.ContinentID = tblCountry.ContinentID
INNER JOIN tblEvent ON tblCountry.CountryID = tblEvent.CountryID
WHERE tblContinent.ContinentName != 'Europe'
GROUP BY tblContinent.ContinentName, tblCountry.CountryName
HAVING Count(*) > 5
ORDER BY tblCountry.CountryName

-----------------------------------------------
USE Music_01
-- Funtction to clean varchars of " and leading/trailing spaces
DROP FUNCTION IF EXISTS fnClean_Strings

GO
CREATE FUNCTION fnClean_Strings(@String varchar(100))
RETURNS varchar(100) 
AS
BEGIN 
	Return TRIM(REPLACE(@String, '"', '')) -- Remove any quotationmarks that are part of the string
	--- Then remove all leading and trailing spacebars
END;
GO

GO
select
    dbo.fnClean_Strings(t.Track_name) as Track_Name
	,a.Title as Album_name
	,t.Track_mins
	,t.Track_secs
from
	dbo.Track as t
	join dbo.Album as a on a.Album_ID = t.Album_ID
order by
	dbo.fnClean_Strings(t.Track_name) asc;


GO

DROP FUNCTION IF EXISTS fnTrackLength

-- Combine Minutes and Seconds into a single column
GO 
CREATE FUNCTION fnTrackLength(@Minutes int, @Seconds int)
Returns varchar(5)
AS
BEGIN
	RETURN CONVERT(varchar(2), FORMAT(@Minutes, '00')) + ':' + CONVERT(varchar(2), FORMAT(@Seconds, '00'))
END;
GO

select
    dbo.fnClean_Strings(t.Track_name) as Track_Name
	,a.Title as Album_name,
	dbo.fnTrackLength(t.Track_mins,t.Track_secs) as Track_Length
from
	dbo.Track as t
	join dbo.Album as a on a.Album_ID = t.Album_ID
order by
	dbo.fnClean_Strings(t.Track_name) asc

------------------------------------------------------
USE DoctorWho
-- write a function that counts the amoutn of Episodes per Episode Type
-- Check wheter the Title contains a 'Part 1' or a 'Part 2'.
-- dbo.fnEpisodeDescription()
-- ALTER DATABASE DocotrWho SET COMPATIBILITY_LEVEL = 170 to use REGEX; but I cannot go hgher than 160
-- So I Use a chunky If ... ELSE (If ... ELSE ...) Statement
DROP FUNCTION IF EXISTS fnEpisodeDescription
GO
Create Function fnEpisodeDescription(@Title varchar(40))
Returns varchar(20)
AS 
BEGIN
	DECLARE @OutVar varchar(20)
	IF @Title LIKE '%(Part 1)' SET @OutVar = 'Part 1'
	ELSE IF @Title LIKE '%(Part 2)' SET @OutVar = 'Part 2'
		ELSE SET @OutVar = 'Single Episode'
	Return @OutVar
END
GO


SELECT dbo.fnEpisodeDescription(Title) AS 'Episode type', COUNT(*) AS 'Number of Episodes' FROM tblEpisode
GROUP BY dbo.fnEpisodeDescription(Title)


-------------------------------------------------------------------------
USE WorldEvents

-- Create A query that shows for Cateory
-- (a) The number of categories beginning with that Initial
-- (b) The average name lengths of the events belonging to that category initial

SELECT substring(UPPER(tblCategory.CategoryName), 1, 1) AS 'Initial',
COUNT(*) AS 'Nr of events with that initial',
AVG(LEN(tblEvent.EventName)) AS 'Average name length'
FROM tblCategory INNER JOIN tblEvent ON tblCategory.CategoryID = tblEvent.CategoryID
GROUP BY substring(UPPER(tblCategory.CategoryName), 1, 1)

SELECT tblEvent.EventName FROM tblEvent


---------------- 
USE WorldEvents

---- (a) get teh century each event is happening in
----- (b) count the number of events that happened in a century

DROP FUNCTION IF EXISTS	fnDateToCentury
GO
CREATE FUNCTION fnDateToCentury(@Date date)
RETURNS varchar(20)
AS
BEGIN
	-- 1. Extract Date From Year
	-- 2. Year from Date to Vachar
	-- 3. Take only the frist 2 numbers
	-- 4. Convert to integer and increase by one
	-- 5. Convert back to varchar and finalize the string
	Return CONVERT(varchar(20), CONVERT(int, LEFT(CONVERT(varchar(4), YEAR(@Date)), 2)) + 1) + 'th Century'
END
GO

SELECT dbo.fnDateToCentury(tblEvent.EventDate) as 'Century', 
Count(*) as 'Count' 
FROM tblEvent
GROUP BY dbo.fnDateToCentury(tblEvent.EventDate)
UNION
SELECT 'All' as 'Century', COUNT(*) as 'Count' FROM tblEvent


----------------------------
USE DoctorWHo

--- Query that lists for each episode year AND enemy name the number of episodes made
--- Condition 1: Only allows episodes with Docotrs born before 1970
--- Condition 2: Ignore all entries where an enemy appeared only once in a particular year

SELECT YEAR(EpisodeDate) as 'Year', EnemyName as 'Enemy', COUNT(*) as 'Number of Episodes' FROM tblEpisode
INNER JOIN tblDoctor ON tblDoctor.DoctorId = tblEpisode.DoctorId
INNER JOIN tblEpisodeEnemy ON tblEpisode.EpisodeId = tblEpisodeEnemy.EpisodeId
INNER JOIN tblEnemy ON tblEpisodeEnemy.EnemyId = tblEnemy.EnemyId
WHERE Year(BirthDate) < 1970
GROUP BY YEAR(EpisodeDate), EnemyName
HAVING COUNT(*) > 1
ORDER BY YEAR(EpisodeDate) asc, COUNT(*) desc



-----------------------------------------------
USE DoctorWho
-- 1. function to count number of companions for a given episode
-- 2. function to count the number of enemies for an episode

---- 3.
-- function to count the number of words (hint: use a combination

-- of LTRIM and RTRIM to remove leading and trailing spaces, then

-- REPLACE to change all spaces to empty strings and compare the

-- LEN of the string before and after this change!)

DROP Function if exists fnCompCount
GO
CREATE FUNCTION fnCompCount(@ID int)
RETURNS int
AS
BEGIN
	RETURN(
	SELECT COUNT(*) FROM tblEpisodeCompanion
		WHERE EpisodeId = @ID
	);
END
GO

DROP Function if exists fnEnCount
GO
CREATE FUNCTION fnEnCount(@ID int)
RETURNS int
AS
BEGIN
	RETURN(
	SELECT COUNT(*) FROM tblEpisodeEnemy
		WHERE EpisodeId = @ID
	);
END
GO

DROP FUNCTION IF EXISTS fnWordCount

GO
CREATE FUNCTION fnWordCount(@Text varchar(100))
RETURNS int
AS
BEGIN
	DECLARE @TextWithInternalSpaces varchar(100)
	DECLARE @TextWithoutInternalSpaces varchar(100)
	SET @TextWithInternalSpaces = TRIM(@Text)
	SET @TextWithoutInternalSpaces = REPLACE(@TextWithInternalSpaces, ' ', '')
	RETURN LEN(@TextWithInternalSpaces) - LEN(@TextWithoutInternalSpaces) + 1;
END

GO

SELECT
EpisodeId,
Title,
dbo.fnCompCount(EpisodeID) as 'Companions', -- method to count comapnions
dbo.fnEnCount(EpisodeId) as 'Enemies', -- method to count enemies
dbo.fnWordCount(Title) as 'Words' -- Count the number of words in the title
FROM tblEpisode
ORDER BY Words DESC 



-----------------------------------------------------------------------------
--- Create a stored procedure for the DoctorWho Database
-- Input: Doctor Name. Output: List of all companions of that doctor.
-- Exception: If no Doctor is named, list all companions

USE DoctorWho

Go 
CREATE PROCEDURE spCompanionsForDoctor 
@NamePart varchar(40) = ''
AS
SELECT DISTINCT tblCompanion.CompanionName as Companions FROM tblCompanion
JOIN tblEpisodeCompanion ON tblEpisodeCompanion.CompanionId = tblCompanion.CompanionId
JOIN tblEpisode ON tblEpisode.EpisodeId = tblEpisodeCompanion.EpisodeId
JOIN tblDoctor ON tblDoctor.DoctorId = tblEpisode.DoctorId
WHERE tblDoctor.DoctorName LIKE '%' + @NamePart + '%'
GO

EXECUTE spCompanionsForDoctor 'Ecc'
EXECUTE spCompanionsForDoctor 'matt'
EXECUTE spCompanionsForDoctor


-----------------------------------------------------------
--- Display Dates with correct suffixees

USE WorldEvents

SELECT EventName, 
DateName(weekday, EventDate) 
+ ' ' + 
DateName(day, EventDate) 
+
CASE 
WHEN DAY(EventDate) = 1 THEN 'st'
WHEN DAY(EventDate) = 2 THEN 'nd'
WHEN DAY(EventDate) = 3 THEN 'rd'
ELSE 'th'
END
+ ' ' + 
DateName(month , EventDate) 
+ ' ' + 
DateName(year, EventDate) as 'Full date'
FROM tblEvent
ORDER BY EventDate