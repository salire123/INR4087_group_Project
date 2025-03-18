# src\backend\src\utils\db.py
import mysql.connector
from mysql.connector import Error
import pymongo
import redis
import os
from .env import Config

from contextlib import contextmanager
from minio import Minio

@contextmanager
def connect_mysql():
    connection = None
    try:
        connection = mysql.connector.connect(
            host=Config.get("MYSQL_HOST"),
            user=Config.get("MYSQL_USER"),
            password=Config.get("MYSQL_PASSWORD"),
            database=Config.get("MYSQL_DATABASE"),
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
    client = None
    try:
        client = pymongo.MongoClient(Config.get("MONGO_URI"))
        db = client[Config.get("MONGO_DATABASE")]
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
    try:
        minioClient = Minio(Config.get("MINIO_ENDPOINT"),
            access_key=Config.get("MINIO_ACCESS_KEY"),
            secret_key=Config.get("MINIO_SECRET_KEY"),
            secure=False
        )
        bucket_name = Config.get("MINIO_BUCKET")
        url = f"{Config.get('MINIO_ENDPOINT')}/{bucket_name}"
        yield minioClient, bucket_name, url
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise

        
@contextmanager
def redis_connection(db: int = 0):
    # 创建 Redis 连接
    client = redis.Redis(
        host=Config.get("REDIS_HOST"),
        port=Config.get("REDIS_PORT"),
        db  = db,
        decode_responses=True  # 确保返回字符串而不是字节
    )
    try:
        # 提供 Redis 客户端给调用者使用
        yield client
    finally:
        # 关闭连接
        client.close()      
    

    