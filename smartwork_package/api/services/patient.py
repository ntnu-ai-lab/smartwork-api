from fastapi import APIRouter,Depends
from api.services.oauth import get_current_active_user,User
from typing import Annotated
from elasticsearch import Elasticsearch
from api.resources.constants import PORT,PASSWORD,USERNAME,HOST
from pydantic import BaseModel
from api.resources.custom_router import LoggingRoute
from elasticsearch import helpers
es = Elasticsearch(HOST+str(PORT),basic_auth=(USERNAME,PASSWORD),verify_certs=False)


router = APIRouter(prefix="/patient",route_class=LoggingRoute,tags=["Patient"])


@router.get("/language")
async def language(
    current_user: Annotated[User, Depends(get_current_active_user)],
):

    return {"message": current_user.country}


@router.get("/demography")
async def language(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    # print(es.search(index="baseline", query={'match' : {"userid":current_user.userid}}))
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


# @router.post("/activity")
# async def activity(
#     current_user: Annotated[User, Depends(get_current_active_user)],
#     activities:Activities
# ):
#     if not es.indices.exists(index="activity"):
#         es.indices.create(index = 'activity')

#     res=es.search(index="activity", query={'match' : {"_id":current_user.userid}},size=1)["hits"]["hits"]
#     if res==[]:
#         prev_acitvities={"activities":[]}
#     else:
#         prev_acitvities=res[0]["_source"]
#     new_activities=list(map(lambda x: dict(x),activities.activities))
#     prev_acitvities["activities"].extend(new_activities)
#     es.index(index='activity', id=current_user.userid, 
#             document=prev_acitvities
#     )
#     return {"activites":prev_acitvities}


class Achievement(BaseModel):
    achievementid:str
    progress:int
    goal:int
    acheievedat:int

class Achievements(BaseModel):
    achievements:list[Achievement]

@router.get("/achievements") # removed stats category achievements,might need to be added back in
async def educations(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    if not es.indices.exists(index="achievements"):
        es.indices.create(index = 'achievements')
    res = es.search(index="achievements", query={'match' : {"userid":current_user.userid}},size=10000)["hits"]["hits"]
    if res!=[]:
        return res[0]["_source"]["achievements"]
    res = es.search(index="data_description",query={"match":{"description_type":"achievement"}},size=900)["hits"]["hits"]
    achievement_goals= list(map(lambda x: (x['_source']["achievementid"],x['_source']["goal"]),res))
    achievements_start=list(map(lambda x: {"achievementid":x[0],"progress":0,"goal":x[1],"achievedat":-1},achievement_goals))
    achievement_dict={"userid":current_user.userid,"achievements":achievements_start}
    es.index(index="achievements",document=achievement_dict)
    return achievements_start


def steps2distance(step_count,gender,height):
    #https://www.walkingwithattitude.com/articles/features/how-to-measure-stride-or-step-length-for-your-pedometer
    if gender=="female":
        return 0.413*int(height)*step_count*0.00001
    return 0.415*int(height)*step_count*0.00001


@router.get("/totals")
async def educations(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    if not es.indices.exists(index="activity"):
        es.indices.create(index = 'activity')
    #steps
    res = es.search(index="activity", query={'match' : {"userid":current_user.userid}},size=10000)["hits"]["hits"]
    res_baseline = es.search(index="baseline", query={'match' : {"userid":current_user.userid}},size=10000)["hits"]["hits"][0]["_source"]["questionnaire"]
    try:
        gender=res_baseline["Dem_gender"]
    except:
        raise Exception("Gender missing from questionnaire")
    try:
        height=res_baseline["Dem_height"]
    except:
        raise Exception("Height missing from questionnaire")
    steps=0
    if res!=[]:
        res=list(map(lambda x: x["_source"],res))
        steps=sum(list(map(lambda x: x["steps"],res)))
    distance=steps2distance(steps,gender,height)
    #exercises
    if not es.indices.exists(index="exercise"):
        es.indices.create(index = 'exercise')
    res = es.search(index="exercise", query={'match' : {"userid":current_user.userid}},size=10000)["hits"]["hits"]
    num_exercises=0
    if res!=[]:
        num_exercises=len(res)
    #education
    if not es.indices.exists(index="education"):
        es.indices.create(index = 'education')
    res = es.search(index="education", query={'match' : {"userid":current_user.userid}},size=10000)["hits"]["hits"]
    num_education=0
    if res!=[]:
        num_education=len(res)

    return [{'totalid': 'TotalDistanceKm', 'progress': round(distance,2)},
            {'totalid': 'EducationalRead', 'progress': num_education },
            {'totalid': 'EducationalQuizAnswers', 'progress': 9999999},
            {'totalid': 'ExercisesCompleted', 'progress': num_exercises}]

class Activity(BaseModel):
    start:int
    end:int
    type:str
    steps:int


@router.get("/daily_progress/{from_point}/{to_point}")
async def daily_progress(
    current_user: Annotated[User, Depends(get_current_active_user)],
    from_point:str,
    to_point:str
):
    #should I update achievements here?
    #progress total
    #
    # res_exercise=es.search(index="exercise",query={'match' : {"userid":current_user.userid}},size=10000)["hits"]["hits"]

    res_exercise=es.search(index="exercise", query={
        "bool": {
            "must": [
                {
                    "match": {
                        "userid": current_user.userid
                    }
                },
                {
                    "range": {
                        "date": {
                            "gte": from_point,  # Greater than or equal to 10
                            "lte": to_point  # Less than or equal to 100
                        }
                    }
                }
            ]
        }
    }
    )

    print(res_exercise)
    raise
    progress_activity=1

    return {
        "progress": 66,
        "progress_activity":50,
        "progress_education":100,
        "progress_exercise":50
    }



@router.post("/activity")
async def activity(
    current_user: Annotated[User, Depends(get_current_active_user)],
    activities: list[Activity]
):
    activity_dicts=list(map(lambda x: dict(x),activities))
    for activity in activity_dicts:
        activity["userid"]=current_user.userid

    helpers.bulk(es,activity_dicts,index="activity")
    return {"status":"success"}

@router.get("/toolbox/educations")
async def educations(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    if not es.indices.exists(index="education"):
        es.indices.create(index = 'education')
    res = es.search(index="education", query={'match' : {"userid":current_user.userid}},size=10000)["hits"]["hits"]
    if res==[]:
        return []
    return list(map(lambda x: x["_source"]["educationid"],res))

@router.get("/toolbox/exercises")
async def educations(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    if not es.indices.exists(index="exercise"):
        es.indices.create(index = 'exercise')
    res = es.search(index="exercise", query={'match' : {"userid":current_user.userid}},size=10000)["hits"]["hits"]
    if res==[]:
        []
    return list(map(lambda x: x["_source"]["exerciseid"],res))

class Settings(BaseModel):
    settings:dict


@router.post("/appsettings")
async def appsettings(
    current_user: Annotated[User, Depends(get_current_active_user)],
    settings :dict
):
    if not es.indices.exists(index="appsettings"):
        es.indices.create(index = 'appsettings')
    es.index(index='appsettings', id=current_user.userid, 
            document=settings
    )
    return {"Status":"True"}


@router.get("/appsettings/")
async def appsettings(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    settings=res = es.search(index="appsettings", query={'match' : {"id":current_user.userid}},size=10000)
    return settings["hits"]["hits"]["_source"]

