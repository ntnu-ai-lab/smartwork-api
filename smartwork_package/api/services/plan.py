from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel
from elasticsearch import Elasticsearch
from api.resources.constants import *
from api.services.oauth import User,get_current_user
from elasticsearch import helpers
import json
from typing import Annotated
from typing import Optional
from api.services.patient import activity_done
import datetime
import requests
import functools
import math
from functools import cmp_to_key
import random
from api.resources.constants import FIRST_WEEK_EDUCATION,FIRST_WEEK_EXERCISES,ES_PASSWORD,ES_URL,MYCBR_URL
from api.achievements.check_achievements import complete_quiz,complete_educational_read,update_goal
from api.resources.custom_router import LoggingRoute
es = Elasticsearch(ES_URL,basic_auth=("elastic",ES_PASSWORD),verify_certs=False)
import re


router = APIRouter(prefix="/patient/plan",route_class=LoggingRoute,tags=["Plan"])




class Plan_info(BaseModel):
    questions:Optional[list]#changed from questionnaire to questions
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
    if "BT_pain_average_prev" in questionnaire_updated.keys():
        questionnaire_updated["BT_pain_average_change"]=questionnaire_updated["BT_pain_average"]-questionnaire_updated["BT_pain_average_prev"]
    else:
        questionnaire_updated["BT_pain_average_change"]=0

    if "T_cpg_function_prev" in questionnaire_updated.keys() and "T_cpg_function" in questionnaire_updated.keys():
        questionnaire_updated["T_cpg_function_change"]=questionnaire_updated["T_cpg_function"]-questionnaire_updated["T_cpg_function_prev"]
    else:
        questionnaire_updated["T_cpg_function_change"]=0
    remove_education=[]
    add_educations=[]
    remove_educations=[]
    if questionnaire_updated["BT_pain_average"]>=7:
        remove_education=BT_PAIN_AVERAGE_HIGH_RM
        add_education=BT_PAIN_AVERAGE_HIGH_ADD
        remove_educations.extend(remove_education)
        add_educations.extend(add_education)
    if questionnaire_updated["BT_pain_average_change"]>=3:
        remove_education=BT_PAIN_AVERAGE_CHANGE_RM
        add_education=BT_PAIN_AVERAGE_CHANGE_ADD
        remove_educations.extend(remove_education)
        add_educations.extend(add_education)
    if questionnaire_updated["BT_pain_average"]>=3 and questionnaire_updated["BT_pain_average"]<=6:
        remove_education=BT_PAIN_AVERAGE_MEDIUM_RM
        add_education=BT_PAIN_AVERAGE_MEDIUM_ADD
        remove_educations.extend(remove_education)
        add_educations.extend(add_education)
    if "T_cpg_function" in questionnaire_updated.keys():
        if questionnaire_updated["T_cpg_function"]>=5:
            add_education=T_CPG_ADD
            add_educations.extend(add_education)
    if "T_cpg_function_change" in questionnaire_updated.keys():
        if questionnaire_updated["T_cpg_function_change"]>=2:
            add_education=T_CPG_CHANGE_ADD
            add_educations.extend(add_education)
    if "T_tampa_fear" in questionnaire_updated.keys():
        if questionnaire_updated["T_tampa_fear"]>=5:
            remove_education=TAMPA_RM
            add_education=TAMPA_ADD
            remove_educations.extend(remove_education)
            add_educations.extend(add_education)
    if "BT_wai" in questionnaire_updated.keys():
        if questionnaire_updated["BT_wai"]>=3:
            add_education=BT_WAI_ADD
            add_educations.extend(add_education)
    if "T_sleep" in questionnaire_updated.keys():
        if questionnaire_updated["T_sleep"] in ["Several times a week", "Sometimes"]:
            add_education=T_SLEEP_ADD
            add_educations.extend(add_education)
    if "BT_pseq_2item" in questionnaire_updated.keys():
        if questionnaire_updated["BT_pseq_2item"]<=8:
            add_education=BT_PSEQ_ADD
            add_educations.extend(add_education)
    if "BT_pss" in questionnaire_updated.keys():
        if questionnaire_updated["BT_pss"]>=6:
            add_education=BT_PSS_ADD
            add_educations.extend(add_education)
    if "BT_phq_2item" in questionnaire_updated.keys():
        if questionnaire_updated["BT_phq_2item"]>=1:
            add_education=BT_PHQ_ADD
            add_educations.extend(add_education)
    if "T_barriers" in questionnaire_updated.keys():
        if "lack_of_time" in questionnaire_updated["T_barriers"]:
            add_education=BARRIERS_TIME_ADD
            add_educations.extend(add_education)
        if "too_tired" in questionnaire_updated["T_barriers"]:
            add_education=BARRIERS_TIRED_ADD
            add_educations.extend(add_education)
        if "lack_of_support" in questionnaire_updated["T_barriers"]:
            add_education=BARRIERS_SUPPORT_ADD
            add_educations.extend(add_education)
        if "family_work" in questionnaire_updated["T_barriers"]:
            add_education=BARRIERS_FAMILY_ADD
            add_educations.extend(add_education)
        if "weather" in questionnaire_updated["T_barriers"]:
            add_education=BARRIERS_WEATHER_ADD
            add_educations.extend(add_education)
        if "facilities" in questionnaire_updated["T_barriers"]:
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
    # print(base_questionnaire)
    
    mycbr_keys=['Dem_age', 'T_tampa_fear', 'T_sleep', 'BT_PHQ_2item', 'F_GPE', 'Dem_bmi', 'Dem_weight', 'Pain_medication', 'Pain_self_efficacy', 'T_cpg_function', 'Education', 'EQ5D_selfcare', 'Primary_pain_site', 'BT_wai', 'Sleep_day', 'EQ5D_mobility', 'BIPQ_life', 'BIPQ_symptoms', 'Dem_gender', 'BT_PSS', 'BT_PSEQ_2item', 'BIPQ_pain_continuation', 'RMDQ', 'PSS', 'FABQ_lbp_cause', 'Comorbidities', 'BIPQ_concern', 'BIPQ_understanding', 'F_PASS', 'BIPQ_control', 'EQ5D_anxiety', 'SaltinGrimby', 'Activity_StepCount', 'T_barriers', 'PSFS_activity', 'BT_pain_average', 'MSKHQ', 'Pain_sites', 'SelfManagement_Exercise', 'Dem_height', 'NDI', 'Pain_1year', 'Employment', 'PSFS_score', 'Sleep_wakeup', 'EQ5D_activity', 'Sleep_end', 'FABQ', 'BIPQ_selfmanagement', 'EQ5D_pain', 'BIPQ_emotion', 'Sleep_difficulty', 'PSFS_activity_name', 'Pain_worst', 'SelfManagement_Education', 'Work_characteristics', 'Family', 'EQ5D', 'SelfManagement_Activity']
    rel_keys=list(filter(lambda x: (x in mycbr_keys) and (x in base_questionnaire.keys()),base_questionnaire.keys()))
    # print(base_questionnaire)
    reduced_questionnaire=dict((k, re.sub(r"(\.0*)$", "", str(base_questionnaire[k]))) for k in rel_keys)
    # print(reduced_questionnaire)
    # raise
    response=requests.post(f"{MYCBR_URL}/concepts/Case/casebases/sbcases/amalgamationFunctions/SMP_Education/retrievalByMultipleAttributes",
                      json=reduced_questionnaire,
                      params={"k":-1}
    )
    cbr_education_items=set("".join(list(map(lambda x: x["SelfManagement_Education"],response.json()))).strip(";").split(";"))
    cbr_education_items=list(filter(lambda x: x!="",cbr_education_items))
    return cbr_education_items

