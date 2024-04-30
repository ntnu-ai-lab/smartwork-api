from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel
from elasticsearch import Elasticsearch
from api.resources.constants import *
from api.services.oauth import User,get_current_user
from elasticsearch import helpers
import json
from typing import Annotated
from typing import Optional
import zen
import datetime
import requests
import functools
import math
from functools import cmp_to_key
import random
from api.resources.custom_router import LoggingRoute
es = Elasticsearch(HOST+str(PORT),basic_auth=(USERNAME,PASSWORD),verify_certs=False)



router = APIRouter(prefix="/patient/plan",route_class=LoggingRoute,tags=["Plan"])




class Plan_info(BaseModel):
    questionnaire:Optional[dict]
    exercises_duration:int


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

def calc_priority(item):
    #TODO: missing logic using exclude
    # print(item)
    if item["thisweek"] and not item["used"]:
        return 4
    elif not item["thisweek"] and not item["used"]:
        return 4
    elif item["thisweek"] and item["used"] and item["canbequiz"]:
        return 3
    elif item["thisweek"] and item["used"] and not item["canbequiz"]:
        return 2
    elif not item["thisweek"] and item["used"] and not item["canbequiz"]:
        return 1



def compare_saliency_priority(a,b):
    if a["priority"]==b["priority"]:
        return 1 if a["saliency"] >b["saliency"] else -1
    else:
         return 1 if a["priority"]>b["priority"] else -1

def grouping(priority_queue):
    #Updates each exercise item so it also contains a group number based on the groups defined in the groups_exertcises dictionary
    items_w_groups=[]
    for exercise in priority_queue:
        updated_item=exercise.copy()
        updated_item["group"]=GROUPS_EXERCISES[updated_item["educationid"]]
        items_w_groups.append(updated_item)
    return items_w_groups

# def group_education_items(priority_queue):
#     items_w_groups=grouping(priority_queue)
#     print(items_w_groups)
#     items_w_groups=sorted(items_w_groups,key=functools.cmp_to_key(lambda x,y : compare_saliency_priority(x,y)),reverse=True)
#     return items_w_groups


def expiry_education_items(item):
    #returns saliency and after how many weeks the exercise expires
    if (item in BT_PAIN_AVERAGE_CHANGE_ADD) or (item in BT_PAIN_AVERAGE_HIGH_ADD):
        return 1
    elif item in BT_PAIN_AVERAGE_MEDIUM_ADD:
        return 1
    elif (item in T_CPG_ADD) or (item in T_CPG_CHANGE_ADD):
        return 2
    elif item in TAMPA_ADD:
        return 4
    elif item in BT_WAI_ADD:
        return 8
    elif item in T_SLEEP_ADD:
        return 4
    elif item in BT_PSEQ_ADD:
        return 8
    elif item in BT_PSS_ADD:
        return 4
    elif item in BT_PHQ_ADD:
        return 1
    elif item in BARRIERS_TIME_ADD:
        return 1
    elif item in BARRIERS_TIRED_ADD:
        return 1
    elif item in BARRIERS_SUPPORT_ADD:
        return 1
    elif item in BARRIERS_FAMILY_ADD:
        return 1
    elif item in BARRIERS_WEATHER_ADD:
        return 1
    elif item in BARRIERS_FACILITIES_ADD:
        return 1
    return None

    

