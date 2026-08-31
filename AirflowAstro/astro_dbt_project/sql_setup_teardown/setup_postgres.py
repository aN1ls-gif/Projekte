
from sqlalchemy import create_engine, text
from dotenv import load_dotenv, dotenv_values
import os
from pathlib import Path
import re

path = Path(os.path.dirname(__file__))
env_path = os.path.join(path.parent.absolute(), '.env')
config_dict = dotenv_values(env_path)


with open(f"{path}/setup_postgres.sql", "r") as f:
    queries = re.split(r";\s*", f.read())[:-1]

# for query in queries:
#     if query.startswith("--"):
#         continue
#     print("Query Start:")
#     print(query)
#     print("Query End\n")

db_string = f"postgresql+psycopg2://{config_dict['SUPERUSER']}:{config_dict['SUPERPWD']}\
@{config_dict['PSQL_IP']}/airflow_pipeline"
print(db_string)
engine = create_engine(db_string)
with engine.connect() as conn:
    for query in queries:
        ## Splitting the file into the singular queries removes the semicolon. Therefore, it needs to be added back 
        if query.startswith("--"):
            continue
        conn.execute(text(query+";"))
    conn.commit()
    