def isquiz(educationid,userid):
    education_description=es.get(index="education_description", id=educationid).body["_source"]["question"]
    has_question=education_description is not None 
    if not has_question: #educational item does not have a question
        return False
    try:
        #means it has been shown and read previously 
        education_item=es.get(index="education", id=userid+educationid)
        if education_item.body["_source"]["is_correct"]:#has been answered correctly perviously
            return False
        return True
    except:
        return False

def generate_plan_education(current_user,base_questionnaire,update_questionnaire):

    # if not es.indices.exists(index="education_queue"):
    #     es.indices.create(index = 'education_queue')

    # res=es.search(index="education_queue", body={"query":{'match' : {"userid":current_user.userid}}},size=1)["hits"]["hits"]
    # if res==[]:
    #     priority_queue=[]
    # else:
    #     priority_queue=res[0]["_source"]["educational_items"].copy()

    #fetch all educational items
    educational_items = es.search(index="education_description", query={'match_all' : {}},size=1000)["hits"]["hits"]
    educational_items=list(map(lambda x: x["_source"],educational_items))
    # print(educational_items)
    educational_items_w_question=list(filter(lambda x: x["question"] is not None,educational_items))

    educational_items_w_question=list(map(lambda x: x["educationid"],educational_items_w_question))

    # has_quiz_question=list(filter(lambda x: x ,educational_items))
    #fetch performed exercises and exercises that were part of previous plan
    performed_items=es.search(index="education", body={"query":{'match' : {"userid":current_user.userid}}},size=1)["hits"]["hits"]
    this_weeks_plan=es.search(index="plan", body={"query":{'match' : {"userid":current_user.userid}}},size=1,sort=[{"created": {"order": "desc"}}])["hits"]["hits"][0]["_source"]["plan"]

    this_weeks_educations=list(map(lambda x: x["educationid"],this_weeks_plan["educations"]))

    if performed_items!=[]:
        educational_items_used=list(map(lambda x: x["_source"]["educationid"],performed_items))
        educational_items_thisweek=list(filter(lambda x: x["_source"]["educationid"] in this_weeks_plan,performed_items))
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
    # print(selected_educational_items)
    #figure out if educational item is used before by checking history of user from es, same for thisweek
    selected_educational_items=list(map(lambda x: {"educationid":x,
                                                   "used":x in educational_items_used,
                                                   "canbequiz": x in educational_items_w_question and x not in educational_items_used,
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
        # print(generic_items_w_groups)
        for generic_item in generic_items_w_groups:
            if generic_item["group"] not in groups:
                today=datetime.datetime.now() + datetime.timedelta(days=1)
                result.append({
                    "educationid":generic_item["educationid"],
                    "priority":1,
                    "expiredate":(today+datetime.timedelta(weeks=1)).timestamp(),
                    "thisweek":False,
                    "group":generic_item["group"],
                    "avoid":False,
                    "excluded":False,
                    "used":False,
                    "usednumber":0,
                    "lastusage":0,
                    "lastquiz":False,
                })
                groups.add(generic_item["group"])
            if len(result)>=7:
                break
    # result=list(map(lambda x: x|{"educationid":x["educationid"]},result))
            
    # for item in result:
    #     item["is_quiz"]=True
    #     item["is_correct"]=False
    #TODO: store updated priority queue in elasticsearch   
    for item in result[:7]:
        item["is_quiz"]=isquiz(item["educationid"],current_user.userid)
    # print(result[:7])
    return result[:7]


def check_pain_relief(questionnaire):
    if "BT_pain_average" not in questionnaire.keys():
        return False
    if questionnaire["BT_pain_average"]>=7:
        return True
    if "BT_pain_average_prev" in questionnaire.keys():
        bt_pain_change=questionnaire["BT_pain_average"]-questionnaire["BT_pain_average_prev"]
        if (questionnaire["BT_pain_average"]<=2 and bt_pain_change>=4) or (questionnaire["BT_pain_average"]>=3 and questionnaire["BT_pain_average"]<=6 and bt_pain_change>=3):
            return True
    return False

def calc_sets_reps(duration):
    if duration<=15:
        return {"number":3,"sets":duration//5,"repetitions":10}
    return {"number":duration//5,"sets":3,"repetitions":10}

def add_core_back_ab(cbr_exercise_items,es_exercise_items):
    exercises=[]
    for grouping in ["Ab","Back","Core"]:
        cbr_exercise_grouping=list(filter(lambda x: x["type"]==grouping,cbr_exercise_items))
        es_exercise_grouping=list(filter(lambda x: grouping==x["type"],es_exercise_items))
        if cbr_exercise_grouping!=[]:
            exercises.append(random.choice(cbr_exercise_grouping))
        else:
            #if no exercise from group is available in cbr exercises use es
            exercises.append(random.choice(es_exercise_grouping))
    # print(exercises)
    # raise
    return exercises

def add_other_types(exercise_set,number_exercises,selected_exercises):
    exercises=[]
    already_selected_types=set(map(lambda x: x["type"] ,selected_exercises))
    all_existing_types=set(map(lambda x: x["type"] ,exercise_set))
    new_types=set(filter(lambda x: x not in already_selected_types ,all_existing_types))
    for new_type in new_types:
        # print(new_type)
        ex_w_new_type=list(filter(lambda x: new_type==x["type"],exercise_set))
        exercises.append(ex_w_new_type[0])
        # print(exercises)
        # raise
        if len(exercises)==number_exercises:
            return exercises
    return exercises
def add_same_type(selected_exercises,exercise_set,number_exercises):
    # print("add_same_type")
    exercises=[]
    types_of_exercises_selected=set(map(lambda x: x["type"] ,selected_exercises))
    for ex_type in types_of_exercises_selected:
        cbr_ex_type_exercises=list(filter(lambda x: ex_type==x["type"],exercise_set))
        for exercise in cbr_ex_type_exercises:
            if exercise not in selected_exercises:
                # print(exercise)
                # raise
                exercises.append(exercise["exerciseid"])
            if len(exercises)==number_exercises:
                return exercises
    return exercises
            
def get_pain_relief_exercises(cbr_exercise_items,es_exercise_items,number_exercises):
    # print("get_pain_relief_exercises")
    # raise
    exercises=[]
    #add exercises from cbr system that are pain relief
    cbr_pain_exercises=list(filter(lambda x: "pain_" in x,cbr_exercise_items))
    exercises.extend(cbr_pain_exercises)
    #if not enough add exercises from elasticsearch
    ex_num=0
    while len(exercises)<number_exercises:
        es_pain_exercises=list(filter(lambda x: "pain_" in x["exerciseid"],es_exercise_items))
        if es_pain_exercises[ex_num]["exerciseid"] not in exercises:
            exercises.append(es_exercise_items[ex_num])
        ex_num+=1
    # print(exercises)
    # raise
    return exercises[:number_exercises]

def generate_plan_exercise(base_questionnaire,update_questionnaire,duration):
    #fetch exercises from cbr 
    # print(base_questionnaire)
    rel_attributes=['Activity_StepCount', 'BIPQ_concern', 'BIPQ_control', 'BIPQ_emotion', 'BIPQ_life', 'BIPQ_pain_continuation', 'BIPQ_selfmanagement', 'BIPQ_symptoms', 'BIPQ_understanding', 'BT_PHQ_2item', 'BT_PSEQ_2item', 'BT_PSS', 'BT_pain_average', 'BT_wai', 'Comorbidities', 'Dem_age', 'Dem_bmi', 'Dem_gender', 'Dem_height', 'Dem_weight', 'EQ5D', 'EQ5D_activity', 'EQ5D_anxiety', 'EQ5D_mobility', 'EQ5D_pain', 'EQ5D_selfcare', 'Education', 'Employment', 'FABQ', 'FABQ_lbp_cause', 'F_GPE', 'F_PASS', 'Family', 'MSKHQ', 'NDI', 'PSFS_activity', 'PSFS_activity_name', 'PSFS_score', 'PSS', 'Pain_1year', 'Pain_medication', 'Pain_self_efficacy', 'Pain_sites', 'Pain_worst', 'Primary_pain_site', 'RMDQ', 'SaltinGrimby', 'SelfManagement_Activity', 'SelfManagement_Education', 'SelfManagement_Exercise', 'Sleep_day', 'Sleep_difficulty', 'Sleep_end', 'Sleep_wakeup', 'T_barriers', 'T_cpg_function', 'T_sleep', 'T_tampa_fear', 'Work_characteristics']
    reduced_questionnaire={}
    for k in base_questionnaire:
        if k in rel_attributes:
            isfloat=False
            temp_value=base_questionnaire[k]
            try:
                float(temp_value)
                isfloat=True
            except:
                pass

            if isfloat:
                temp_value=float(temp_value)
                if temp_value.is_integer():
                    temp_value=int(temp_value)
            reduced_questionnaire[k]=str(temp_value)
    # print(reduced_questionnaire)
    response=requests.post(f"{MYCBR_URL}/concepts/Case/casebases/sbcases/amalgamationFunctions/SMP_Exercise/retrievalByMultipleAttributes",
                      json=reduced_questionnaire,
                      params={"k":-1}
    )
    # print(response.json())
    # raise
    #get exercise names from cbr
    cbr_exercise_items=list(set("".join(list(map(lambda x: x["SelfManagement_Exercise"],response.json()))).split(";")))
    # print(cbr_exercise_items)
    # raise
    #lookup each of the names in ES to get additional info on the exercises
    cbr_exercise_items=es.search(index="exercise_description", query={"bool": {"filter": {"terms": {"exerciseid": cbr_exercise_items}}}},size=10000)["hits"]["hits"]
    cbr_exercise_items=list(map(lambda x: x["_source"],cbr_exercise_items))
    #fetch exercises from rulebase
    es_exercise_items = es.search(index="exercise_description", query={'match' : {"description_type":"exercise"}},size=10000)["hits"]["hits"]
    es_exercise_items=list(map(lambda x: x["_source"],es_exercise_items))
    #filter level of exercises
    res=es.search(index="exercise", query={'match' : {"userid":"stuart"}})
    exercises_performed=res.body["hits"]["hits"]
    total_reps=list(map(lambda x: x["repsperformed1"]+x["repsperformed2"]+x["repsperformed3"],exercises_performed))
    if len(exercises_performed)==0:
        percentage_reps=0
    else:
        percentage_reps=sum(total_reps)/(30*len(exercises_performed))#assume 10 per set
    total_exercise_time=len(exercises_performed)*5
    exercise_level=1
    if total_exercise_time>=45 and percentage_reps>=1:
        exercise_level+=1

    es_exercise_items=list(filter(lambda x: x["level"]==exercise_level,es_exercise_items))
    cbr_exercise_items=list(filter(lambda x: x["level"]==exercise_level,cbr_exercise_items))
    number_exercises=calc_sets_reps(duration)["number"]
    exercises=[]
    if update_questionnaire:
        if check_pain_relief(update_questionnaire):
            return get_pain_relief_exercises(cbr_exercise_items,es_exercise_items,number_exercises)

    #######not pain relief
    #add random exercise from back,ab and core from cbr system
    exercises.extend(add_core_back_ab(cbr_exercise_items,es_exercise_items))
    # print(list(map(lambda x: x["exerciseid"],exercises)))
    if len(exercises)==number_exercises:
        return exercises

    # print(exercises,"post ab back")
    #add exercises of types that are not already in exercises list
    exercises.extend(add_other_types(cbr_exercise_items,number_exercises-len(exercises),exercises))
    # print(list(map(lambda x: x["exerciseid"],exercises)))
    if len(exercises)==number_exercises:
        return exercises
    
    #same as above but for exercises from elasticsearch
    exercises.extend(add_other_types(es_exercise_items,number_exercises-len(exercises),exercises))
    # print(list(map(lambda x: x["exerciseid"],exercises)))
    if len(exercises)==number_exercises:
        return exercises
    
    # print(exercises,"other types es")
    #if there are still slots to fill and all types are represented add one more of each type until filled
    exercises.extend(add_same_type(exercises,cbr_exercise_items,number_exercises-len(exercises)))
    if len(exercises)==number_exercises:
        return exercises
    # print(list(map(lambda x: x["exerciseid"],exercises)))
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
    prev_plan=es.search(index="plan", body={"query":{'match' : {"userid":current_user.userid}}},size=1)["hits"]["hits"]
    if prev_plan==[]:
        return {
        "goal":STEP_GOAL_MIN,
        "recommended_min":STEP_GOAL_MIN,
        "recommended_max":STEP_GOAL_MAX
        }
    prev_plan=es.search(index="plan", body={"query":{'match' : {"userid":current_user.userid}}},size=1,sort=[{"created": {"order": "asc"}}])["hits"]["hits"][0]["_source"]
    prev_steps=prev_plan["done"]["steps"]
    
    if prev_steps>STEP_GOAL_MAX:
        prev_steps=STEP_GOAL_MAX
    elif prev_steps<STEP_GOAL_MIN:
        prev_steps=STEP_GOAL_MIN
    
    # average between last week goal and steps done
    #TODO: assumes latest plan is latest in history
    previous_goal=prev_plan["plan"]["activity"]["goal"]
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
    if current_plan["start"]<datetime.datetime.now().timestamp() and current_plan["end"]>datetime.datetime.now().timestamp():
        return True
    return False
    

def generate_plan(current_user,plan_info,educations,exercises):
    curr_dt = datetime.datetime.now()
    return {
                    "userid":current_user.userid,
                    "created":int(curr_dt.timestamp()),
                    "start":datetime.datetime.combine(curr_dt, datetime.time.min).timestamp(),
                    "end":datetime.datetime.combine(curr_dt+datetime.timedelta(days=7), datetime.time.max).timestamp(),
                    "exercises_duration":plan_info.exercises_duration,
                    # "history":history,
                    "plan":{
                        "date":curr_dt.timestamp(),
                        "educations":educations,
                        "exercises":exercises,
                        "activity":generate_activity_goal(current_user)
                    },
                    "done":{
                        "steps":0,
                        "date":curr_dt.timestamp(),
                        "exercises":[],
                        "educations":[],
                        "activity": {
                                    "goal": 0,
                                    "recommended_max": 0,
                                    "recommended_min": 0
                                    }
                        } #TODO: what is this supposed to be? Woulfnt it just be 0?
                   }

def find_previous_stepcounts(previous_plans,userid):
    final_activity=""
    for i,previous_plan in enumerate(previous_plans):
        # print(previous_plan["_source"]["start"])
        activity=activity_done(previous_plan["_source"]["start"],previous_plan["_source"]["end"],userid)
        final_activity+=str(i)+":"+str(activity)+";"
    return final_activity

@router.post("/next")
async def next(
    current_user: Annotated[User, Depends(get_current_user)],
    plan_info: Plan_info
):
    print("neeeeext")
    es.index(index="tailoring", document={"userid":current_user.userid,"date":datetime.datetime.now().timestamp(),"questionnaire":plan_info.questions})
    all_plans=es.search(index="plan",body={"query":{'match' : {"userid":current_user.userid}}},size=1000)["hits"]["hits"]
    #set standard first week plan
    if all_plans==[]:
        response = es.mget(index="education_description", body={"ids": FIRST_WEEK_EDUCATION})
        educations=list(map(lambda x: x["_source"],response["docs"]))
        
        response = es.mget(index="exercise_description", body={"ids": FIRST_WEEK_EXERCISES})
        exercises=list(map(lambda x: x["_source"],response["docs"]))[:plan_info.exercises_duration//5]
        # print(exercises)
        # print(educations)
        # raise
        complete_plan=generate_plan(current_user,plan_info,educations,exercises)
        es.index(index='plan', document=complete_plan)
        es.indices.refresh(index='plan')
        return complete_plan
    all_plans.sort(key=lambda x: x["_source"]["created"],reverse=True)
    current_plan=all_plans[0]["_source"]
    # if plan_is_active(current_plan):
    #     raise HTTPException(status_code=500,detail="User already has a valid plan.")
    #check if user has questionnaire
    base_questionnaire = es.search(index="questionnaire", body={"query":{'match' : {"userid":current_user.userid}}},size=1)["hits"]["hits"][0]["_source"]["questionnaire"]
    #check if user has a previous plan
    previous_plans = es.search(index="plan", query={'match' : {"userid":current_user.userid}},sort=[{"created": {"order": "asc"}}],size=1)["hits"]["hits"]

    if base_questionnaire==[]:
        raise HTTPException(status_code=500,detail="Missing baseline questionannaire")
    else:
        #merges baseline questionnaire with new info
        if plan_info.questions is not None:
            tailoring_questionnaire=dict(map(lambda x: (x["questionid"],int(x["answer"]) if x["answer"].isnumeric() else x["answer"]) ,plan_info.questions))
            # if "BT_pain_average_prev" not in tailoring_questionnaire.keys():
            #     tailoring_questionnaire["BT_pain_average_prev"]=0
            # if "T_cpg_function_prev" not in tailoring_questionnaire.keys():
            #     tailoring_questionnaire["T_cpg_function_prev"]=0
            # if "T_cpg_function" not in tailoring_questionnaire.keys():
            #     tailoring_questionnaire["T_cpg_function"]=0
            complete_questionnaire=base_questionnaire | tailoring_questionnaire
        else:
            complete_questionnaire=base_questionnaire
        complete_questionnaire["Activity_StepCount"]=find_previous_stepcounts(previous_plans,current_user.userid)
    if tailoring_questionnaire is not None:
        tmp_questionnaire=tailoring_questionnaire.copy()
        tmp_questionnaire["userid"]=current_user.userid
        tmp_questionnaire["date"]=datetime.datetime.now().timestamp()
        es.index(index='tailoring_questionnaire', document=tmp_questionnaire)

    exercises=generate_plan_exercise(complete_questionnaire,tailoring_questionnaire,plan_info.exercises_duration)
    print(exercises)
    # raise
    # exercises=es.mget(index="exercise_description", body={"ids": exercises})["docs"]
    # exercises=list(map(lambda x: x["_source"],exercises))
    educations=generate_plan_education(current_user,complete_questionnaire,tailoring_questionnaire)
    educations=es.mget(index="education_description", body={"ids": list(map(lambda x: x["educationid"],educations)) })["docs"]
    educations=list(map(lambda x: x["_source"],educations))
    # print(list(map(lambda x: es.search(index="data_description", query={'match' : {"ExerciseID":x}},size=100)["hits"]["hits"][0]["_source"],exercises)))
    complete_plan=generate_plan(current_user,plan_info,educations,exercises)
    # print(complete_plan)
    # raise
    # raise
    #TODO: need to check if plan is valid first
    update_goal(current_user.userid,"SessionCompleted")
    if es.exists(index="appsettings", id=current_user.userid):
        es.update(index="appsettings",id=current_user.userid,doc={"hideIntroSession":True})
    # print(complete_plan)
    # raise
    es.index(index='plan', document=complete_plan)
    es.indices.refresh(index='plan')
    # print(complete_plan)
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
    # exerciseid: list
    request:Request
):
    exercises=await request.json()
    status=exercises[0]["status"]
    exerciseid=exercises[0]["exerciseid"]

    res=es.search(
        index="plan",
        query={'match': {"userid": current_user.userid}},
        sort=[{"created": {"order": "desc"}}],
        size=1
    )["hits"]["hits"]
    id=res[0]["_id"]
    doc=res[0]["_source"]
    if status=="skip" or status=="skip_replace":
        for exercise in doc["plan"]["exercises"]:
                if exercise["exerciseid"]==exerciseid:
                    exercise["skipped"]=True
    if status=="skip":
        es.update(index="plan",id=id,doc=doc)
        return {"status":200}
    elif status=="skip_replace":
        reason=exercises[0]["reason"]
        original_exercise = es.search(index="exercise_description",query={"match":{"exerciseid":exerciseid}},size=900)
        original_exercise=original_exercise["hits"]["hits"][0]
        original_level = original_exercise["_source"]["level"]
        original_type = original_exercise["_source"]["type"]
        if reason=="pain":
            new_level=original_level
        elif reason=="easy":
            new_level=original_level+1
        elif reason=="difficult":
            new_level=original_level-1
        elif reason=="instruction_unclear":
            new_level=original_level
            
        new_level=min([new_level,6])
        new_level=max([new_level,1])
        # print(original_type,new_level)
        new_exercise=es.search(index="exercise_description",query={"bool":
                                                {"must":[
                                                    {"match":{"type":original_type}},
                                                        {"match":{"level":new_level}}
                                                ],
                                                "must_not":[{"match":{"exerciseid":exerciseid}}]
                                        
                                        }},size=900).body["hits"]["hits"][0]["_source"]
        doc["plan"]["exercises"].append(new_exercise)
        es.update(index="plan",id=id,doc=doc)
        return {"status":200}
    #check for status skip_replace
    # elif exercises[0]["status"]=="skip_replace":
    #easy, difficult,instruction_unclear,pain


    exercise_dicts=list(map(lambda x: dict(x),exercises))
    for exercise_item in exercise_dicts:
        exercise_item["userid"]=current_user.userid
        exercise_item["_id"]=current_user.userid+"_"+exercise_item["exerciseid"]
        exercise_item["date"]=int(datetime.datetime.now().timestamp())
    # doc["plan"]["exercises"]=doc["plan"]["exercises"].extend(exercise_dicts)
    doc["done"]["exercises"].extend(exercise_dicts)
    es.update(index="plan",id=id,doc=doc)
    helpers.bulk(es,exercise_dicts,index="exercise")
    return {"status":200}

class Education_item(BaseModel):
    educationid:str
    is_quiz:bool
    is_correct:bool


@router.post("/education")
async def education(
    current_user: Annotated[User, Depends(get_current_user)],
    education_items: list[Education_item]
):
    complete_educational_read(current_user.userid)
    education_dicts=list(map(lambda x: dict(x),education_items))
    for education_item in education_dicts:
        if education_item["is_quiz"]:
            complete_quiz(current_user.userid)
        education_item["_id"]=current_user.userid+"_"+education_item["educationid"]
        education_item["userid"]=current_user.userid
        education_item["date"]=int(datetime.datetime.now().timestamp())
    # raise
    helpers.bulk(es,education_dicts,index="education")
    plan=es.search(
        index="plan",
        query={'match': {"userid": current_user.userid}},
        sort=[{"created": {"order": "desc"}}],
        size=1
    )["hits"]["hits"]
    doc=plan[0]["_source"]
    # print(education_dicts)
    doc["done"]["educations"].extend(education_dicts)
    es.update(index="plan",id=plan[0]["_id"],doc=doc)
    



@router.get("/latest")
async def latest(
    current_user: Annotated[User, Depends(get_current_user)],
):
    res=es.search(index="plan", query={'match' : {"userid":current_user.userid}},size=999)["hits"]["hits"]
    print(res)
    if res==[]:
        # one_week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
        return []
    # if datetime.datetime.fromisoformat(res[0]["_source"]["endDate"])<datetime.datetime.now():
    #     return []
    plans=list(map(lambda x: x["_source"],res))
    plans.sort(key=lambda x: x["created"],reverse=True)
    # print(list(map(lambda x: x["created"],plans)))
    plan=plans[0]
    # print(plans)
    plan["plan"]["exercises"]=list(filter(lambda x: "skipped" not in x.keys(),plan["plan"]["exercises"]))
    # if  not plan_is_active(plan):
    #     return []
    plan["planExpired"]=True
    return plan



class Goal(BaseModel):
    goal:int

@router.put("/activity_goal/{goal}")
async def activity_goal(
    current_user: Annotated[User, Depends(get_current_user)],
    goal:int
):
    # print(request.query_params)
    res=es.search(index="plan", query={'match' : {"userid":current_user.userid}},sort=[
    {
      "start": {
        "order": "desc"
      }
    }
  ],size=1)["hits"]["hits"]
    plan=res[0]["_source"]
    plan["plan"]["activity"]["goal"]=goal
    es.update(index='plan',id=res[0]["_id"],doc=plan)
    return plan

def get_between(index,start,end,userid):
    return es.search(index=index, query={
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
                           "gte": start,  
                            "lte": end
                        }
                    }
                }
            ]
        }
    })["hits"]["hits"]


