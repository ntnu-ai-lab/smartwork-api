from fastapi import APIRouter,Depends
from api.services.oauth import get_current_active_user,User
from typing import Annotated
from elasticsearch import Elasticsearch
from api.resources.constants import PORT,PASSWORD,USERNAME,HOST,ACHIEVEMENT_ORDER
from pydantic import BaseModel
from api.resources.custom_router import LoggingRoute
from elasticsearch import helpers
from datetime import datetime
import pandas as pd
from api.achievements.check_achievements import avg_steps_per_week, complete_onetime_goal, total_steps,steps_in_a_day

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
async def achievements(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    if not es.indices.exists(index="achievements"):
        es.indices.create(index = 'achievements')
    res = es.search(index="achievements", query={'match' : {"userid":current_user.userid}},size=10000)["hits"]["hits"]
    srt = {b: i for i, b in enumerate(ACHIEVEMENT_ORDER)}
    res=sorted(res, key=lambda x: srt[x["_source"]["achievementid"]])
    if res==[]:
        res = es.search(index="data_description",query={"match":{"description_type":"achievement"}},size=900)["hits"]["hits"]
        achievement_goals= list(map(lambda x: (x['_source']["achievementid"],x['_source']["goal"]),res))
        achievements_start=list(map(lambda x: 
                                    {"index":"achievements",
                                     "_id":current_user.userid+"_"+x[0],
                                     "_source":{"userid":current_user.userid,
                                        "achievementid":x[0],
                                        "progress":0,
                                        "goal":x[1],
                                        "achievedat":-1}
                                    }
                                     ,achievement_goals))
        helpers.bulk(es,achievements_start,index="achievements")
    return list(map(lambda x: x["_source"],res))




def steps2distance(step_count,gender,height):
    #https://www.walkingwithattitude.com/articles/features/how-to-measure-stride-or-step-length-for-your-pedometer
    if gender=="female":
        return 0.413*int(height)*step_count*0.00001
    return 0.415*int(height)*step_count*0.00001


@router.get("/totals")
async def totals(
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



@router.get("/daily_progress/{from_point}/{to_point}")
async def daily_progress(
    current_user: Annotated[User, Depends(get_current_active_user)],
    from_point:str,
    to_point:str
):
    #progress total
    from_point_date=datetime.strptime(from_point,"%Y-%m-%d").timestamp()
    to_point_date=datetime.strptime(to_point,"%Y-%m-%d").timestamp()
    # res_exercise=es.search(index="exercise",query={'match' : {"userid":current_user.userid}},size=10000)["hits"]["hits"]
    print(from_point_date,to_point_date)
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
                            "gte": from_point_date,  
                            "lte": to_point_date
                        }
                    }
                }
            ]
        }
    }
    )
    res_education=es.search(index="education", query={
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
                            "gte": from_point_date,  
                            "lte": to_point_date
                        }
                    }
                }
            ]
        }
    }
    )
    completed_exercises=res_exercise["hits"]["hits"]
    completed_educations=res_education["hits"]["hits"]
    plan=es.search(index="plan", query={'match' : {"userid":current_user.userid}},size=1)["hits"]["hits"][0]["_source"]["plan"]
    exercises_in_plan=plan["exercises"]
    education_in_plan=plan["educations"]
    
    progress_exercise=round(len(completed_exercises)/len(exercises_in_plan),2)
    progress_education=round(len(completed_educations)/len(education_in_plan),2)
    progress_activity=10000
    total_progress=round(1/3*progress_exercise+1/3*progress_education+1/3*progress_activity,2)
    return {
        "progress": total_progress*100,
        "progress_activity":progress_activity*100,
        "progress_education":progress_education*100,
        "progress_exercise":progress_exercise*100,
    }

class Activity(BaseModel):
    start:int
    end:int
    type:str
    steps:int

class Activities(BaseModel):
    activities:list[Activity]


@router.post("/activity")
async def activity(
    current_user: Annotated[User, Depends(get_current_active_user)],
    activities: Activities
):
    if not es.indices.exists(index="activity"):
        es.indices.create(index = 'activity')
    activity_dicts=list(map(lambda x: dict(x),activities.activities))
    for activity in activity_dicts:
        activity["userid"]=current_user.userid
        activity["_id"]=current_user.userid+"_"+datetime.fromtimestamp(activity["start"]/1000).isoformat()
    helpers.bulk(es,activity_dicts,index="activity")
    # total_steps(current_user.userid)
    # avg_steps_per_week(current_user.userid)
    # steps_in_a_day(current_user.userid)
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
async def exercises(
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
    settings["hideIntroSession"]=True 
    if not es.indices.exists(index="appsettings"):
        es.indices.create(index = 'appsettings')
        es.index(index='appsettings', id=current_user.userid, 
            document=settings
        )
    es.index(index='appsettings', id=current_user.userid, 
            document=settings
        )
    if settings["sleepReminders"]["enabled"]:
        complete_onetime_goal(current_user.userid,"SetSleepTool")
    if not pd.isna(settings["goalSetting"]["specific"]):
        complete_onetime_goal(current_user.userid,"SetGoalSetting")
    return {"Status":"True"}


@router.get("/appsettings")
async def appsettings(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    if not es.indices.exists(index="appsettings"):
        es.indices.create(index = 'appsettings')
    try:
        settings = es.get(index="appsettings", id=current_user.userid)
    except:
        return []
    settings=settings["_source"]
    return settings

