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
    # res = es.index(index='account', id="stuartgo", 
    #         document={
    #             'userid': 'stuartgo',
    #             'password': '$2b$12$phrVybcm8uyeTl9D/cdYoeZxiOHsjddjitMoYWv8lMVu9bMuY1L2a',
    #             'country': 'nl',
    #             'clinician': 'NTNU',
    #             'rights': 'ROLE_USER',
    #             'isaccountnonexpired': True,
    #             'isaccountnonlocked': True,
    #             'iscredentialsnonexpired': True,
    #             'isenabled': True}
    # )

    res = es.search(index="data_description",query={"exists": {"field": "educationid"}},size=900)
    return res["hits"]["hits"]