@router.get("/on/{day}")
async def on(
    current_user: Annotated[User, Depends(get_current_user)],
    day: str
):
    query_date=datetime.datetime.strptime(day, "%Y-%m-%d")
    # query_date=query_date.timestamp()
    if query_date>datetime.datetime.now():
        return None
    start_time=datetime.datetime.combine(query_date,datetime.time.min).timestamp()
    end_time=datetime.datetime.combine(query_date,datetime.time.max).timestamp()
    # print(start_time,end_time)
    res=es.search(index="plan", query={
        "bool": {
            "must": [
                {
                    "match": {
                        "userid": current_user.userid
                    }
                },
                {
                    "range": {
                        "end": {
                            "gte": end_time
                        }
                    }
                },
                {
                    "range": {
                        "start": {
                           "lte": start_time,  
                        }
                    }
                }
            ]
        }
    })["hits"]["hits"]#[0]["_source"]["plan"]
    if len(res)==0:
        return None
    else:
        plan=res[0]["_source"]#["plan"]
    exercises=get_between("exercise",start_time,end_time,current_user.userid)
    educations=get_between("education",start_time,end_time,current_user.userid)
    activities=get_between("activity",start_time,end_time,current_user.userid)
    # print(activities)
    steps_done=sum(map(lambda x: x["_source"]["steps"],activities))
    # print(plan)
    # print(steps_done)
    plan["done"]={"exercises":exercises, "educations":educations,"activity":steps_done}

    return plan




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
    

