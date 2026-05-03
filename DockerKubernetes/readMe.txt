Example of Containerizing a Pipeline that
1) Scrapes Stock Market Data
2) Uses a Spark-ETL Pipeline to clean and save the data
3) Creates a simple Streamlit Dashboard to depict the data


Directories:
- Docker: Contains everything neccessary to create the Docker Imigaes as well as the files to run a MultiContainer App
- Kubernetes: Build ontop of the Docker Images to Control the containers using Kubernetes