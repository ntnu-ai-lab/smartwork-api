from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from elasticsearch import Elasticsearch
from services.constants import PORT,PASSWORD,USERNAME,STEP_GOAL_MIN,STEP_GOAL_MAX,HOST
from services.oauth import User,get_current_user

from typing import Annotated
from typing import Optional
import zen
import datetime
import requests
import math
es = Elasticsearch(HOST+str(PORT),basic_auth=(USERNAME,PASSWORD),verify_certs=False)


router = APIRouter(prefix="/patient/plan")


generic_education_items=["Cause of LBP_1", "Cause of LBP_2", "Cause of LBP_3", "Cause of LBP_4", "Cause of LBP_5", "Cause of LBP_6",
			"Guideline LBP_1", "Guideline LBP_2", "Guideline LBP_3",
			"Imaging_1", "Imaging_2",
			"Pain rating_1",
			"Reassurance_2", "Reassurance_4", "Reassurance_6", "Reassurance_8", "Reassurance_9", "Reassurance_10",
			"Stay active_1", "Stay active_2", "Stay active_3", "Stay active_4", "Stay active_5", "Stay active_6", "Stay active_7", "Stay active_8", "Stay active_9", "Stay active_10", "Stay active_11", "Stay active_12", "Stay active_13", "Stay active_14",
			"Start exercise_1", "Start exercise_2", "Start exercise_5", "Start exercise_8", "Start exercise_9", "Start exercise_10",
			"Structure of back_1", "Structure of back_2", "Structure of back_3", "Structure of back_4",
			"Mind-body connection_1", "Mind-body connection_2", "Mind-body connection_5", "Mind-body connection_8",
			"Encouragement to SM_1", "Encouragement to SM_5",
			"Attitude_1", "Attitude_2", "Attitude_3", "Attitude_4", "Attitude_5", "Attitude_6",
			"Distraction_2",
			"Thoughts_1", "Thoughts_3",
			"Daily activity_1", "Daily activity_2", "Daily activity_3", "Daily activity_4", "Daily activity_5",
			"Me time_1", "Me time_2",
			"Sleep disorders_1",
			"MSK pain_1",
			"Goal setting_1", "Goal setting_2", "Goal setting_3", "Goal setting_4", "Goal setting_5",
			"Action planning_1", "Action planning_2", "Action planning_3",
			"Pacing_1", "Pacing_2", "Pacing_3", "Pacing_4", "Pacing_5", "Pacing_6",
			"Relaxation_1", "Relaxation_2", "Relaxation_3", "Relaxation_4", "Relaxation_5",
			"Sleep_4",
			"Family and friends_3"]
# Example filesystem content, it is up to you how you obtain content
with open("./api/resources/smart_work_education.json", "r") as f:
  content1 = f.read()

with open("./api/resources/smart_work_grouping.json", "r") as f:
  content2 = f.read()

with open("./api/resources/smart_work_exercise.json", "r") as f:
  content3 = f.read()
engine = zen.ZenEngine()

decision_education = engine.create_decision(content1)

decision_grouping = engine.create_decision(content2)

decision_exercise = engine.create_decision(content3)


class Plan_info(BaseModel):
    questionnaire:Optional[dict]
    exercise_duration:int


def add_items_priority_queue(priority_queue,additional_items):
    """Adds items not in prioirty queue from additional items list, used for items fetched from cbr and rulebase

    Args:
        priority_queue ([dict]):
        additional_items (list): 

    Returns:
        _type_: updated priority queue
    """
    for cbr_item in additional_items:
        added=False
        for item in priority_queue:
            # print(cbr_item,item["id"])
            if cbr_item==item["id"]:
                item["priority"]+=1
                added=True
                break
        if not added:
            today=datetime.datetime.now() + datetime.timedelta(days=1)
            priority_queue.append(
                {
                    "id":cbr_item,
                    "priority":1,
                    "expiredate":float(today.timestamp()),
                    "thisweek":False,
                    "avoid":False,
                    "excluded":False,
                    "used":False,
                    "usedNumber":0,
                    "lastUsage":0,
                    "lastQuiz":False
                }
            )
    return priority_queue