@router.get("/can_skip_exercise/{exercise_id}")
async def can_skip(
    current_user: Annotated[User, Depends(get_current_user)],
    exercise_id
    ):
    #fetch plan for correct user
    plan_query=es.search(index="plan", query={'match' : {"userid":current_user.userid}},size=100)["hits"]["hits"][-1]
    plan_id=plan_query["_id"]
    plan=plan_query["_source"]["plan"]
    exercise=es.search(index="exercise_description", query={'match' : {"exerciseid":exercise_id}},size=100)["hits"]["hits"][0]["_source"]

    exercises_from_plan=plan["exercises"]
    exercise_type=exercise["type"]
    # print(exercises_from_plan,"sleem")
    #find if there are any exercises of same type that have been skipped
    # print(exercises_from_plan)
    skipped_exercises=list(filter(lambda x: ("skipped" in x.keys()) and (x["type"]==exercise_type),exercises_from_plan ))
    # print(skipped_exercises)
    if []==skipped_exercises: #and exercise_id in list(map(lambda x: x["exerciseid"], exercises_from_plan)):
        # plan["exercises"]=list(filter(lambda x: x["exerciseid"]!=exercise_type,exercises_from_plan))
        # exercise["skipped"]=True
        # plan["exercises"].append(exercise)
        return {"value":True}
    else:
        return {"value":False}
    # new_plan=plan_query["_source"].copy()
    # new_plan["plan"]=plan
    # es.update(index='plan', doc=new_plan,id=plan_id)