def rule_filter_education(questionnaire):
    questionnaire_updated=questionnaire.copy()
    questionnaire_updated["bt_pain_average_change"]=questionnaire_updated["bt_pain_average"]-questionnaire_updated["bt_pain_average_prev"]
    questionnaire_updated["t_cpg_function_change"]=questionnaire_updated["t_cpg_function"]-questionnaire_updated["t_cpg_function_prev"]
    remove_education=[]
    add_educations=[]
    remove_educations=[]
    if questionnaire_updated["bt_pain_average"]>=7:
        remove_education=BT_PAIN_AVERAGE_HIGH_RM
        add_education=BT_PAIN_AVERAGE_HIGH_ADD
        remove_educations.extend(remove_education)
        add_educations.extend(add_education)
    if questionnaire_updated["bt_pain_average_change"]>=3:
        remove_education=BT_PAIN_AVERAGE_CHANGE_RM
        add_education=BT_PAIN_AVERAGE_CHANGE_ADD
        remove_educations.extend(remove_education)
        add_educations.extend(add_education)
    if questionnaire_updated["bt_pain_average"]>=3 and questionnaire_updated["bt_pain_average"]<=6:
        remove_education=BT_PAIN_AVERAGE_MEDIUM_RM
        add_education=BT_PAIN_AVERAGE_MEDIUM_ADD
        remove_educations.extend(remove_education)
        add_educations.extend(add_education)
    if questionnaire_updated["t_cpg_function"]>=5:
        add_education=T_CPG_ADD
        add_educations.extend(add_education)
    if questionnaire_updated["t_cpg_function_change"]>=2:
        add_education=T_CPG_CHANGE_ADD
        add_educations.extend(add_education)
    if questionnaire_updated["t_tampa_fear"]>=5:
        remove_education=TAMPA_RM
        add_education=TAMPA_ADD
        remove_educations.extend(remove_education)
        add_educations.extend(add_education)
    if questionnaire_updated["bt_wai"]>=3:
        add_education=BT_WAI_ADD
        add_educations.extend(add_education)
    if questionnaire_updated["t_sleep"] in ["Several times a week", "Sometimes"]:
        add_education=T_SLEEP_ADD
        add_educations.extend(add_education)
    if questionnaire_updated["bt_pseq_2item"]<=8:
        add_education=BT_PSEQ_ADD
        add_educations.extend(add_education)
    if questionnaire_updated["bt_pss"]>=6:
        add_education=BT_PSS_ADD
        add_educations.extend(add_education)
    if questionnaire_updated["bt_phq_2item"]>=1:
        add_education=BT_PHQ_ADD
        add_educations.extend(add_education)
    if "lack_of_time" in questionnaire_updated["t_barriers"]:
        add_education=BARRIERS_TIME_ADD
        add_educations.extend(add_education)
    if "too_tired" in questionnaire_updated["t_barriers"]:
        add_education=BARRIERS_TIRED_ADD
        add_educations.extend(add_education)
    if "lack_of_support" in questionnaire_updated["t_barriers"]:
        add_education=BARRIERS_SUPPORT_ADD
        add_educations.extend(add_education)
    if "family_work" in questionnaire_updated["t_barriers"]:
        add_education=BARRIERS_FAMILY_ADD
        add_educations.extend(add_education)
    if "weather" in questionnaire_updated["t_barriers"]:
        add_education=BARRIERS_WEATHER_ADD
        add_educations.extend(add_education)
    if "facilities" in questionnaire_updated["t_barriers"]:
        add_education=BARRIERS_FACILITIES_ADD
        add_educations.extend(add_education)

    # groups={'Cause of LBP_1': 0, 'Cause of LBP_2': 0, 'Cause of LBP_3': 0, 'Cause of LBP_4': 0, 'Cause of LBP_5': 0, 'Cause of LBP_6': 0, 'Guideline LBP_1': 1, 'Guideline LBP_2': 1, 'Guideline LBP_3': 1, 'Imaging_1': 2, 'Imaging_2': 2, 'Pain rating_1': 3, 'Reassurance_1': 4, 'Reassurance_2': 4, 'Reassurance_3': 4, 'Reassurance_4': 4, 'Reassurance_5': 4, 'Reassurance_6': 4, 'Reassurance_7': 4, 'Reassurance_8': 4, 'Reassurance_9': 4, 'Reassurance_10': 4, 'Stay active_1': 5, 'Stay active_2': 5, 'Stay active_3': 5, 'Stay active_4': 5, 'Stay active_5': 5, 'Stay active_6': 5, 'Stay active_7': 5, 'Stay active_8': 5, 'Stay active_9': 5, 'Stay active_10': 5, 'Stay active_11': 5, 'Stay active_12': 5, 'Stay active_13': 5, 'Stay active_14': 5, 'Start exercise_1': 6, 'Start exercise_2': 6, 'Start exercise_3': 6, 'Start exercise_4': 6, 'Start exercise_5': 6, 'Start exercise_6': 6, 'Start exercise_7': 6, 'Start exercise_8': 6, 'Start exercise_9': 6, 'Start exercise_10': 6, 'Structure of back_1': 7, 'Structure of back_2': 7, 'Structure of back_3': 7, 'Structure of back_4': 7, 'Mind-body connection_1': 8, 'Mind-body connection_2': 8, 'Mind-body connection_3': 8, 'Mind-body connection_4': 8, 'Mind-body connection_5': 8, 'Mind-body connection_6': 8, 'Mind-body connection_7': 8, 'Mind-body connection_8': 8, 'Mind-body connection_9': 8, 'Mind-body connection_10': 8, 'Encouragement to SM_1': 9, 'Encouragement to SM_2': 9, 'Encouragement to SM_4': 9, 'Encouragement to SM_5': 9, 'Encouragement to SM_6': 9, 'Encouragement to SM_7': 9, 'Encouragement to SM_8': 9, 'Accepting pain_1': 10, 'Accepting pain_2': 10, 'Accepting pain_3': 10, 'Anxious_1': 11, 'Anxious_2': 11, 'Anxious_3': 11, 'Attitude_1': 12, 'Attitude_2': 12, 'Attitude_3': 12, 'Attitude_4': 12, 'Attitude_5': 12, 'Attitude_6': 12, 'Changing negative thoughts_1': 13, 'Changing negative thoughts_2': 13, 'Changing negative thoughts_3': 13, 'Changing negative thoughts_4': 13, 'Changing negative thoughts_5': 13, 'Changing negative thoughts_6': 13, 'Changing negative thoughts_7': 13, 'Changing negative thoughts_9': 13, 'Changing negative thoughts_10': 13, 'Distraction_1': 14, 'Distraction_2': 14, 'Distraction_3': 14, 'Distraction_4': 14, 'Distraction_5': 14, 'Distraction_6': 14, 'Distress_1': 15, 'Fear-avoidance_1': 16, 'Fear-avoidance_2': 16, 'Fear-avoidance_3': 16, 'Fear-avoidance_4': 16, 'Fear-avoidance_5': 16, 'Fear-avoidance_6': 16, 'Stress_1': 17, 'Stress_2': 17, 'Stress_3': 17, 'Thoughts_1': 18, 'Thoughts_2': 18, 'Thoughts_3': 18, 'Thoughts_4': 18, 'Thoughts_5': 18, 'Thoughts_6': 18, 'Thoughts_7': 18, 'Daily activity_1': 19, 'Daily activity_2': 19, 'Daily activity_3': 19, 'Daily activity_4': 19, 'Daily activity_5': 19, 'Me time_1': 20, 'Me time_2': 20, 'FA Reassurance_2': 21, 'FA Reassurance_3': 21, 'FA Reassurance_4': 21, 'FA Reassurance_5': 21, 'FA Stay active_1': 22, 'FA Stay active_2': 22, 'FA Stay active_3': 22, 'FA Stay active_4': 22, 'FA Stay active_5': 22, 'FA Stay active_6': 22, 'FA Stay active_7': 22, 'Depression_1': 23, 'Anxiety_1': 24, 'Sleep disorders_1': 25, 'MSK pain_1': 26, 'Goal setting_1': 27, 'Goal setting_2': 27, 'Goal setting_3': 27, 'Goal setting_4': 27, 'Goal setting_5': 27, 'Action planning_1': 28, 'Action planning_2': 28, 'Action planning_3': 28, 'Pacing_1': 29, 'Pacing_2': 29, 'Pacing_3': 29, 'Pacing_4': 29, 'Pacing_5': 29, 'Pacing_6': 29, 'Problem solving_1': 30, 'Problem solving_2': 30, 'Problem solving_3': 30, 'Problem solving_4': 30, 'Relaxation_1': 31, 'Relaxation_2': 31, 'Relaxation_3': 31, 'Relaxation_4': 31, 'Relaxation_5': 31, 'Sleep_1': 32, 'Sleep_2': 32, 'Sleep_3': 32, 'Sleep_4': 32, 'Work_1': 33, 'Work_2': 33, 'Work_3': 33, 'Work_4': 33, 'Work_5': 33, 'Family and friends_1': 34, 'Family and friends_2': 34, 'Family and friends_3': 34, 'Family and friends_4': 34, 'Family and friends_5': 34, 'Family and friends_6': 34, 'Barrier time_1': 35, 'Barrier time_2': 35, 'Barrier tiredness_1': 36, 'Barrier tiredness_2': 36, 'Barrier support_1': 37, 'Barrier family work_1': 38, 'Barrier family work_2': 38, 'Barrier weather_1': 39, 'Barrier weather_2': 39, 'Barrier facilities_1': 40, 'Barrier facilities_2': 40, 'Barrier facilities_3': 40}
    items=list(filter(lambda x: x not in remove_educations,add_educations))
    # items=list(map(lambda x: {"name":x["name"],"group":groups[x["name"]],"saliency":x["saliency"]} ,items))
    # items=calc_priority(items,questionnaire)

    # items.sort(key=cmp_to_key(compare_saliency_priority),reverse=True)
    # items=list(map(lambda x: x["name"],items))
    return items #list(dict.fromkeys(items)) #removes duplicates and maintains order


