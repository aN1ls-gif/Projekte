USE WorldEvents

-------------- Replace the following Query using a CTE. --------------
SELECT
	CASE
		WHEN year(e.EventDate) < 1900 THEN
			'19th century and earlier'
		WHEN year(e.EventDate) < 2000 THEN
			'20th century'
		ELSE '21th century'
	END AS Era,
	COUNT(e.EventID)
FROM
	tblEvent AS e
GROUP BY
	CASE
		WHEN year(e.EventDate) < 1900 THEN
			'19th century and earlier'
		WHEN year(e.EventDate) < 2000 THEN
			'20th century'
		ELSE '21th century'
	END

GO
-- The CTE
WITH Era_CTE (Era, EventID) 
AS 
(
	SELECT
	CASE
		WHEN year(e.EventDate) < 1900 THEN
			'19th century and earlier'
		WHEN year(e.EventDate) < 2000 THEN
			'20th century'
		ELSE '21th century'
	END AS Era, e.EventID
	FROM tblEvent AS e
)
-- The outer query referecing the CTE
SELECT Era_CTE.Era as 'Era', COUNT(Era_CTE.EventID)
FROM Era_CTE
GROUP BY Era_CTE.Era

-------------------------------------------
USE Music_01
-- The following code was provided by teh practive task
select
	s.Venue_ID
	,count(*) as Count_shows
	,avg(s.Revenue_$) as Avg_revenue_$
	,avg(s.Tickets_sold) as Avg_tickets_sold
from
	dbo.Show as s
group by
	s.Venue_ID
----
GO
WITH Venue_CTL (ID, ShowCount, AvgRevenue$, AvTicketsSold)
AS
(
select
	s.Venue_ID
	,count(*) as Count_shows
	,avg(s.Revenue_$) as Avg_revenue_$
	,avg(s.Tickets_sold) as Avg_tickets_sold
from
	dbo.Show as s
group by
	s.Venue_ID
)
SELECT
v.Venue,
v.Opening_date,
c.City,
Venue_CTL.ShowCount, 
Venue_CTL.AvgRevenue$,
Venue_CTL.AvTicketsSold
FROM
Venue as v
JOIN Venue_CTL ON Venue_CTL.ID = v.Venue_ID
JOIN City as c ON c.City_ID = v.City_ID
ORDER BY Venue_CTL.ShowCount DESC




-------------------------------------------------------------------------
GO
USE WorldEvents

GO
WITH 
SPACE_CTE (Country, c_Event) AS
(
	SELECT tblCountry.CountryName, tblCategory.CategoryName FROM tblEvent
	JOIN tblCountry ON tblCountry.CountryID = tblEvent.CountryID
	JOIN tblCategory ON tblCategory.CategoryID = tblEvent.CategoryID
	WHERE tblCountry.CountryName = 'Space'
),
NON_SPACE_CTE (Country, c_Event) AS
(
	SELECT tblCountry.CountryName, tblCategory.CategoryName FROM tblEvent
	JOIN tblCountry ON tblCountry.CountryID = tblEvent.CountryID
	JOIN tblCategory ON tblCategory.CategoryID = tblEvent.CategoryID
	WHERE tblCountry.CountryName <> 'Space'
)
SELECT DISTINCT NON_SPACE_CTE.Country AS 'Country' FROM NON_SPACE_CTE
WHERE NON_SPACE_CTE.c_Event IN (SELECT DISTINCT SPACE_CTE.c_Event FROM SPACE_CTE)



----------------------------------------------------------------------------
GO
USE WorldEvents

--- Without CTE
SELECT tblCategory.CategoryName, tblEvent.EventName FROM tblEvent
JOIN tblCategory ON tblCategory.CategoryID = tblEvent.CategoryID
WHERE tblEvent.EventName LIKE '[A-M]%'

--- With CTE
WITH A_to_M_CTE (CategoryID, EventName)
AS
(
	SELECT tblEvent.CategoryID, tblEvent.EventName FROM tblEvent
	WHERE tblEvent.EventName LIKE '[A-M]%'
)
SELECT tblCategory.CategoryName, A_to_M_CTE.EventName FROM A_to_M_CTE
JOIN tblCategory ON tblCategory.CategoryID = A_to_M_CTE.CategoryID


---------------------------------------------------------------------------------
GO 
USE WorldEvents

WITH
TopCountries_CTE (CountryID, Nr_of_Events)
AS
(
	SELECT TOP 3 tblCountry.CountryID, COUNT(tblEvent.EventID) FROM tblCountry
	JOIN tblEvent ON tblEvent.CountryID = tblCountry.CountryID
	GROUP BY tblCountry.CountryID
	ORDER BY COUNT(tblEvent.EventID) DESC
),
TopCategories_CTE (CategoryID, No_of_Events)
AS
(
	SELECT TOP 3 tblCategory.CategoryID, COUNT(tblEvent.EventID) FROM tblCategory
	JOIN tblEvent ON tblEvent.CategoryID = tblCategory.CategoryID
	GROUP BY tblCategory.CategoryID
	ORDER BY COUNT(tblEvent.EventID) DESC
)
SELECT tblCountry.CountryName, tblCategory.CategoryName, COUNT(tblEvent.EventID) as 'Nr of Events' FROM TopCountries_CTE
CROSS JOIN TopCategories_CTE
JOIN tblCountry ON tblCountry.CountryID = TopCountries_CTE.CountryID
JOIN tblCategory ON tblCategory.CategoryID = TopCategories_CTE.CategoryID
JOIN tblEvent ON tblEvent.CountryID = TopCountries_CTE.CountryID AND tblEvent.CategoryID = TopCategories_CTE.CategoryID
GROUP BY tblCountry.CountryName, tblCategory.CategoryName
ORDER BY COUNT(tblEvent.EventID) DESC
