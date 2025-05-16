from fastapi import APIRouter,Depends
from api.services.oauth import get_current_active_user,User
from typing import Annotated
from elasticsearch import Elasticsearch
from api.resources.constants import ES_PASSWORD,ES_URL,ACHIEVEMENT_ORDER
from pydantic import BaseModel
from api.resources.custom_router import LoggingRoute
from elasticsearch import helpers
from datetime import datetime
import pandas as pd
from api.achievements.check_achievements import update_goal,total_steps,daily_steps,avg_weekly_steps

es = Elasticsearch(ES_URL,basic_auth=("elastic",ES_PASSWORD),verify_certs=False)


router = APIRouter(prefix="/patient",route_class=LoggingRoute,tags=["Patient"])


@router.get("/language")
async def language(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Returns the language of the user
    """
    return {"message": current_user.language}


@router.get("/demography")
async def language(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Returns the age, gender, height and weight of the user
    """
    demographics={}
    res=es.search(index="questionnaire", query={'match' : {"userid":current_user.userid}})["hits"]["hits"][0]["_source"]["questionnaire"]
    demographics["age"]=res["Dem_age"]
    demographics["gender"]=res["Dem_gender"]
    demographics["height"]=res["Dem_height"]
    demographics["weight"]=res["Dem_weight"]
    return demographics


class Achievement(BaseModel):
    achievementid:str
    progress:int
    goal:int
    acheievedat:int

class Achievements(BaseModel):
    achievements:list[Achievement]

@router.get("/achievements") 
async def achievements(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Returns achievement info for the user that is signed in
    """
    res = es.search(index="achievements", query={'match' : {"userid":current_user.userid}},size=10000)["hits"]["hits"]
    srt = {b: i for i, b in enumerate(ACHIEVEMENT_ORDER)}
    res=sorted(res, key=lambda x: srt[x["_source"]["achievementid"]])
    return list(map(lambda x: x["_source"],res))




def steps2distance(step_count,gender,height):
    #https://www.walkingwithattitude.com/articles/features/how-to-measure-stride-or-step-length-for-your-pedometer
    if gender=="female":
        return 0.413*float(height)*step_count*0.00001
    return 0.415*float(height)*step_count*0.00001


@router.get("/totals")
async def totals(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Returns the total distance walked, number of exercises completed, number of educational items read and number of educational quiz answers
    """
    res = es.search(index="activity", query={'match' : {"userid":current_user.userid}},size=10000)["hits"]["hits"]
    
    res_baseline = es.search(index="questionnaire", query={'match' : {"userid":current_user.userid}},size=10000)["hits"]["hits"]
    if len(res_baseline)==0:
        return None
    res_baseline=res_baseline[0]["_source"]["questionnaire"]
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
    res = es.search(index="exercise", query={'match' : {"userid":current_user.userid}},size=10000)["hits"]["hits"]
    num_exercises=0
    if res!=[]:
        num_exercises=len(res)
    #education
    res = es.search(index="education", query={'match' : {"userid":current_user.userid}},size=10000)["hits"]["hits"]
    num_education=0
    num_quiz=0
    if res!=[]:
        num_education=len(res)
        num_quiz=len(list(filter(lambda x: "is_correct" in x["_source"].keys(),res)))

    return [{'totalid': 'TotalDistanceKm', 'progress': round(distance,2)},
            {'totalid': 'EducationalRead', 'progress': num_education },
            {'totalid': 'EducationalQuizAnswers', 'progress': num_quiz},
            {'totalid': 'ExercisesCompleted', 'progress': num_exercises}]

def activity_done(from_point,to_point,userid):
    activities=es.search(index="activity", query={
        "bool": {
            "must": [
                {
                    "match": {
                        "userid": userid
                    }
                },
                {
                    "range": {
                        "date": {
                            "gte": from_point,  
                            "lte": to_point
                        }
                    }
                }
            ]
        }
    }
    )["hits"]["hits"]
    steps_performed=sum(list(map(lambda x: x["_source"]["steps"],activities)))
    return steps_performed

@router.get("/daily_progress/{from_point}/{to_point}")
async def daily_progress(
    current_user: Annotated[User, Depends(get_current_active_user)],
    from_point:str,
    to_point:str
):
    """
    Returns the progress of the user from a given date to another date. It returns total progress, progress in activity, progress in education and progress in exercise
    """
    from_point_date=datetime.strptime(from_point,"%Y-%m-%d").timestamp()
    to_point_date=datetime.strptime(to_point,"%Y-%m-%d").timestamp()
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
    activity_goal=es.search(index="plan", query={
        "bool": {
            "must": [
                {
                    "match": {
                        "userid": current_user.userid
                    }
                },
                {
                    "range": {
                        "created": {
                           "gte": from_point_date,  
                            "lte": to_point_date
                        }
                    }
                }
            ]
        }
    }
    )["hits"]["hits"]
    if len(activity_goal)==0:
        return {
            "progress": 0,
            "progress_activity":0,
            "progress_education":0,
            "progress_exercise":0,
        }
    else:
        activity_goal=activity_goal[0]["_source"]["plan"]["activity"]["goal"]
    
    completed_exercises=res_exercise["hits"]["hits"]
    completed_educations=res_education["hits"]["hits"]
    plan=es.search(index="plan", query={'match' : {"userid":current_user.userid}},size=1)["hits"]["hits"][0]["_source"]["plan"]
    exercises_in_plan=plan["exercises"]
    education_in_plan=plan["educations"]
    steps_performed=activity_done(from_point_date,to_point_date,current_user.userid)
    progress_exercise=round(len(completed_exercises)/len(exercises_in_plan),2)
    progress_education=round(len(completed_educations)/len(education_in_plan),2)
    progress_activity=steps_performed/activity_goal
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


class ActivityContainer(BaseModel):
    activities:list[Activity]


@router.post("/activity")
async def activity(
    current_user: Annotated[User, Depends(get_current_active_user)],
    activities: ActivityContainer
):
    """
    Adds activity to the user
    """
    activity_dicts=list(map(lambda x: x.model_dump(),activities.activities))
    for activity in activity_dicts:
        activity["date"]=datetime.now().timestamp()
        activity["userid"]=current_user.userid
        # activity["_id"]=current_user.userid+"_"+datetime.fromtimestamp(activity["start"]/1000).timestamp()
    helpers.bulk(es,activity_dicts,index="activity")
    
    total_steps(current_user.userid)
    daily_steps(current_user.userid)
    avg_weekly_steps(current_user.userid)
    # avg_steps_per_week(current_user.userid)
    # steps_in_a_day(current_user.userid)
    return {"status":"success"}

@router.get("/toolbox/educations")
async def educations(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Returns all educational items seen by the user
    """
    res = es.search(index="education", query={'match' : {"userid":current_user.userid}},size=10000)["hits"]["hits"]
    if res==[]:
        return []
    return list(map(lambda x: x["_source"]["educationid"],res))

@router.get("/toolbox/exercises")
async def exercises(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Returns all exercises performed by the user"""
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
    """
    Still just appsettings
    """
    settings["hideIntroSession"]=True  
    es.index(index='appsettings', id=current_user.userid, 
        document=settings
    )
    es.index(index='appsettings', id=current_user.userid, 
            document=settings
        )
    if settings["sleepReminders"]["enabled"]:
        update_goal(current_user.userid,"SetSleepTool")
    if not pd.isna(settings["goalSetting"]["specific"]):
        update_goal(current_user.userid,"SetGoalSetting")
    return {"Status":"True"}


@router.get("/appsettings")
async def appsettings(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Just appsettings
    """
    try:
        settings = es.get(index="appsettings", id=current_user.userid)
    except:
        return []
    settings=settings["_source"]
    return settings

