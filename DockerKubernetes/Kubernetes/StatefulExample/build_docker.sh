# Create Images for the python scripts
docker build -f Dockerfiles/Database_Init -t an1ls/my_sql_init:latest .
docker build -f Dockerfiles/Dashboard -t an1ls/my_sql_dashboard:latest .

docker image push an1ls/my_sql_init:latest
docker image push an1ls/my_sql_dashboard:latest