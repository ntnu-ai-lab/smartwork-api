from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from elasticsearch import Elasticsearch
from services.constants import PORT,PASSWORD,USERNAME
from services.oauth import User,get_current_user
from typing import Annotated
from typing import Optional

es = Elasticsearch("https://localhost:"+str(PORT),basic_auth=(USERNAME,PASSWORD),verify_certs=False)


router = APIRouter(prefix="/patient/plan")


class Plan_info(BaseModel):
    exercise_questions:Optional[dict]



@router.post("/next")
async def next(
    current_user: Annotated[User, Depends(get_current_user)],
    exercises_duration: Plan_info
):

    if not es.indices.exists(index="plan"):
        es.indices.create(index = 'plan')
    #check if user has questionnaire
    questionnaire=res = es.search(index="baseline", body={"query":{'match' : {"userid":current_user.userid}}},size=1)["hits"]["hits"]
    #check if user has a previous plan
    previous_plan=res = es.search(index="plan", body={"query":{'match' : {"userid":current_user.userid}}},size=100)["hits"]["hits"] #TODO: change to most recent rather than top 100
    if questionnaire==[]:
        raise HTTPException(status_code=400,detail="Missing questionannaire")
    print(previous_plan)

    #create exercise plan
    #create education plan
    #create step goal
    # if previous_plan==[]:


    #if has no previous plan
    #elif no cases in database
    #else
    return {"message": "Nothing to see here"}