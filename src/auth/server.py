import jwt, datetime, os 
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials, HTTPBearer
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

app = FastAPI(
    title='MSA Auth',
    description='Auth',
    docs_url='/api/docs',
    version='1.0.0',
)

load_dotenv()

MYSQL_HOST = os.environ.get('MYSQL_HOST')
MYSQL_USER = os.environ.get('MYSQL_USER')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD')
MYSQL_DB = os.environ.get('MYSQL_DB')
MYSQL_PORT = os.environ.get('MYSQL_PORT', '3308')

DATABASE_URL = f'mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}'

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
)

def get_db():
    with engine.connect() as connection:
        yield connection

def create_jwt(user_name, secret, authz):
    return jwt.encode(
        {
            'user_name' : user_name,
            'exp': datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(days=1),
            'iat': datetime.datetime.now(tz=datetime.timezone.utc),
            'admin': authz,
        },
        secret,
        algorithm='HS256',
    )

@app.post('/login', summary='Log in')
async def login(auth : HTTPBasicCredentials = Depends(HTTPBasic())):

    if not auth.username or not auth.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='missing credentials',
            headers={'WWW-Authenticate': 'Basic'},
        
	)
    query = text('SELECT email, password FROM user WHERE email = :email')
    with engine.connect() as conn:
        result = conn.execute(query, {'email': auth.username})
        user_row = result.fetchone()

        if user_row is None:
            raise HTTPException(status_code=401, detail='invalid credentials')

        email, password = user_row

        if auth.password != password:
            raise HTTPException(status_code=401, detail='invalid credentials')

        token = create_jwt(auth.username, os.environ.get('JWT_SECRET'), True)
        return {'access_token': token}


@app.post('/validate')
async def validate(auth : HTTPBasicCredentials = Depends(HTTPBearer())):
    encoded_jwt = auth.credentials  # 'Bearer <token>'에서 토큰만 추출됨

    secret = os.environ.get('JWT_SECRET')
    if not secret:
        raise HTTPException(status_code=500, detail='JWT secret is not configured')
    try:
        decoded = jwt.decode(encoded_jwt, secret, algorithms=['HS256'])
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Not authorized')

    return decoded


if __name__ == '__main__':
    uvicorn.run('server:app', host='0.0.0.0', port=5000, reload=True)