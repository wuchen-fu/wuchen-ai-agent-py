import os

from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from dotenv import find_dotenv, load_dotenv

dotenv_path = find_dotenv(filename='.env.dev', usecwd=True)
load_dotenv(dotenv_path=dotenv_path)
MSQL_UEL = 'mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8mb4'.format(
    os.getenv('DB_MYSQL_USER'),
              os.getenv('DB_MYSQL_PASSWORD'),
              os.getenv('DB_MYSQL_URL'),
os.getenv('DB_MYSQL_PORT'),
os.getenv('DB_MYSQL_DATABASE')
)
print(MSQL_UEL)

db_mysql = SQLDatabase.from_uri(MSQL_UEL)
print(f'dialect:{db_mysql.dialect}')
print(db_mysql.get_usable_table_names())
print(db_mysql.run('select * from ai_chat_message limit 2'))
SQLDatabaseToolkit(db=db_mysql)