def physical_activity_progress(userid):
    goal=es.search(index="plan", query={'match' : {"userid":userid}},size=1,sort=[{"created": {"order": "asc"}}])["hits"]["hits"][0]["_source"]["plan"]["activity"]["goal"]
    activities=es.search(index="activity",query={'match' : {"userid":userid}},size=1)["hits"]["hits"]
    activities_past_week=list(filter(lambda x: datetime.datetime.fromtimestamp(x["_source"]["date"])>datetime.datetime.now()-datetime.timedelta(days=7),activities))
    total_steps=sum([x["_source"]["steps"] for x in activities_past_week])
    return total_steps/goal

def filter_tailoring(previous_tailorings,baseline,userid):
    pa_percentage=physical_activity_progress(userid)
    tailoring=["BT_pain_average"]
    if len(previous_tailorings)%2==0:
        tailoring.append("T_cpg_function")
    if (len(previous_tailorings)+2)%4==0 and len(previous_tailorings)>=2 and (int(baseline["T_tampa_fear"])>=2 or pa_percentage<0.5):
        tailoring.append("T_tampa_fear")
    if (len(previous_tailorings)+8)%8==0 and len(previous_tailorings)>=8 and int(baseline["BT_wai"])<=5:
        tailoring.append("BT_wai")
    if (len(previous_tailorings)+4)%4==0 and len(previous_tailorings)>=4 and int(baseline["BT_wai"])>5:
        tailoring.append("T_sleep")#missing logic
    pseq_total=list(map(lambda x: int(baseline[f"PSEQPre_SQ00{x}"]) if x<10 else int(baseline[f"PSEQPre_SQ0{x}"]),range(1,11)))
    pseq_total=sum(pseq_total)
    if (len(previous_tailorings)+2)%2==0 and len(previous_tailorings)>=2 and pseq_total<=24:
        tailoring.append("BT_pseq_5")
        tailoring.append("BT_pseq_9")
    if (len(previous_tailorings)+8)%8==0 and len(previous_tailorings)>=8 and int(baseline["BT_PSS"])>=14:
        tailoring.extend(["BT_PSS_2","BT_PSS_4","BT_PSS_5","BT_PSS_10"])
    if (len(previous_tailorings)+3)%4==0 and len(previous_tailorings)>=3 and int(baseline["BT_PHQ_2item"])>=2:
        tailoring.append("BT_phq_1")
        tailoring.append("BT_phq_2")
    if pa_percentage<0.75:
        tailoring.append("T_barriers")
    if len(previous_tailorings)>=2:
        barriers_past_two=previous_tailorings[-2:]
        barriers_past_two=list(map(lambda x: 0 if "T_barriers" not in x["_source"].keys() else 0 if x["_source"]["T_barriers"]!=7 else 1,barriers_past_two))
        if sum(barriers_past_two)==0:
            tailoring.remove("T_barriers")
    return tailoring


