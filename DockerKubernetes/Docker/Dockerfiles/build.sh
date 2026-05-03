# start the minikube cluster
# minikube start

# Create Images for the python scripts
docker build -f PySpark_Base -t an1ls/pyspark_base:ver_1.0 ..
docker build -f Stream_Scrape_lite -t an1ls/stream_scrape:ver_2.0 ..
docker build -f Stream_ETL_lite -t an1ls/stream_etl:ver_2.0 ..
docker build -f Stream_Dashboard_lite -t an1ls/stream_dashboard:ver_2.0 ..

# Create the network that the Multi-Container App will use
# While docker-compose automatically creates a Network for the containers to share (if non is specified), I want to create a network and connect to it manually for practice purposes.
docker network create Spark_Dashboard

# Create Volumes
docker volume create DeltaTable
docker volume create DeltaCheckpoint
docker volume create DeltaArchive
docker volume create ScrapeSource
docker volume create ScrapeArchive
docker volume create ScrapeCheckpoint

# Docker-Compose fr Multi-Container app
docker compose -f docker-compose.yaml up 