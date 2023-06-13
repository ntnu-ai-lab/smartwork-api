from fastapi import APIRouter,Depends
from elasticsearch import Elasticsearch
from services.oauth import get_current_active_user,User
from typing import Annotated
es = Elasticsearch("https://localhost:9400",basic_auth=("elastic","UhJ=sDusoDu=8a*JJ-H6"),verify_certs=False)
es.indices.get_alias(index="*")

router = APIRouter(prefix="/data")


@router.get("/education/list")
async def root(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    print(current_user.country)
    res = es.search(index="data_description", body={"query":{'match' : {"_type":"education_"+"en"}}},size=900)
    if not res["hits"]:
        return []

    return res