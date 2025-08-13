import os, gridfs, pika, json
import uvicorn
from fastapi import FastAPI, Depends
from fastapi.security import HTTPBearer, HTTPBasicCredentials, HTTPAuthorizationCredentials, HTTPBasic
from fastapi.responses import FileResponse
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from auth_service import access
from validate_service import validate
from dotenv import load_dotenv

app = FastAPI(
    title='MSA Gateway',
    description='Gateway',
    docs_url='/api/docs',
    version='1.0.0'
)

load_dotenv()

MONGO_HOST = os.environ.get('MONGO_HOST')
MONGO_PORT = os.environ.get('MONGO_PORT')
RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST')
RABBITMQ_PORT = os.environ.get('RABBITMQ_PORT')

client = MongoClient(f"mongodb://{MONGO_HOST}:{MONGO_PORT}")

fs_videos = gridfs.GridFS(client.videos)
fs_mp3s = gridfs.GridFS(client.mp3s)

connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
channel = connection.channel()


@app.post('/login', summary='Login')
def login(request : HTTPBasicCredentials = Depends(HTTPBasic())):
    token, err = access.login(request)

    if not err:
        return token
    else:
        return err


@app.post('/validate', summary='Validate')
def login(request : HTTPBasicCredentials = Depends(HTTPBasic())):
    token, err = access.login(request)

    if not err:
        return token
    else:
        return err


if __name__ == '__main__':
    uvicorn.run('server:app', host='0.0.0.0', port=8080, reload=True)