@router.get("/tailoring")
async def tailoring(
    current_user: Annotated[User, Depends(get_current_user)],
):
    baseline = es.get(index="questionnaire",id=current_user.userid)["_source"]["questionnaire"]
    # all_tailoring_questions=list(map(lambda x: x["_source"],res["hits"]["hits"]))
    previous_tailorings=es.search(index="tailoring_questionnaire", query={'match' : {"userid":current_user.userid}},size=9999)["hits"]["hits"]
    previous_tailorings.sort(key=lambda x: x["_source"]["date"],reverse=True)
    # print(previous_tailorings,"previous_tailorings")
    tailoring=filter_tailoring(previous_tailorings,baseline,current_user.userid)
    # print(tailoring,"ttailoring")
    # update_goal(current_user.userid,"QACompleted")
    tailoring=es.mget(index="tailoring_description", body={"ids": tailoring}).body["docs"]
    tailoring=list(map(lambda x: x["_source"],tailoring))
    # print(tailoring)
    return tailoring

@router.get("/summary")
async def tailoring(
    current_user: Annotated[User, Depends(get_current_user)],
):
    res = es.search(index="achievements", query={"bool":{"must":[{'match' : {"userid":"stuart"}}],
                                                   "must_not":[{'match' : {"achievedat":-1}}],
                                                  }
                                          }
                      ,size=10000)["hits"]["hits"]
    achievements=list(map(lambda x: x["_source"],res))
    # for i in 

    past_week=datetime.datetime.now()-datetime.timedelta(days=7)
    # list
    achievements=list(filter(lambda x: datetime.datetime.fromtimestamp(str(x["achievedate"]))>past_week,achievements))
    return achievements