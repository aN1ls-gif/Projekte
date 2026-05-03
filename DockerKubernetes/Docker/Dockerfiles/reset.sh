# Remove images
docker rmi Stream_Scrape
docker rmi Stream_ETL
docker rmi Stream_Dashboard

# remove network
docker network rm Spark_Dashboard

# remove volumes (if not connected to a running container)
docker volume prune