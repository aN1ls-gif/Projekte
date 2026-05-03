use Music_01
go

select
	t.Track_name
	,a.Title as Album_name
	,t.Track_mins
	,t.Track_secs
from
	dbo.Track as t
	join dbo.Album as a on a.Album_ID = t.Album_ID
order by
	t.Track_name asc