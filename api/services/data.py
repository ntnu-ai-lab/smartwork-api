from fastapi import APIRouter,Depends
from elasticsearch import Elasticsearch
from services.oauth import get_current_active_user,User
from typing import Annotated
from services.constants import PORT,PASSWORD,USERNAME


es = Elasticsearch("https://localhost:"+str(PORT),basic_auth=(USERNAME,PASSWORD),verify_certs=False)

router = APIRouter(prefix="/data")


@router.get("/education/list")
async def root(
    current_user: Annotated[User, Depends(get_current_active_user)],

):
    res = es.search(index="data_description",query={"match":{"description_type":"education"}},size=900)
    return res["hits"]["hits"]

@router.get("/exercise/list")
async def root(
    current_user: Annotated[User, Depends(get_current_active_user)],

):
    res = es.search(index="data_description",query={"match":{"description_type":"exercise"}},size=900)
    return res["hits"]["hits"]


@router.get("/achievement/list")
async def root(
    current_user: Annotated[User, Depends(get_current_active_user)],

):
    res = es.search(index="data_description",query={"match":{"description_type":"achievement"}},size=900)
    return res["hits"]["hits"]

@router.get("/achievement/types")
async def root(
    current_user: Annotated[User, Depends(get_current_active_user)],

):
    res = es.search(index="data_description",query={"match":{"description_type":"achievement"}},size=900)
    
    return set(map(lambda x: x["_source"]["type"] ,res["hits"]["hits"]))