Batch - Processing:
Batch_ETL_Functions.py : All the functions for the Pipeline
Batch_ETL_Pipeline.ipynb : Execute the Pipeline
Batch_ETL_Functions.py : Simple Unittests for the functions
Batch_ETL_Analysis.ipynb : Explore PySparks native plotting


Stream - Processing:
Stream_Scrape.ipynb : Scrape stock market data from Finance.yahoo and seperate it into date-seperated .json files
Stream_DataSimulation.ipynb : Move the .json files from the storage Folder into the Source Folder, simoulating the continous arrivel of new data. Alternativly all logs, checkpoints, source-files and tables can be deleted to reset the Streaming process
Stream_ETL.ipynb : The Streaming ETL Pipeline
Stream-Dashboard.py : Access the Delta tables created by the Streaming pipline and use Streamlit to create a Basic Dashboard, testing Plotly and Altair

Folders:
Logs : Contains log files from the Batch ETL
BatchData : Contains all the data related to the Batch ETL Pipeline
StreamData : Contains all the data related to the Stream ETL Pipeline