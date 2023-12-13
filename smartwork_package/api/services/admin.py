from fastapi import APIRouter,Depends,HTTPException
from elasticsearch import Elasticsearch
from api.services.oauth import get_current_active_user,User
from typing import Annotated
from pydantic import BaseModel
from jose import JWTError, jwt
from api.services.oauth import pwd_context
from api.resources.constants import PORT,PASSWORD,USERNAME,HOST
import time
es = Elasticsearch(HOST+str(PORT),basic_auth=(USERNAME,PASSWORD),verify_certs=False)
from api.resources.custom_router import LoggingRoute

router = APIRouter(prefix="/admin",route_class=LoggingRoute,tags=["Admin"])


class FullUser(BaseModel):
    group: str
    language: str
    questionnaire:dict
    role:str
    username: str
    password: str


@router.post("/adduser")
async def adduser(
    # current_user: Annotated[User, Depends(get_current_active_user)],
    user_data:FullUser
):
    print(user_data.password)
    if not es.indices.exists(index="account"):
        es.indices.create(index = 'account')
    if not es.indices.exists(index="baseline"):
        es.indices.create(index = 'baseline')
    try:
        res = es.index(index='account', id=user_data.username, 
                document={
                    'userid': user_data.username,
                    'password': pwd_context.hash(user_data.password),
                    'country': user_data.language,
                    'clinician': 'NTNU',
                    'rights': user_data.role,
                    'isaccountnonexpired': True,
                    'isaccountnonlocked': True,
                    'iscredentialsnonexpired': True,
                    'isenabled': True,
                    'date':time.time()}
        )
        es.indices.refresh(index='account')
        
        res = es.index(index='baseline', id=user_data.username, 
                document={
                    'userid': user_data.username,
                    'questionnaire':user_data.questionnaire
                    }
        )
        es.indices.refresh(index='baseline')
    except:
        raise HTTPException(status_code=500)

    return "User was added"