def fetch_cbr_educational_items(base_questionnaire):
    response=requests.post("http://localhost:8080/concepts/Case/casebases/sbcases/amalgamationFunctions/SMP_Education/retrievalByMultipleAttributes",
                      json=base_questionnaire,
                      params={"k":-1}
    )
    cbr_education_items=set("".join(list(map(lambda x: x["SelfManagement_Education"],response.json()))).strip(";").split(";"))
    return cbr_education_items
def generate_plan_education(current_user,base_questionnaire,update_questionnaire):

    # if not es.indices.exists(index="education_queue"):
    #     es.indices.create(index = 'education_queue')

    # res=es.search(index="education_queue", body={"query":{'match' : {"userid":current_user.userid}}},size=1)["hits"]["hits"]
    # if res==[]:
    #     priority_queue=[]
    # else:
    #     priority_queue=res[0]["_source"]["educational_items"].copy()

    if not es.indices.exists(index="education"):
        es.indices.create(index = 'education')

    #fetch all educational items
    educational_items = es.search(index="data_description", query={'match' : {"description_type":"education"}},size=1000)["hits"]["hits"]
    educational_items=list(map(lambda x: x["_source"],educational_items))
    # print(list(filter(lambda x: "question" not in x.keys(),educational_items)))
    # raise
    educational_items_w_question=list(filter(lambda x: x["question"]!="Missing value",educational_items))
    educational_items_w_question=list(map(lambda x: x["educationid"],educational_items_w_question))

    has_quiz_question=list(filter(lambda x: x,educational_items))
    #fetch performed exercises and exercises that were part of previous plan
    performed_items=es.search(index="education", body={"query":{'match' : {"userid":current_user.userid}}},size=1)["hits"]["hits"]
    if performed_items!=[]:
        educational_items_used=list(map(lambda x: x["_source"]["educationid"],performed_items))
        educational_items_thisweek=list(filter(lambda x: x["thisweek"],performed_items))
        educational_items_thisweek=list(map(lambda x: x["educationid"],educational_items_thisweek))
    else:
        educational_items_used=[]
        educational_items_thisweek=[]

    #combine cbr and rule educational item into list with just the names of the items
    cbr_education_items=fetch_cbr_educational_items(base_questionnaire)
    if update_questionnaire:
        rule_education_items=rule_filter_education(update_questionnaire)
    else:
        rule_education_items=[]
    selected_educational_items=list(cbr_education_items)
    selected_educational_items.extend(rule_education_items)

    #figure out if educational item is used before by checking history of user from es, same for thisweek
    selected_educational_items=list(map(lambda x: {"educationid":x,
                                                   "used":x in educational_items_used,
                                                   "canbequiz": x in has_quiz_question and x not in educational_items_used,
                                                   "thisweek": x in educational_items_thisweek,
                                                   "expiry_weeks":expiry_education_items(x)}
                                ,selected_educational_items))
    #calculate prioirity
    for item in selected_educational_items:
        item["priority"]=calc_priority(item)

    selected_educational_items.sort(key=lambda x: x["priority"])


    result=grouping(selected_educational_items) #decision_grouping.evaluate({"priority_queue":priority_queue})["result"]
    result.sort(key=lambda x: x["priority"],reverse=True)

    #if there are not enough items in plan add generic items
    #TODO: not sure if this is implemented correcty
    if len(result)<7:
        groups=set(map(lambda x: x["group"] if "group" in x.keys() else None,result))

        generic_items_w_groups=grouping(list(map(lambda x: {"educationid":x},GENERIC_EDUCATION_ITEMS)))#decision_grouping.evaluate({"priority_queue":list(map(lambda x: {"id":x},generic_education_items))})["result"]
        for generic_item in generic_items_w_groups:
            if generic_item["group"] not in groups:
                today=datetime.datetime.now() + datetime.timedelta(days=1)
                result.append({
                    "id":generic_item["id"],
                    "priority":1,
                    "expiredate":float(today.timestamp()+datetime.timedelta(weeks=1)),
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
    # result=list(map(lambda x: x|{"educationid":x["educationid"]},result))
            
    # for item in result:
    #     item["is_quiz"]=True
    #     item["is_correct"]=False
    #TODO: store updated priority queue in elasticsearch   

    print(result[:7])
    return result[:7]


def check_pain_relief(questionnaire):
    bt_pain_change=questionnaire["bt_pain_average"]-questionnaire["bt_pain_average_prev"]
    if questionnaire["bt_pain_average"]>=7 or \
        (questionnaire["bt_pain_average"]<=2 and bt_pain_change>=4) or \
        (questionnaire["bt_pain_average"]>=3 and questionnaire["bt_pain_average"]<=6 and bt_pain_change>=3):
        return True
    return False

def calc_sets_reps(duration):
    if duration<=15:
        return {"number":3,"sets":duration//5,"repetitions":10}
    return {"number":duration//5,"sets":3,"repetitions":10}

def add_core_back_ab(cbr_exercise_items,es_exercise_items):
    exercises=[]
    for grouping in ["back_","ab_","core_"]:
        cbr_exercise_grouping=list(filter(lambda x: grouping in x,cbr_exercise_items))
        es_exercise_grouping=list(filter(lambda x: grouping in x["exerciseid"],es_exercise_items))
        if cbr_exercise_grouping!=[]:
            exercises.append(random.choice(cbr_exercise_grouping))
        else:
            #if no exercise from group is available in cbr exercises use es
            exercises.append(random.choice(es_exercise_grouping))
    return exercises

def add_other_types(exercise_set,number_exercises,selected_execrises):
    exercises=[]
    types_of_exercises=set(map(lambda x: x["type"] ,exercise_set))
    for ex_type in types_of_exercises:
        #checks if type already added in exercises
        if list(filter(lambda x: ex_type in x, exercises))==[]:
            # print(ex_type)
            # print(exercise_set[0])
            exercises.append(random.choice(list(filter(lambda x: ex_type==x["type"],exercise_set))))
        if len(exercises)==number_exercises:
            return exercises
    return exercises
def add_same_type(selected_exercises,exercise_set,number_exercises):
    exercises=[]
    types_of_exercises_selected=set(map(lambda x: x.split("_")[0]+"_" ,selected_exercises))
    for ex_type in types_of_exercises_selected:
        cbr_ex_type_exercises=list(filter(lambda x: ex_type in x,exercise_set))
        for exercise in cbr_ex_type_exercises:
            if exercise not in selected_exercises:
                exercises.append(exercise)
            if len(exercises)==number_exercises:
                return exercises
    return exercises
            
def get_pain_relief_exercises(cbr_exercise_items,es_exercise_items,number_exercises):
    exercises=[]
    #add exercises from cbr system that are pain relief
    cbr_pain_exercises=list(filter(lambda x: "pain_" in x,cbr_exercise_items))
    exercises.extend(cbr_pain_exercises)
    #if not enough add exercises from elasticsearch
    ex_num=0
    while len(exercises)<number_exercises:
        es_pain_exercises=list(filter(lambda x: "pain_" in x["ExerciseID"],es_exercise_items))
        if es_pain_exercises[ex_num]["ExerciseID"] not in exercises:
            exercises.append(es_exercise_items[ex_num]["ExerciseID"])
        ex_num+=1
    return exercises[:number_exercises]

def generate_plan_exercise(base_questionnaire,update_questionnaire,duration):
    #fetch exercises from cbr 
    response=requests.post("http://localhost:8080/concepts/Case/casebases/sbcases/amalgamationFunctions/SMP_Exercise/retrievalByMultipleAttributes",
                      json=base_questionnaire,
                      params={"k":-1}
    )
    #get exercise names from cbr
    cbr_exercise_items=list(set("".join(list(map(lambda x: x["SelfManagement_Exercise"],response.json()))).split(";")))
    #lookup each of the names in ES to get additional info on the exercises
    cbr_exercise_items=es.search(index="data_description", query={"bool": {"filter": {"terms": {"ExerciseID": cbr_exercise_items}}}},size=10000)["hits"]["hits"]
    cbr_exercise_items=list(map(lambda x: x["_source"],cbr_exercise_items))

    #fetch exercises from rulebase
    es_exercise_items = es.search(index="data_description", query={'match' : {"description_type":"exercise"}},size=10000)["hits"]["hits"]
    es_exercise_items=list(map(lambda x: x["_source"],es_exercise_items))
    number_exercises=calc_sets_reps(duration)["number"]
    exercises=[]
    if update_questionnaire:
        if check_pain_relief(update_questionnaire):
            return get_pain_relief_exercises(cbr_exercise_items,es_exercise_items,number_exercises)
    #######not pain relief
    #add random exercise of back,ab and core from cbr system
    exercises.extend(add_core_back_ab(cbr_exercise_items,es_exercise_items))
    if len(exercises)==number_exercises:
        return exercises
    # print(exercises,"post ab back")
    #add exercises of types that are not already in exercises list
    exercises.extend(add_other_types(cbr_exercise_items,number_exercises-len(exercises),exercises))
    if len(exercises)==number_exercises:
        return exercises
    # print(exercises,"other types cbr")
    #same as above but for exercises from elasticsearch
    exercises.extend(add_other_types(es_exercise_items,number_exercises-len(exercises),exercises))
    if len(exercises)==number_exercises:
        return exercises
    # print(exercises,"other types es")
    #if there are still slots to fill and all types are represented add one more of each type until filled
    exercises.extend(add_same_type(exercises,cbr_exercise_items,number_exercises-len(exercises)))
    if len(exercises)==number_exercises:
        return exercises
    #same as above but for es
    exercises.extend(add_same_type(exercises,es_exercise_items,number_exercises-len(exercises)))
    return exercises

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
    #no previous plan
    if res==[] or res[0]["_source"]["history"]==[]: #TODO: not entirely sure this is correct, can history be empty if a plan exists?
        return {
        "goal":STEP_GOAL_MIN,
        "recommended_min":STEP_GOAL_MIN,
        "recommended_max":STEP_GOAL_MAX
        }
    else:
        res=res[0]["_source"]["history"][-1]["activity"]
    #fetch done part of that plan
    #where is this even stored?
    prev_steps=res[0]["_source"]["done"]["steps"]
    
    if prev_steps>STEP_GOAL_MAX:
        prev_steps=STEP_GOAL_MAX
    elif prev_steps<STEP_GOAL_MIN:
        prev_steps=STEP_GOAL_MIN
    
    # average between last week goal and steps done
    #TODO: assumes latest plan is latest in history
    previous_goal=res["goal"]
    new_goal= (prev_steps +previous_goal)/2
    # round to hundreds
    new_goal=int(math.ceil(new_goal / 100.0)) * 100
    
    #calc nex min max
    recommended_min,recommended_max=min_max_activity(new_goal)
    return {"goal":new_goal,
    "recommended_min":recommended_min,
    "recommended_max":recommended_max
    }



def plan_is_active(current_plan):
    if current_plan==[]:
        return False
    plan=current_plan[0]["_source"]
    if datetime.datetime.fromtimestamp(plan["start"]/1000)<datetime.datetime.now() and datetime.datetime.fromtimestamp(plan["end"]/1000)>datetime.datetime.now():
        return True
    return False
    
    
@router.post("/next")
async def next(
    current_user: Annotated[User, Depends(get_current_user)],
    plan_info: Plan_info
):
    if not es.indices.exists(index="plan"):
        es.indices.create(index = 'plan')
    #TODO: check if current plan has expired before creating a new plan, if not error
    current_plan=es.search(index="plan",body={"query":{'match' : {"userid":current_user.userid}}},size=1)["hits"]["hits"]
    if plan_is_active(current_plan):
        raise HTTPException(status_code=500,detail="User already has a valid plan.")
    #check if user has questionnaire
    base_questionnaire=res = es.search(index="baseline", body={"query":{'match' : {"userid":current_user.userid}}},size=1)["hits"]["hits"][0]["_source"]["questionnaire"]
    #check if user has a previous plan
    previous_plan=res = es.search(index="plan", body={"query":{'match' : {"userid":current_user.userid}}},size=100)["hits"]["hits"] #TODO: change to most recent rather than top 100
    if previous_plan!=[]:
        history=previous_plan[0]["_source"]["history"]
    else:
        history=[]
    if base_questionnaire==[]:
        raise HTTPException(status_code=500,detail="Missing baseline questionannaire")
    # else:
    #     #merges baseline questionnaire with new info
    #     if plan_info.questionnaire is not None:
    #         complete_questionnaire=questionnaire[0]["_source"]["questionnaire"] | plan_info.questionnaire
    #     else:
    #         complete_questionnaire=questionnaire[0]["_source"]["questionnaire"]
    

    curr_dt = datetime.datetime.now()
    exercises=generate_plan_exercise(base_questionnaire,plan_info.questionnaire,plan_info.exercises_duration)
    # print(list(map(lambda x: es.search(index="data_description", query={'match' : {"ExerciseID":x}},size=100)["hits"]["hits"][0]["_source"],exercises)))
    complete_plan={
                    "userid":current_user.userid,
                    "created":int(curr_dt.timestamp()*1000),
                    "start":int(datetime.datetime.combine(curr_dt, datetime.time.min).timestamp()*1000),
                    "end":int(datetime.datetime.combine(curr_dt+datetime.timedelta(days=7), datetime.time.max).timestamp()*1000),
                    "exercises_duration":plan_info.exercises_duration,
                    "history":history,
                    "plan":{
                        "date":int(curr_dt.timestamp()*1000),
                        "educations":generate_plan_education(current_user,base_questionnaire,plan_info.questionnaire),
                        "exercises":exercises,
                        "activity":generate_activity_goal(current_user)
                    },
                    "done":{
                        "steps":0,
                        "date":int(curr_dt.timestamp()*1000),
                        "exercises":[],
                        "educations":[],
                        "activity": {
                                    "goal": 0,
                                    "recommended_max": 0,
                                    "recommended_min": 0
                                    }
                        } #TODO: what is this supposed to be? Woulfnt it just be 0?
                   }
    
    #TODO: need to check if plan is valid first
    print(complete_plan)
    es.index(index='plan', body=json.dumps(complete_plan))


    #should exercises also be added to the Exercise ES index?
    return complete_plan


class Exercise(BaseModel):
    exerciseid:str
    performed:int
    repsperformed1:int
    repsperformed2:int
    repsperformed3:int
    status:str



@router.post("/exercise")
async def exercise(
    current_user: Annotated[User, Depends(get_current_user)],
    exercises: list[Exercise]
):
    exercise_dicts=list(map(lambda x: dict(x),exercises))
    for exercise_item in exercise_dicts:
        exercise_item["userid"]=current_user.userid
        exercise_item["date"]=int(datetime.datetime.now().timestamp())
    helpers.bulk(es,exercise_dicts,index="exercise")
    # return {"status":"Success"}

class Education_item(BaseModel):
    educationid:str
    is_quiz:bool
    is_correct:bool


@router.post("/education")
async def education(
    current_user: Annotated[User, Depends(get_current_user)],
    education_items: list[Education_item]
):
    eudcation_dicts=list(map(lambda x: dict(x),education_items))
    for education_item in eudcation_dicts:
        education_item["userid"]=current_user.userid
        education_item["date"]=int(datetime.datetime.now().timestamp())
    helpers.bulk(es,eudcation_dicts,index="education")
    



@router.get("/latest")
async def latest(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if not es.indices.exists(index="plan"):
        es.indices.create(index = 'plan')
    res=es.search(index="plan", query={'match' : {"userid":current_user.userid}},size=1)["hits"]["hits"]
    # print(res)
    if res==[]:
        return []
    res=res[0]["_source"]

    return res



class Goal(BaseModel):
    goal:int

@router.put("/activity_goal/{goal}")
async def activity_goal(
    current_user: Annotated[User, Depends(get_current_user)],
    goal:int
):
    # print(request.query_params)
    res=es.search(index="plan", query={'match' : {"userid":current_user.userid}},size=1)["hits"]["hits"]
    plan=res[0]["_source"]
    plan["plan"]["activity"]["goal"]=goal
    es.update(index='plan',id=res[0]["_id"],body={"doc":plan})
    return plan
class Day(BaseModel):
    day:str

@router.get("/on")
async def on(
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




@router.get("/exercise/completed/{plan_start}")
async def exercise_completed_get(
    current_user: Annotated[User, Depends(get_current_user)],
    plan_start
    
):
    exercises=es.search(index="exercise", query={
        "bool": {
      "filter": [
        {
          "range": {
            "date":{
              "gte":plan_start
            }
          }
        },
      ]
    }},size=100)["hits"]["hits"]
    if exercises!=[]:
        return list(map(lambda x: x["_source"],exercises))
    return exercises

@router.get("/education/completed")
async def education_completed_get(
    current_user: Annotated[User, Depends(get_current_user)],
):
    
    res=es.search(index="plan", query={'match' : {"userid":current_user.userid}},size=1)["hits"]["hits"]
    if res==[]:
        return []
    res=res[0]["_source"]
   
    return res["done"]["educations"] 
    

@router.get("/can_skip_exercise")
async def can_skip(
    current_user: Annotated[User, Depends(get_current_user)],
    exercise_id
    ):
    #fetch plan for correct user
    plan_query=es.search(index="plan", query={'match' : {"userid":current_user.userid}},size=100)["hits"]["hits"][-1]
    plan_id=plan_query["_id"]
    plan=plan_query["_source"]["plan"]
    exercise=es.search(index="data_description", query={'match' : {"ExerciseID":exercise_id}},size=100)["hits"]["hits"][0]["_source"]

    exercises_from_plan=plan["exercises"]
    exercise_type=exercise["Type"]
    # print(exercises_from_plan,"sleem")
    #find if there are any exercises of same type that have been skipped
    # print(exercise)
    # print(list(filter(lambda x: ("skipped" in x.keys()) and (x["Type"]==exercise_type),exercises_from_plan )))
    if []==list(filter(lambda x: ("skipped" in x.keys()) and (x["Type"]==exercise_type),exercises_from_plan )) and exercise_id in list(map(lambda x: x["ExerciseID"], exercises_from_plan)):
        plan["exercises"]=list(filter(lambda x: x["ExerciseID"]!=exercise_type,exercises_from_plan))
        exercise["skipped"]=True
        plan["exercises"].append(exercise)
    else:
        return {"value":False}
    new_plan=plan_query["_source"].copy()
    new_plan["plan"]=plan
    es.update(index='plan', body=json.dumps(new_plan),id=plan_id)
    return {"value":True}



@router.get("/tailoring")
async def tailoring(
    current_user: Annotated[User, Depends(get_current_user)],
):
    res = es.search(index="data_description",query={"match":{"description_type":"tailoring"}},size=900)
    tailoring=list(map(lambda x: x["_source"],res["hits"]["hits"]))
    # print(tailoring)
    return tailoring
