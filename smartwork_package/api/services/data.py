from fastapi import APIRouter,Depends
from elasticsearch import Elasticsearch
from api.services.oauth import get_current_active_user,User
from typing import Annotated
from api.resources.constants import ES_URL,ES_PASSWORD
from api.resources.custom_router import LoggingRoute

router = APIRouter(prefix="/data",route_class=LoggingRoute,tags=["Data"])




es = Elasticsearch(ES_URL,basic_auth=("elastic",ES_PASSWORD),verify_certs=False)



@router.get("/education/list")
async def EducationalItems(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Returns a list of all educational items
    """
    res = es.search(index="education_description",query={"match":{"description_type":"education"}},size=900)["hits"]["hits"]
    return list(map(lambda x: x["_source"],res))

@router.get("/exercise/list")
async def ExerciseItems(
    current_user: Annotated[User, Depends(get_current_active_user)],

):
    """
    Returns a list of all exercise items
    """
    res = es.search(index="exercise_description",query={"match":{"description_type":"exercise"}},size=900)["hits"]["hits"]
    return list(map(lambda x: x["_source"],res))


@router.get("/achievement/list")
async def AchievementItems(
    current_user: Annotated[User, Depends(get_current_active_user)],

):
    """
    Returns a list of all achievement items
    """
    res = es.search(index="achievement_description",query={"match_all":{}},size=900)["hits"]["hits"]#{"bool":{"must_not":{"term":{"type":"stats"}}}}
    return list(map(lambda x: x["_source"],res))

@router.get("/achievement/types")
async def AchievementTypes(
    current_user: Annotated[User, Depends(get_current_active_user)],

):
    """
    Returns a list of all achievement types
    """
    res = es.search(index="achievement_description",query={"match":{"description_type":"achievement"}},size=900)["hits"]["hits"]
    types=set(map(lambda x: x["_source"]["type"],res))
    types=list(filter(lambda x: x!="stats", types))
    return list(map(lambda x: {"type":x},types))