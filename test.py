import requests
import mysql.connector
MYSQL_HOST = 'localhost'
MYSQL_PORT = 3307  # Updated port
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'root_password'
MYSQL_DB = 'user_management'

conn = mysql.connector.connect(
    host=MYSQL_HOST,
    port=MYSQL_PORT,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=MYSQL_DB
)
