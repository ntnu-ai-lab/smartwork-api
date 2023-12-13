from fastapi import APIRouter,Depends
from elasticsearch import Elasticsearch
from api.services.oauth import get_current_active_user,User
from typing import Annotated
from api.resources.constants import PORT,PASSWORD,USERNAME,HOST
from api.resources.custom_router import LoggingRoute

router = APIRouter(prefix="/data",route_class=LoggingRoute,tags=["Data"])




es = Elasticsearch(HOST+str(PORT),basic_auth=(USERNAME,PASSWORD),verify_certs=False)



@router.get("/education/list")
async def root(
    current_user: Annotated[User, Depends(get_current_active_user)],

):
    res = es.search(index="data_description",query={"match":{"description_type":"education"}},size=900)["hits"]["hits"]
    return list(map(lambda x: x["_source"],res))

@router.get("/exercise/list")
async def root(
    current_user: Annotated[User, Depends(get_current_active_user)],

):
    res = es.search(index="data_description",query={"match":{"description_type":"exercise"}},size=900)["hits"]["hits"]
    return list(map(lambda x: x["_source"],res))


@router.get("/achievement/list")
async def root(
    current_user: Annotated[User, Depends(get_current_active_user)],

):
    res = es.search(index="data_description",query={"match":{"description_type":"achievement"}},size=900)["hits"]["hits"]
    return list(map(lambda x: x["_source"],res))

@router.get("/achievement/types")
async def root(
    current_user: Annotated[User, Depends(get_current_active_user)],

):
    res = es.search(index="data_description",query={"match":{"description_type":"achievement"}},size=900)["hits"]["hits"]
    types=set(map(lambda x: x["_source"]["type"],res))
    return list(map(lambda x: {"type":x},types))