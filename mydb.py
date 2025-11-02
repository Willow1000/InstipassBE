import mysql.connector
from dotenv import load_dotenv
load_dotenv()
import os
config =     {
        "user": os.environ['DB_USER'],
        "password":os.environ['DB_PASS'],
        'port':os.environ['DB_PORT'],
        "host":os.environ["DB_HOST"]
    }
mydb = mysql.connector.connect(**config)

mycursor = mydb.cursor()

try:
    mycursor.execute("CREATE DATABASE InstiPassDB")
except Exception as e:
    pass
finally:
    mycursor.execute("USE InstiPassDB")    