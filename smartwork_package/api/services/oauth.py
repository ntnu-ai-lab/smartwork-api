import json
import shutil
from typing import Any, Optional


from fastapi import APIRouter, Form, Request
from pydantic import BaseModel
from datetime import datetime, timedelta,timezone
from typing import Annotated, Union

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from elasticsearch import Elasticsearch
# from api.resources.constants import PORT,PASSWORD,USERNAME,HOST
from api.resources.custom_router import LoggingRoute
from api.resources.constants import ES_PASSWORD,ES_URL,CLIENT_ID,SECRET_KEY,CLIENT_IDS


es = Elasticsearch(ES_URL,basic_auth=("elastic",ES_PASSWORD),verify_certs=False)



router = APIRouter(prefix="/oauth",route_class=LoggingRoute,tags=["Oauth"])
# router.route_class=LoggingRoute
# to get a string like this run:
# openssl rand -hex 32

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 6*30*24*60*60




class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


class User(BaseModel):
    userid: str
    isenabled: Union[bool, None] = None
    admin: bool = False
    

class UserInDB(User):
    password: str
    language: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")




oauth2_scheme = OAuth2PasswordBearer(tokenUrl="oauth/token",description="Either authenticate as a user using username and password or as a client using client_id and client_secret to access the admin endpoints. When entering as a client use Request Body for the client_id and client_secret.")




# print(pwd_context.hash("secret"))


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)




def get_user(username):
    if not es.indices.exists(index="account"):
        es.indices.create(index = 'account')
    res = es.search(index="account", query={'match' : {"_id":username}})
    if not res["hits"]["hits"]:
        return None
    return UserInDB(**res.body["hits"]["hits"][0]["_source"])


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        admin: str = payload.get("access")
        if admin is not None:
            return User(userid="temp",admin=True,isenabled=True)
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
):
    if not current_user.isenabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

class OAuth2PasswordRequestFormCustom(OAuth2PasswordRequestForm):
    #just to make username and password optional so we can have client side only authorization, not sure if that is common though....
    def __init__(
        self,
        grant_type: str = Form(default=None, regex="password"),
        username: Optional[str] = Form(default=None),
        password: Optional[str] = Form(default=None),
        scope: str = Form(default=""),
        client_id: Optional[str] = Form(default=None),
        client_secret: Optional[str] = Form(default=None),
    ):
        self.grant_type = grant_type
        self.username = username
        self.password = password
        self.scopes = scope.split()
        self.client_id = client_id
        self.client_secret = client_secret


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestFormCustom, Depends()]
):
    """
    Used to generate tokens, both for users and clients
    """
    print(form_data,"jinkers")
    if form_data.client_id:
        if form_data.client_id!=CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect client_id",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if CLIENT_IDS[form_data.client_id] != form_data.client_secret:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect client_secret",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
        data={"sub": "temp","access":"admin"}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.userid}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Returns the user that is signed in
    """
    return current_user


# @router.get("/users/me/items/")
# async def read_own_items(
#     current_user: Annotated[User, Depends(get_current_active_user)]
# ):
    
#     return [{"item_id": "Foo", "owner": current_user.username}]