def generate_plan_education(current_user,questionnaire):
    if not es.indices.exists(index="education_queue"):
        es.indices.create(index = 'education_queue')

    res=es.search(index="education_queue", body={"query":{'match' : {"userid":current_user.userid}}},size=1)["hits"]["hits"]
    if res==[]:
        priority_queue=[]
    else:
        priority_queue=res[0]["_source"]["educational_items"].copy()
    # cbr_education_items=["Changing negative thoughts_7","Changing negative thoughts_6"]
    response=requests.post("http://localhost:8080/concepts/Case/casebases/sbcases/amalgamationFunctions/SMP_Education/retrievalByMultipleAttributes",
                      json=questionnaire,
                      params={"k":-1}
    )
    cbr_education_items=set("".join(list(map(lambda x: x["SelfManagement_Education"],response.json()))).split(";"))
    rule_education_items=list(map(lambda x: x["item"],decision_education.evaluate(questionnaire)["result"]))
    
    #increase priority of items fetched from cbr system
    priority_queue=add_items_priority_queue(priority_queue,cbr_education_items)
    #increase priority of items fetched from rule system
    priority_queue=add_items_priority_queue(priority_queue,rule_education_items)
    #TODO: missing canbequiz argument
    result=decision_grouping.evaluate({"priority_queue":priority_queue})["result"]
    result.sort(key=lambda x: x["priority"],reverse=True)
    

    #if there are not enough items in plan add generic items
    if len(result)<7:
        groups=set(map(lambda x: x["group"],result))
        generic_items_w_groups=decision_grouping.evaluate({"priority_queue":list(map(lambda x: {"id":x},generic_education_items))})["result"]
        for generic_item in generic_items_w_groups:
            if generic_item["group"] not in groups:
                today=datetime.datetime.now() + datetime.timedelta(days=1)
                result.append({
                    "id":generic_item["id"],
                    "priority":1,
                    "expiredate":float(today.timestamp()),
                    "thisweek":False,
                    "group":generic_item["group"],
                    "avoid":False,
                    "excluded":False,
                    "used":False,
                    "usednumber":0,
                    "lastusage":0,
                    "lastquiz":False
                })
                groups.add(generic_item["group"])
            if len(result)>=7:
                break
    #TODO: store updated priority queue in elasticsearch   
    return result[:7]

def generate_plan_exercise(current_user,questionnaire):
    #fetch exercises from cbr 
    response=requests.post("http://localhost:8080/concepts/Case/casebases/sbcases/amalgamationFunctions/SMP_Education/retrievalByMultipleAttributes",
                      json=questionnaire,
                      params={"k":-1}
    )
    cbr_exercise_items=set("".join(list(map(lambda x: x["SelfManagement_Exercise"],response.json()))).split(";"))



    #fetch exercises from rulebase
    res = es.search(index="data_description", query={'match' : {"description_type":"exercise"}},size=10000)
    temp_quest={
        "bt_pain_average":5,
        "bt_pain_average":3,
        "duration":35,
        "condition":"LBP",
        "exercises":[
            {
            "condition":"LBP"
            }
        ]
        }

    # rule_exercise_items=list(map(lambda x: x["item"],decision_exercise.evaluate(temp_quest)["result"]))
    print(decision_exercise.evaluate(temp_quest))
    return 2

def min_max_activity(goal):
    if goal<6000:
        recommended_min=round(goal*0.9*0.01)*100
        recommended_max=round(goal*1.1*0.01)*100
    elif goal<8000:
        recommended_min=round(goal*0.85*0.01)*100
        recommended_max=round(goal*1.15*0.01)*100
    else:
        recommended_min=round(goal*0.8*0.01)*100
        recommended_max=round(goal*1.2*0.01)*100
    if recommended_min < STEP_GOAL_MIN:
        recommended_min=STEP_GOAL_MIN
    if recommended_max> STEP_GOAL_MAX:
        recommended_max=STEP_GOAL_MAX
    if recommended_max<STEP_GOAL_MIN:
        recommended_max=STEP_GOAL_MAX
    if recommended_min>STEP_GOAL_MAX:
        recommended_min=STEP_GOAL_MIN
    return recommended_min,recommended_max


def generate_activity_goal(current_user):
    #get latest completed plan
    res=es.search(index="plan", body={"query":{'match' : {"userid":current_user.userid}}},size=1)["hits"]["hits"]
    print(res)
    #no previous plan
    if res==[]:
        return {
        "goal":STEP_GOAL_MIN,
        "recommended_min":STEP_GOAL_MIN,
        "recommended_max":STEP_GOAL_MAX
        }
    #fetch done part of that plan
    #where is this even stored?
    prev_steps=res[0]["_source"]["done"]["steps"]
    
    if prev_steps>STEP_GOAL_MAX:
        prev_steps=STEP_GOAL_MAX
    elif prev_steps<STEP_GOAL_MIN:
        prev_steps=STEP_GOAL_MIN
    
    # average between last week goal and steps done
    #TODO: assumes latest plan is latest in history
    previous_goal=res[0]["_source"]["history"][-1]["activity"]["goal"]
    new_goal= (prev_steps +previous_goal)/2
    # round to hundreds
    new_goal=int(math.ceil(new_goal / 100.0)) * 100
    
    #calc nex min max
    recommended_min,recommended_max=min_max_activity(new_goal)
    return {"goal":new_goal,
    "recommended_min":recommended_min,
    "recommended_max":recommended_max
    }

