import mysql.connector
from mysql.connector import Error
import pymongo
import os

from dotenv import load_dotenv

def create_mysql_connection():
    load_dotenv()
    try:
        connection = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DB"),
        )
        return connection
    except Error as e:
        print(f"The error '{e}' occurred")

def create_mongo_connection():
    load_dotenv()
    try:
        client = pymongo.MongoClient(f"mongodb://{os.getenv('MONGO_HOST')}:{os.getenv('MONGO_PORT')}/")
        return client
    except Error as e:
        print(f"The error '{e}' occurred")