from fastapi import APIRouter,Depends
from services.oauth import get_current_active_user,User
from typing import Annotated
from elasticsearch import Elasticsearch
from services.constants import PORT,PASSWORD,USERNAME,HOST
from pydantic import BaseModel


es = Elasticsearch(HOST+str(PORT),basic_auth=(USERNAME,PASSWORD),verify_certs=False)

router = APIRouter(prefix="/patient")


@router.get("/language")
async def language(
    current_user: Annotated[User, Depends(get_current_active_user)],
):

    return {"message": current_user.country}


@router.get("/demography")
async def language(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    print(es.search(index="baseline", query={'match' : {"userid":current_user.userid}}))
    demographics={}
    res=es.search(index="baseline", query={'match' : {"userid":current_user.userid}})["hits"]["hits"][0]["_source"]["questionnaire"]
    demographics["age"]=res["Dem_age"]
    demographics["gender"]=res["Dem_gender"]
    demographics["height"]=res["Dem_height"]
    demographics["weight"]=res["Dem_weight"]
    return demographics


class Activity(BaseModel):
    start:int
    end: int
    type:str
    steps:int

class Activities(BaseModel):
    activities:list[Activity]


@router.post("/activity")
async def activity(
    current_user: Annotated[User, Depends(get_current_active_user)],
    activities:Activities
):
    if not es.indices.exists(index="activity"):
        es.indices.create(index = 'activity')

    res=es.search(index="activity", query={'match' : {"_id":current_user.userid}},size=1)["hits"]["hits"]
    if res==[]:
        prev_acitvities={"activities":[]}
    else:
        prev_acitvities=res[0]["_source"]
    new_activities=list(map(lambda x: dict(x),activities.activities))
    prev_acitvities["activities"].extend(new_activities)
    es.index(index='activity', id=current_user.userid, 
            document=prev_acitvities
    )
    return {"activites":prev_acitvities}


class Achievement(BaseModel):
    achievementid:str
    progress:int
    goal:int
    acheievedat:int

class Achievements(BaseModel):
    achievements:list[Achievement]


@router.post("/activity")
async def activity(
    current_user: Annotated[User, Depends(get_current_active_user)],
    achievements:Achievements
):
    if not es.indices.exists(index="activity"):
        es.indices.create(index = 'activity')

    res=es.search(index="activity", query={'match' : {"_id":current_user.userid}},size=1)["hits"]["hits"]
    if res==[]:
        prev_acitvities={"activities":[]}
    else:
        prev_acitvities=res[0]["_source"]
    new_activities=list(map(lambda x: dict(x),activity.activities))
    prev_acitvities["activities"].extend(new_activities)
    es.index(index='activity', id=current_user.userid, 
            document=prev_acitvities
    )
    return {"activites":prev_acitvities}

@router.get("/toolbox/educations")
async def educations(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    res = es.search(index="education", query={'match' : {"userid":current_user.userid}},size=10000)
    return {"educations":list(map(lambda x: x["_source"]["educationid"],res["hits"]["hits"]))}

@router.get("/toolbox/exercises")
async def educations(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    res = es.search(index="exercise", query={'match' : {"userid":current_user.userid}},size=10000)
    return {"exercises":list(map(lambda x: x["_source"]["exerciseid"],res["hits"]["hits"]))}
    