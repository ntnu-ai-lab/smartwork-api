from fastapi import APIRouter,Depends
from services.oauth import get_current_active_user,User
from typing import Annotated
from elasticsearch import Elasticsearch
from services.constants import PORT,PASSWORD,USERNAME



es = Elasticsearch("https://localhost:"+str(PORT),basic_auth=(USERNAME,PASSWORD),verify_certs=False)

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
