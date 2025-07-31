import os

from dotenv import find_dotenv, load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://{}:{}@cluster0.ra7lzz2.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

dotenv_path = find_dotenv(filename='.env.dev', usecwd=True)
load_dotenv(dotenv_path=dotenv_path)
Mongo_URL = 'mongodb+srv://{}:{}@{}/?retryWrites=true&w=majority&appName=Cluster0"'.format(
    os.getenv('DB_MONGO_USER'),
              os.getenv('DB_MONGO_PASSWORD'),
              os.getenv('DB_MONGO_URL'))

# Create a new client and connect to the server
client = MongoClient(Mongo_URL, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)