from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from elasticsearch import Elasticsearch
from services.constants import PORT,PASSWORD,USERNAME
from services.oauth import User,get_current_user
from typing import Annotated
from typing import Optional
from datetime import datetime,timedelta
import zen
import requests
es = Elasticsearch("https://localhost:"+str(PORT),basic_auth=(USERNAME,PASSWORD),verify_certs=False)


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
engine = zen.ZenEngine()

decision_education = engine.create_decision(content1)

decision_grouping = engine.create_decision(content2)


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
                print("yes")
                item["priority"]+=1
                added=True
                break
        if not added:
            today=datetime.now() + timedelta(days=1)
            priority_queue.append(
                {
                    "id":cbr_item,
                    "priority":1,
                    "expiredate":int(today.timestamp()),
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
    #TODO: fetch most similar cases from CBR based on baseline questionnaire
    cbr_education_items=["Changing negative thoughts_7","Changing negative thoughts_6"]
    response=requests.post("http://localhost:8080/concepts/Case/casebases/sbcases/amalgamationFunctions/SMP_Education/retrievalByMultipleAttributes",
                      json=questionnaire,
                      params={"k":-1}
    )
    cbr_education_items=response.json()[0]["SelfManagement_Education"].split(";")
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
                today=datetime.now() + timedelta(days=1)
                result.append({
                    "id":generic_item["id"],
                    "priority":1,
                    "expiredate":int(today.timestamp()),
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


@router.post("/next")
async def next(
    current_user: Annotated[User, Depends(get_current_user)],
    plan_info: Plan_info
):
    #TODO: check if current plan has expired before creating a new plan

    #check if user has questionnaire
    questionnaire=res = es.search(index="baseline", body={"query":{'match' : {"userid":current_user.userid}}},size=1)["hits"]["hits"]
    #check if user has a previous plan
    previous_plan=res = es.search(index="plan", body={"query":{'match' : {"userid":current_user.userid}}},size=100)["hits"]["hits"] #TODO: change to most recent rather than top 100
    if questionnaire==[]:
        raise HTTPException(status_code=500,detail="Missing baseline questionannaire")
    else:
        #merges baseline questionnaire with new info
        complete_questionnaire=questionnaire[0]["_source"]["questionnaire"] | plan_info.questionnaire
        #TODO: should this only merge with the previous plan and not all previous exercises?

    #create exercise plan
    #create education plan
    #create step goal
    # if previous_plan==[]:
    complete_plan={"education":generate_plan_education(current_user,complete_questionnaire)
                   }

    #if has no previous plan
    #elif no cases in database
    #else
    #TODO: check if plan is valid, then store it in ES for the priority queue. Add exercises in plan to exercises used 
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