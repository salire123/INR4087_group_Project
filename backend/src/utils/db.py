# src\backend\src\utils\db.py
import mysql.connector
from mysql.connector import Error
import pymongo
import os
from dotenv import load_dotenv
from contextlib import contextmanager
import boto3
from botocore.client import Config

@contextmanager
def connect_mysql():
    load_dotenv()
    connection = None
    try:
        connection = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DATABASE"),
        )
        cursor = connection.cursor()
        yield (cursor, connection)
    except Error as e:
        print(f"The error '{e}' occurred")
        raise  # Re-raise the exception to be handled by the caller
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

@contextmanager
def connect_mongo():
    load_dotenv()
    client = None
    try:
        client = pymongo.MongoClient(os.getenv("MONGO_URI"))
        db = client[os.getenv("MONGO_DATABASE")]
        yield db
    except pymongo.errors.ConnectionFailure as e:  # Updated to ConnectionFailure
        print(f"Connection failure: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise
    finally:
        if client:
            client.close()

@contextmanager
#Minio connection
def connect_Minio():
    load_dotenv()
    try:
        minioClient = boto3.client('s3',
            endpoint_url=os.getenv("MINIO_ENDPOINT"),
            aws_access_key_id=os.getenv("MINIO_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("MINIO_SECRET_KEY"),
            config=Config(signature_version='s3v4')
        )
        bucket_name = os.getenv("MINIO_BUCKET")
        url = f"{os.getenv('MINIO_ENDPOINT')}/{bucket_name}"
        yield minioClient, bucket_name, url
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise

        
            
    

    