from fastapi import APIRouter,Depends,HTTPException
from elasticsearch import Elasticsearch,helpers
from api.services.oauth import get_current_active_user,User
from typing import Annotated
from pydantic import BaseModel
from jose import JWTError, jwt
from api.services.oauth import pwd_context
import datetime
from api.resources.constants import ES_PASSWORD,ES_URL,LS_MAPPING
es = Elasticsearch(ES_URL,basic_auth=("elastic",ES_PASSWORD),verify_certs=False)
from api.resources.custom_router import LoggingRoute
router = APIRouter(prefix="/admin",route_class=LoggingRoute,tags=["Admin"])


class FullUser(BaseModel):
    questionnaire:dict
    username: str
    password: str
    language:str

class PartialUser(BaseModel):
    questionnaire:dict
    username: str
    
class PasswordReset(BaseModel):
    username: str
    password: str

# def format_data(questionnaire):
#     comorbidities=""
#     # if 
#     painsites=""
#     for i in range(1,10):
#         painsites+=questionnaire["PainSites_SQ_00"]
@router.post("/reset_password")
async def adduser(
    current_user: Annotated[User, Depends(get_current_active_user)],
    user_data:PasswordReset
): 
    if not current_user.admin:
        raise HTTPException(403,"You need admin access to create users")
    es.update(index='account', id=user_data.username,
            doc={
                'password': user_data.password,
                }
    )
    es.indices.refresh(index='account')
    return "Password was reset"

@router.post("/adduser")
async def adduser(
    current_user: Annotated[User, Depends(get_current_active_user)],
    user_data:FullUser
): 
    
    if not current_user.admin:
        raise HTTPException(403,"You need admin access to create users")
    # try:
    res = es.index(index='account', id=user_data.username, 
            document={
                'userid': user_data.username,
                'password': None,
                'language': user_data.language,
                'clinician': 'NTNU',
                # 'rights': user_data.role,
                'isaccountnonexpired': True,
                'isaccountnonlocked': True,
                'iscredentialsnonexpired': True,
                'isenabled': False,
                'date':datetime.datetime.now().timestamp()}
    )
    es.indices.refresh(index='account')
    formatted_questionnaire=user_data.questionnaire.copy()
    # formatted_questionnaire=format_data(formatted_questionnaire)
    #maps to variable names used in rules and mycbr
    for (key,new_key) in LS_MAPPING.items():
        # value=formatted_questionnaire.pop(key,None)
        if key not in formatted_questionnaire.keys():
            continue
        formatted_questionnaire[new_key]=formatted_questionnaire[key]
    res = es.index(index='baseline', id=user_data.username, 
            document={
                'userid': user_data.username,
                'questionnaire':formatted_questionnaire
                }
    )
    res = es.index(index='questionnaire', id=user_data.username, 
            document={
                'userid': user_data.username,
                'questionnaire':formatted_questionnaire
                }
    )
    es.indices.refresh(index='baseline')
    es.indices.refresh(index='questionnaire')

    res = es.search(index="data_description",query={"match":{"description_type":"achievement"}},size=900)["hits"]["hits"]
    achievement_goals= list(map(lambda x: (x['_source']["achievementid"],x['_source']["goal"]),res))
    achievements_start=list(map(lambda x: 
                                {"index":"achievements",
                                    "_id":user_data.username+"_"+x[0],
                                    "_source":{"userid":user_data.username,
                                    "achievementid":x[0],
                                    "progress":0,
                                    "goal":x[1],
                                    "achievedat":-1
                                    }
                                }
                                    ,achievement_goals))
    helpers.bulk(es,achievements_start,index="achievements")
    # except:
    #     raise HTTPException(status_code=500)

    return "User was added"

@router.post("/followup")
async def followup(
    current_user: Annotated[User, Depends(get_current_active_user)],
    user_data:PartialUser
): 
    
    if not current_user.admin:
        raise HTTPException(403,"You need admin access to add followup")
    # try:
            
    formatted_questionnaire=user_data.questionnaire.copy()
    #maps to variable names used in rules and mycbr
    for (key,new_key) in LS_MAPPING.items():
        value=formatted_questionnaire.pop(key,None)
        formatted_questionnaire[new_key]=value
    try:
        prev_questionnaire=es.get(index='questionnaire', id=user_data.username)["_source"]["questionnaire"]
    except:
        raise HTTPException(404,"User not found ")
    formatted_questionnaire=prev_questionnaire | formatted_questionnaire
    es.update(index='questionnaire', id=user_data.username, 
            doc={
                'questionnaire':formatted_questionnaire
                }
    )
    es.indices.refresh(index='questionnaire')

    # except:
    #     raise HTTPException(status_code=500)

    return "Followup added"


# @router.post("/test")
# async def mini(
#     # current_user: Annotated[User, Depends(get_current_active_user)],
#     user_data:dict
# ): 
#     print(user_data)