@router.post("/next")
async def next(
    current_user: Annotated[User, Depends(get_current_user)],
    plan_info: Plan_info
):
    if not es.indices.exists(index="plan"):
        es.indices.create(index = 'plan')
    #TODO: check if current plan has expired before creating a new plan, if not error

    #check if user has questionnaire
    questionnaire=res = es.search(index="baseline", body={"query":{'match' : {"userid":current_user.userid}}},size=1)["hits"]["hits"]
    #check if user has a previous plan
    previous_plan=res = es.search(index="plan", body={"query":{'match' : {"userid":current_user.userid}}},size=100)["hits"]["hits"] #TODO: change to most recent rather than top 100
    if previous_plan!=[]:
        history=previous_plan[0]["_source"]["history"]
    else:
        history=[]
    if questionnaire==[]:
        raise HTTPException(status_code=500,detail="Missing baseline questionannaire")
    else:
        #merges baseline questionnaire with new info
        complete_questionnaire=questionnaire[0]["_source"]["questionnaire"] | plan_info.questionnaire
        #TODO: should this only merge with the previous plan and not all previous exercises?

    #create exercise plane
    #create education plan
    #create step goal
    # if previous_plan==[]:
    curr_dt = datetime.datetime.now()
    complete_plan={
                    "userid":current_user.userid,
                    "date":curr_dt.timestamp(),
                    "start":int(datetime.datetime.combine(curr_dt, datetime.time.min).timestamp()),
                    "end":int(datetime.datetime.combine(curr_dt+datetime.timedelta(days=7), datetime.time.max).timestamp()),
                    "exercise_duration":plan_info.exercise_duration,
                    "history":history,
                    "plan":{
                        "date":curr_dt.timestamp(),
                        "educations":generate_plan_education(current_user,complete_questionnaire),
                        "exercises":generate_plan_exercise(current_user,complete_questionnaire),
                        "activity":generate_activity_goal(current_user)
                    },
                    "done":{"steps":0} #TODO: what is this supposed to be? Woulfnt it just be 0?
                   }
    
    #TODO: need to check if plan is valid first
    es.index(index='plan', body=complete_plan)


    #should exercises also be added to the Exercise ES index?
    return complete_plan


class Exercise(BaseModel):
    exerciseid:str
    performed:int
    sets:int
    setduration:int
    reps:int
    repsperformed1:int
    repsperformed2:int
    repsperformed3:int

class Exercises(BaseModel):
    exercises:list[Exercise]

@router.post("/exercise")
async def exercise(
    current_user: Annotated[User, Depends(get_current_user)],
    exercises: Exercises
):
    res=es.search(index="exercise", query={'match' : {"_id":current_user.userid}},size=1)["hits"]["hits"]
    print(exercises)


@router.get("/latest")
async def latest(
    current_user: Annotated[User, Depends(get_current_user)],
):
    res=es.search(index="plan", query={'match' : {"userid":current_user.userid}},size=1)["hits"]["hits"]
    history=res[0]["_source"]["history"]
    if history==[]:
        return []
    return history[-1]


class Goal(BaseModel):
    goal:int

@router.put("/activity_goal")
async def latest(
    current_user: Annotated[User, Depends(get_current_user)],
    goal: Goal
):
    res=es.search(index="plan", query={'match' : {"userid":current_user.userid}},size=1)["hits"]["hits"]
    plan=res[0]["_source"]
    plan["plan"]["activity"]["goal"]=goal.goal
    es.update(index='plan',id=res[0]["_id"],body={"doc":plan})

class Day(BaseModel):
    day:str

@router.get("/on")
async def latest(
    current_user: Annotated[User, Depends(get_current_user)],
    day: Day
):
    query_date=datetime.datetime.strptime(day.day, "%d-%m-%Y")
    query_date=query_date.timestamp()
    res=es.search(index="plan", query={'match' : {"userid":current_user.userid}},size=1)["hits"]["hits"]
    plans=res[0]["_source"]["history"]
    current_plan=res[0]["_source"]
    current_plan.pop("history")
    plans.append(current_plan) #add current plan list with history
    for plan in plans:
        if query_date>=plan["start"] and query_date<=plan["end"]:
            return plan
    return {}


class Education_item(BaseModel):
    educationid:str
    is_quiz:bool
    is_correct:bool

@router.post("/education/completed")
async def latest(
    current_user: Annotated[User, Depends(get_current_user)],
    education_item:Education_item
):
    if not es.indices.exists(index="education"):
        es.indices.create(index = 'education')
    education=dict(education_item)
    education["userid"]=current_user.userid
    es.index(index="education",document=education)

class Exercise_item(BaseModel):
     exerciseid:str
     performed:int
     sets:int
     setduration:int
     reps:int
     repsperformed1:int
     repsperformed2:int
     repsperformed3:int
     status:str
     


@router.post("/exercise/completed")
async def latest(
    current_user: Annotated[User, Depends(get_current_user)],
    exercise_item:Exercise_item
):
    if not es.indices.exists(index="exercise"):
        es.indices.create(index = 'exercise')
    exercise=dict(exercise_item)
    exercise["userid"]=current_user.userid
    es.index(index="exercise",document=exercise)