from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel
from elasticsearch import Elasticsearch
from api.resources.constants import PORT,PASSWORD,USERNAME,STEP_GOAL_MIN,STEP_GOAL_MAX,HOST
from api.services.oauth import User,get_current_user
from elasticsearch import helpers
import json
from typing import Annotated
from typing import Optional
import zen
import datetime
import requests
import math
from functools import cmp_to_key
import random
from api.resources.custom_router import LoggingRoute
es = Elasticsearch(HOST+str(PORT),basic_auth=(USERNAME,PASSWORD),verify_certs=False)



router = APIRouter(prefix="/patient/plan",route_class=LoggingRoute,tags=["Plan"])

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

def calc_priority(items,questionnaire):
    updated_items=[]
    for item in items:
        item_copy=item.copy()
        if item_copy["name"] in questionnaire["thisweek"] and item_copy["name"] not in questionnaire["used"]:
            item_copy["priority"]=4
        elif item_copy["name"] not in questionnaire["thisweek"] and item_copy["name"] not in questionnaire["used"]:
            item_copy["priority"]=4
        elif item_copy["name"] in questionnaire["thisweek"] and item_copy["name"] in questionnaire["used"] and item_copy["name"] in questionnaire["canbequiz"]:
            item_copy["priority"]=3
        elif item_copy["name"] in questionnaire["thisweek"] and item_copy["name"] in questionnaire["used"] and item_copy["name"] not in questionnaire["canbequiz"]:
            item_copy["priority"]=2
        elif item_copy["name"] not in questionnaire["thisweek"] and item_copy["name"] in questionnaire["used"] and item_copy["name"] not in questionnaire["canbequiz"]:
            item_copy["priority"]=1
        updated_items.append(item_copy)
    return updated_items

def compare_saliency_priority(a,b):
    if a["priority"]==b["priority"]:
        return 1 if a["saliency"] >b["saliency"] else -1
    else:
         return 1 if a["priority"]>b["priority"] else -1

def rule_filter_education(questionnaire):
    questionnaire_updated=questionnaire.copy()
    questionnaire_updated["bt_pain_average_change"]=questionnaire_updated["bt_pain_average"]-questionnaire_updated["bt_pain_average_prev"]
    questionnaire_updated["t_cpg_function_change"]=questionnaire_updated["t_cpg_function"]-questionnaire_updated["t_cpg_function_prev"]
    remove_education=None
    add_educations=[]
    remove_educations=[]
    if questionnaire_updated["bt_pain_average"]>=7:
        remove_education=['Guideline_2', 'Guideline_3', 'Reassurance_8', 'Stay active_2', 'Stay active_3', 'Stay active_7', 'Stay active_12', 'Start exercise_1', 'Start exercise_2', 'Start exercise_3', 'Start exercise_4', 'Start exercise_5', 'Start exercise_6', 'Start exercise_7', 'Start exercise_8', 'Start exercise_9', 'Start exercise_10', 'Encouragement to SM_7', 'Encouragement to SM_8', 'Depression_1', 'Anxiety_1', 'Sleep disorders_1', 'MSK Pain_1', 'Pacing_1']
        add_education=['Cause of LBP_1', 'Cause of LBP_3', 'Cause of LBP_4', 'Cause of LBP_5', 'Imaging_1', 'Imaging_2', 'Pain rating_1', 'Reassurance_2', 'Reassurance_5', 'Accepting pain_1', 'Accepting pain_3', 'Distraction_1', 'Distraction_4', 'Distraction_5', 'Distress_1', 'FA Reassurance_2', 'FA Reassurance_3', 'FA Reassurance_4', 'FA Reassurance_5', 'FA Stay active_1', 'FA Stay active_2', 'FA Stay active_3', 'FA Stay active_4', 'FA Stay active_5', 'FA Stay active_6', 'FA Stay active_7', 'Problem solving_1', 'Problem solving_2', 'Problem solving_3', 'Problem solving_4', 'Relaxation_1', 'Relaxation_2', 'Relaxation_3', 'Relaxation_4', 'Relaxation_5']
        expire_week=1
        remove_educations.extend(remove_education)
        add_educations.extend(list(map(lambda x: {"name":x,"saliency":15},add_education)))
    if questionnaire_updated["bt_pain_average_change"]>=3:
        remove_education=['Guideline_2', 'Guideline_3', 'Reassurance_8', 'Stay active_2', 'Stay active_3', 'Stay active_7', 'Stay active_12', 'Start exercise_1', 'Start exercise_2', 'Start exercise_3', 'Start exercise_4', 'Start exercise_5', 'Start exercise_6', 'Start exercise_7', 'Start exercise_8', 'Start exercise_9', 'Start exercise_10', 'Encouragement to SM_7', 'Encouragement to SM_8', 'Depression_1', 'Anxiety_1', 'Sleep disorders_1', 'MSK Pain_1', 'Pacing_1']
        add_education=['Cause of LBP_1', 'Cause of LBP_3', 'Cause of LBP_4', 'Cause of LBP_5', 'Imaging_1', 'Imaging_2', 'Pain rating_1', 'Reassurance_2', 'Reassurance_5', 'Accepting pain_1', 'Accepting pain_3', 'Distraction_1', 'Distraction_4', 'Distraction_5', 'Distress_1', 'FA Reassurance_2', 'FA Reassurance_3', 'FA Reassurance_4', 'FA Reassurance_5', 'FA Stay active_1', 'FA Stay active_2', 'FA Stay active_3', 'FA Stay active_4', 'FA Stay active_5', 'FA Stay active_6', 'FA Stay active_7', 'Problem solving_1', 'Problem solving_2', 'Problem solving_3', 'Problem solving_4', 'Relaxation_1', 'Relaxation_2', 'Relaxation_3', 'Relaxation_4', 'Relaxation_5']
        expire_week=1
        remove_educations.extend(remove_education)
        add_educations.extend(list(map(lambda x: {"name":x,"saliency":15},add_education)))
    if questionnaire_updated["bt_pain_average"]>=3 and questionnaire_updated["bt_pain_average"]<=6:
        remove_education=['Sleep disorders_1', 'MSK pain_1']
        add_education=['Cause of LBP_1', 'Cause of LBP_3', 'Cause of LBP_4', 'Cause of LBP_5', 'Guideline LBP_1', 'Guideline LBP_2', 'Guideline LBP_3', 'Pain rating_1', 'Reassurance_4', 'Reassurance_6', 'Reassurance_7', 'Stay active_1', 'Stay active_5', 'Stay active_6', 'Stay active_9', 'Stay active_10', 'Stay active_13', 'Start exercise_3', 'Start exercise_4', 'Start exercise_6', 'Start exercise_8', 'Start exercise_9', 'Start exercise_10', 'Accepting pain_1', 'Accepting pain_2', 'Accepting pain_3', 'Distraction_3', 'Distraction_6', 'Thoughts_2', 'Thoughts_4', 'FA Reassurance_4', 'Daily activity_1', 'Daily activity_2', 'Daily activity_3', 'Daily activity_4', 'Daily activity_5', 'Me time_1', 'Me time_2', 'Problem solving_1', 'Problem solving_2', 'Problem solving_3', 'Problem solving_4', 'Relaxation_1', 'Relaxation_2', 'Relaxation_3', 'Relaxation_4', 'Relaxation_5']
        expire_week=1
        remove_educations.extend(remove_education)
        add_educations.extend(list(map(lambda x: {"name":x,"saliency":14},add_education)))
    if questionnaire_updated["t_cpg_function"]>=5:
        add_education=['Guideline LBP_3', 'Reassurance_9', 'Reassurance_10', 'Stay active_1', 'Stay active_7', 'Stay active_12', 'Start exercise_5', 'Start exercise_9', 'Start exercise_10', 'Encouragement to SM_1', 'Encouragement to SM_2', 'Encouragement to SM_5', 'Encouragement to SM_7', 'Encouragement to SM_8', 'Fear-avoidance_4', 'Daily activity_1', 'Daily activity_2', 'Daily activity_3', 'Daily activity_4', 'Daily activity_5', 'Me time_1', 'Me time_2', 'FA Stay active_2', 'Goal setting_1', 'Goal setting_2', 'Goal setting_3', 'Goal setting_4', 'Goal setting_5', 'Action planning_1', 'Action planning_2', 'Action planning_3', 'Pacing_1', 'Pacing_2', 'Pacing_3', 'Pacing_4', 'Pacing_5', 'Pacing_6', 'Problem solving_2', 'Problem solving_3', 'Problem solving_4']
        expire_week=2
        add_educations.extend(list(map(lambda x: {"name":x,"saliency":13},add_education)))
    if questionnaire_updated["t_cpg_function_change"]>=2:
        add_education=['Guideline LBP_3', 'Reassurance_9', 'Reassurance_10', 'Stay active_1', 'Stay active_7', 'Stay active_12', 'Start exercise_5', 'Start exercise_9', 'Start exercise_10', 'Encouragement to SM_1', 'Encouragement to SM_2', 'Encouragement to SM_5', 'Encouragement to SM_7', 'Encouragement to SM_8', 'Fear-avoidance_4', 'Daily activity_1', 'Daily activity_2', 'Daily activity_3', 'Daily activity_4', 'Daily activity_5', 'Me time_1', 'Me time_2', 'FA Stay active_2', 'Goal setting_1', 'Goal setting_2', 'Goal setting_3', 'Goal setting_4', 'Goal setting_5', 'Action planning_1', 'Action planning_2', 'Action planning_3', 'Pacing_1', 'Pacing_2', 'Pacing_3', 'Pacing_4', 'Pacing_5', 'Pacing_6', 'Problem solving_2', 'Problem solving_3', 'Problem solving_4']
        expire_week=2
        add_educations.extend(list(map(lambda x: {"name":x,"saliency":13},add_education)))
    if questionnaire_updated["t_tampa_fear"]>=5:
        remove_education=['Pacing_4', 'Pacing_6']
        add_education=['Reassurance_1', 'Reassurance_3', 'Reassurance_8', 'Stay active_3', 'Stay active_4', 'Stay active_5', 'Stay active_6', 'Stay active_7', 'Stay active_8', 'Stay active_11', 'Stay active_13', 'Start exercise_1', 'Start exercise_4', 'Start exercise_6', 'Start exercise_7', 'Start exercise_8', 'Start exercise_9', 'Start exercise_10', 'Structure of back_2', 'Structure of back_3', 'Mind-body connection_4', 'Mind-body connection_7', 'Encouragement to SM_2', 'Encouragement to SM_6', 'Encouragement to SM_7', 'Attitude_5', 'Attitude_6', 'Changing negative thoughts_1', 'Fear-avoidance_1', 'Fear-avoidance_2', 'Fear-avoidance_3', 'Fear-avoidance_4', 'Fear-avoidance_5', 'Fear-avoidance_6', 'Thoughts_5', 'Goal setting_2', 'Goal setting_3', 'Pacing_1', 'Pacing_2', 'Pacing_3', 'Pacing_5', 'Relaxation_3', 'Relaxation_4']
        expire_week=4
        remove_educations.extend(remove_education)
        add_educations.extend(list(map(lambda x: {"name":x,"saliency":12},add_education)))
    if questionnaire_updated["bt_wai"]>=3:
        add_education=['Work_1', 'Work_2', 'Work_3', 'Work_4', 'Work_5', 'Family and friends_3', 'Barrier family work_2']
        expire_week=8
        add_educations.extend(list(map(lambda x: {"name":x,"saliency":11},add_education)))
    if questionnaire_updated["t_sleep"] in ["Several times a week", "Sometimes"]:
        add_education=['Sleep disorders_1', 'Relaxation_1', 'Relaxation_2', 'Relaxation_4', 'Relaxation_5', 'Sleep_1', 'Sleep_2', 'Sleep_3', 'Sleep_4']
        expire_week=4
        add_educations.extend(list(map(lambda x: {"name":x,"saliency":10},add_education)))
    if questionnaire_updated["bt_pseq_2item"]<=8:
        add_education=['Reassurance_5', 'Reassurance_9', 'Stay active_1', 'Stay active_2', 'Stay active_3', 'Stay active_4', 'Stay active_5', 'Stay active_6', 'Stay active_7', 'Stay active_8', 'Stay active_9', 'Stay active_10', 'Stay active_11', 'Stay active_12', 'Stay active_13', 'Stay active_14', 'Start exercise_1', 'Start exercise_4', 'Start exercise_5', 'Start exercise_7', 'Start exercise_8', 'Start exercise_9', 'Start exercise_10', 'Mind-body connection_2', 'Mind-body connection_3', 'Mind-body connection_4', 'Mind-body connection_6', 'Mind-body connection_10', 'Encouragement to SM_1', 'Encouragement to SM_2', 'Encouragement to SM_4', 'Encouragement to SM_5', 'Encouragement to SM_6', 'Encouragement to SM_7', 'Encouragement to SM_8', 'Accepting pain_1', 'Accepting pain_2', 'Accepting pain_3', 'Attitude_1', 'Attitude_2', 'Attitude_3', 'Attitude_4', 'Attitude_5', 'Attitude_6', 'Changing negative thoughts_6', 'Changing negative thoughts_9', 'Thoughts_4', 'Me time_1', 'Me time_2', 'Goal setting_1', 'Goal setting_2', 'Goal setting_3', 'Goal setting_4', 'Goal setting_5', 'Action planning_1', 'Action planning_2', 'Action planning_3', 'Problem solving_2', 'Problem solving_3', 'Problem solving_4', 'Work_1', 'Work_4', 'Family and friends_1', 'Family and friends_2', 'Family and friends_3', 'Family and friends_4', 'Family and friends_5', 'Family and friends_6', 'Barrier support_1']
        expire_week=8
        add_educations.extend(list(map(lambda x: {"name":x,"saliency":9},add_education)))
    if questionnaire_updated["bt_pss"]>=6:
        add_education=['Reassurance_3', 'Reassurance_4', 'Reassurance_9', 'Stay active_7', 'Stay active_9', 'Stay active_10', 'Stay active_11', 'Stay active_13', 'Mind-body connection_1', 'Mind-body connection_3', 'Mind-body connection_5', 'Mind-body connection_6', 'Mind-body connection_7', 'Mind-body connection_9', 'Mind-body connection_10', 'Encouragement to SM_1', 'Encouragement to SM_2', 'Encouragement to SM_4', 'Encouragement to SM_5', 'Encouragement to SM_6', 'Encouragement to SM_7', 'Anxious_1', 'Anxious_2', 'Anxious_3', 'Attitude_1', 'Attitude_3', 'Attitude_4', 'Attitude_5', 'Attitude_6', 'Changing negative thoughts_1', 'Changing negative thoughts_2', 'Changing negative thoughts_3', 'Changing negative thoughts_4', 'Changing negative thoughts_5', 'Changing negative thoughts_6', 'Changing negative thoughts_7', 'Changing negative thoughts_9', 'Changing negative thoughts_10', 'Distraction_6', 'Stress_1', 'Stress_2', 'Stress_3', 'Thoughts_1', 'Thoughts_3', 'Thoughts_6', 'Thoughts_7', 'Me time_1', 'Me time_2', 'Goal setting_2', 'Goal setting_4', 'Goal setting_5', 'Action planning_1', 'Action planning_2', 'Action planning_3', 'Problem solving_2', 'Problem solving_3', 'Problem solving_4', 'Relaxation_2', 'Relaxation_5', 'Family and friends_1', 'Family and friends_2', 'Family and friends_3', 'Family and friends_4', 'Family and friends_5', 'Family and friends_6']
        expire_week=4
        add_educations.extend(list(map(lambda x: {"name":x,"saliency":8},add_education)))
    if questionnaire_updated["bt_phq_2item"]>=1:
        add_education=['Stay active_4', 'Stay active_10', 'Mind-body connection_3', 'Mind-body connection_5', 'Mind-body connection_6', 'Mind-body connection_7', 'Mind-body connection_9', 'Encouragement to SM_1', 'Encouragement to SM_2', 'Encouragement to SM_4', 'Encouragement to SM_5', 'Encouragement to SM_6', 'Encouragement to SM_7', 'Anxious_1', 'Anxious_2', 'Anxious_3', 'Attitude_3', 'Attitude_5', 'Changing negative thoughts_1', 'Changing negative thoughts_2', 'Changing negative thoughts_3', 'Changing negative thoughts_4', 'Changing negative thoughts_5', 'Changing negative thoughts_6', 'Changing negative thoughts_7', 'Changing negative thoughts_9', 'Changing negative thoughts_10', 'Distraction_1', 'Distraction_5', 'Distraction_6', 'Fear-avoidance_1', 'Thoughts_1', 'Thoughts_2', 'Thoughts_3', 'Depression_1', 'Anxiety_1', 'Problem solving_1', 'Problem solving_3', 'Relaxation_2', 'Relaxation_3', 'Relaxation_4', 'Relaxation_5', 'Family and friends_1', 'Family and friends_2', 'Family and friends_3', 'Family and friends_4', 'Family and friends_5', 'Family and friends_6']
        expire_week=1
        add_educations.extend(list(map(lambda x: {"name":x,"saliency":7},add_education)))
    if "lack_of_time" in questionnaire_updated["t_barriers"]:
        add_education=['Barrier time_1', 'Barrier time_2', 'Daily activity_1', 'Daily activity_2', 'Daily activity_3', 'Daily activity_4', 'Daily activity_5', 'Goal setting_3', 'Action planning_1']
        expire_week=1
        add_educations.extend(list(map(lambda x: {"name":x,"saliency":6},add_education)))
    if "too_tired" in questionnaire_updated["t_barriers"]:
        add_education=['Barrier tiredness_1', 'Barrier tiredness_2']
        expire_week=1
        add_educations.extend(list(map(lambda x: {"name":x,"saliency":5},add_education)))
    if "lack_of_support" in questionnaire_updated["t_barriers"]:
        add_education=['Barrier support_1', 'Barrier family work_1', 'Daily activity_3', 'Daily activity_4', 'Family and friends_1', 'Family and friends_2', 'Family and friends_3', 'Family and friends_4', 'Family and friends_5', 'Family and friends_6']
        expire_week=1
        add_educations.extend(list(map(lambda x: {"name":x,"saliency":4},add_education)))
    if "family_work" in questionnaire_updated["t_barriers"]:
        add_education=['Barrier family work_1', 'Barrier family work_2', 'Work_1', 'Work_2', 'Family and friends_1', 'Family and friends_3']
        expire_week=1
        add_educations.extend(list(map(lambda x: {"name":x,"saliency":3},add_education)))
    if "weather" in questionnaire_updated["t_barriers"]:
        add_education=['Barrier weather_1', 'Barrier weather_2']
        expire_week=1
        add_educations.extend(list(map(lambda x: {"name":x,"saliency":2},add_education)))
    if "facilities" in questionnaire_updated["t_barriers"]:
        add_education=['Barrier facilities_1', 'Barrier facilities_2', 'Barrier facilities_2']
        expire_week=1
        add_educations.extend(list(map(lambda x: {"name":x,"saliency":1},add_education)))

    groups={'Cause of LBP_1': 0, 'Cause of LBP_2': 0, 'Cause of LBP_3': 0, 'Cause of LBP_4': 0, 'Cause of LBP_5': 0, 'Cause of LBP_6': 0, 'Guideline LBP_1': 1, 'Guideline LBP_2': 1, 'Guideline LBP_3': 1, 'Imaging_1': 2, 'Imaging_2': 2, 'Pain rating_1': 3, 'Reassurance_1': 4, 'Reassurance_2': 4, 'Reassurance_3': 4, 'Reassurance_4': 4, 'Reassurance_5': 4, 'Reassurance_6': 4, 'Reassurance_7': 4, 'Reassurance_8': 4, 'Reassurance_9': 4, 'Reassurance_10': 4, 'Stay active_1': 5, 'Stay active_2': 5, 'Stay active_3': 5, 'Stay active_4': 5, 'Stay active_5': 5, 'Stay active_6': 5, 'Stay active_7': 5, 'Stay active_8': 5, 'Stay active_9': 5, 'Stay active_10': 5, 'Stay active_11': 5, 'Stay active_12': 5, 'Stay active_13': 5, 'Stay active_14': 5, 'Start exercise_1': 6, 'Start exercise_2': 6, 'Start exercise_3': 6, 'Start exercise_4': 6, 'Start exercise_5': 6, 'Start exercise_6': 6, 'Start exercise_7': 6, 'Start exercise_8': 6, 'Start exercise_9': 6, 'Start exercise_10': 6, 'Structure of back_1': 7, 'Structure of back_2': 7, 'Structure of back_3': 7, 'Structure of back_4': 7, 'Mind-body connection_1': 8, 'Mind-body connection_2': 8, 'Mind-body connection_3': 8, 'Mind-body connection_4': 8, 'Mind-body connection_5': 8, 'Mind-body connection_6': 8, 'Mind-body connection_7': 8, 'Mind-body connection_8': 8, 'Mind-body connection_9': 8, 'Mind-body connection_10': 8, 'Encouragement to SM_1': 9, 'Encouragement to SM_2': 9, 'Encouragement to SM_4': 9, 'Encouragement to SM_5': 9, 'Encouragement to SM_6': 9, 'Encouragement to SM_7': 9, 'Encouragement to SM_8': 9, 'Accepting pain_1': 10, 'Accepting pain_2': 10, 'Accepting pain_3': 10, 'Anxious_1': 11, 'Anxious_2': 11, 'Anxious_3': 11, 'Attitude_1': 12, 'Attitude_2': 12, 'Attitude_3': 12, 'Attitude_4': 12, 'Attitude_5': 12, 'Attitude_6': 12, 'Changing negative thoughts_1': 13, 'Changing negative thoughts_2': 13, 'Changing negative thoughts_3': 13, 'Changing negative thoughts_4': 13, 'Changing negative thoughts_5': 13, 'Changing negative thoughts_6': 13, 'Changing negative thoughts_7': 13, 'Changing negative thoughts_9': 13, 'Changing negative thoughts_10': 13, 'Distraction_1': 14, 'Distraction_2': 14, 'Distraction_3': 14, 'Distraction_4': 14, 'Distraction_5': 14, 'Distraction_6': 14, 'Distress_1': 15, 'Fear-avoidance_1': 16, 'Fear-avoidance_2': 16, 'Fear-avoidance_3': 16, 'Fear-avoidance_4': 16, 'Fear-avoidance_5': 16, 'Fear-avoidance_6': 16, 'Stress_1': 17, 'Stress_2': 17, 'Stress_3': 17, 'Thoughts_1': 18, 'Thoughts_2': 18, 'Thoughts_3': 18, 'Thoughts_4': 18, 'Thoughts_5': 18, 'Thoughts_6': 18, 'Thoughts_7': 18, 'Daily activity_1': 19, 'Daily activity_2': 19, 'Daily activity_3': 19, 'Daily activity_4': 19, 'Daily activity_5': 19, 'Me time_1': 20, 'Me time_2': 20, 'FA Reassurance_2': 21, 'FA Reassurance_3': 21, 'FA Reassurance_4': 21, 'FA Reassurance_5': 21, 'FA Stay active_1': 22, 'FA Stay active_2': 22, 'FA Stay active_3': 22, 'FA Stay active_4': 22, 'FA Stay active_5': 22, 'FA Stay active_6': 22, 'FA Stay active_7': 22, 'Depression_1': 23, 'Anxiety_1': 24, 'Sleep disorders_1': 25, 'MSK pain_1': 26, 'Goal setting_1': 27, 'Goal setting_2': 27, 'Goal setting_3': 27, 'Goal setting_4': 27, 'Goal setting_5': 27, 'Action planning_1': 28, 'Action planning_2': 28, 'Action planning_3': 28, 'Pacing_1': 29, 'Pacing_2': 29, 'Pacing_3': 29, 'Pacing_4': 29, 'Pacing_5': 29, 'Pacing_6': 29, 'Problem solving_1': 30, 'Problem solving_2': 30, 'Problem solving_3': 30, 'Problem solving_4': 30, 'Relaxation_1': 31, 'Relaxation_2': 31, 'Relaxation_3': 31, 'Relaxation_4': 31, 'Relaxation_5': 31, 'Sleep_1': 32, 'Sleep_2': 32, 'Sleep_3': 32, 'Sleep_4': 32, 'Work_1': 33, 'Work_2': 33, 'Work_3': 33, 'Work_4': 33, 'Work_5': 33, 'Family and friends_1': 34, 'Family and friends_2': 34, 'Family and friends_3': 34, 'Family and friends_4': 34, 'Family and friends_5': 34, 'Family and friends_6': 34, 'Barrier time_1': 35, 'Barrier time_2': 35, 'Barrier tiredness_1': 36, 'Barrier tiredness_2': 36, 'Barrier support_1': 37, 'Barrier family work_1': 38, 'Barrier family work_2': 38, 'Barrier weather_1': 39, 'Barrier weather_2': 39, 'Barrier facilities_1': 40, 'Barrier facilities_2': 40, 'Barrier facilities_3': 40}
    items=list(filter(lambda x: x not in remove_educations,add_educations))
    items=list(map(lambda x: {"name":x["name"],"group":groups[x["name"]],"saliency":x["saliency"]} ,items))
    items=calc_priority(items,questionnaire)

    items.sort(key=cmp_to_key(compare_saliency_priority),reverse=True)
    items=list(map(lambda x: x["name"],items))
    return list(dict.fromkeys(items)) #removes duplicates and maintains order
def generate_plan_education(current_user,base_questionnaire,update_questionnaire):
    if not es.indices.exists(index="education_queue"):
        es.indices.create(index = 'education_queue')

    res=es.search(index="education_queue", body={"query":{'match' : {"userid":current_user.userid}}},size=1)["hits"]["hits"]
    if res==[]:
        priority_queue=[]
    else:
        priority_queue=res[0]["_source"]["educational_items"].copy()
    # cbr_education_items=["Changing negative thoughts_7","Changing negative thoughts_6"]
    response=requests.post("http://localhost:8080/concepts/Case/casebases/sbcases/amalgamationFunctions/SMP_Education/retrievalByMultipleAttributes",
                      json=base_questionnaire,
                      params={"k":-1}
    )
    # print("test, is it returning",response.json())
    cbr_education_items=set("".join(list(map(lambda x: x["SelfManagement_Education"],response.json()))).split(";"))
    #increase priority of items fetched from cbr system
    priority_queue=add_items_priority_queue(priority_queue,cbr_education_items)
    #increase priority of items fetched from rule system
    if update_questionnaire:
        rule_education_items=rule_filter_education(update_questionnaire)
        priority_queue=add_items_priority_queue(priority_queue,rule_education_items)
    #TODO: missing canbequiz argument
    result=decision_grouping.evaluate({"priority_queue":priority_queue})["result"]
    result.sort(key=lambda x: x["priority"],reverse=True)

    #if there are not enough items in plan add generic items
    if len(result)<7:
        groups=set(map(lambda x: x["group"] if "group" in x.keys() else None,result))
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
    result=list(map(lambda x: x|{"educationid":x["id"]},result))
    #TODO: store updated priority queue in elasticsearch   
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
            print(ex_type)
            print(exercise_set[0])
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
    # temp_quest={
    #     "bt_pain_average":5,
    #     "bt_pain_average_prev":3,
    #     "duration":35,
    #     "condition":"LBP",
    #     }
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
    print(exercises,"post ab back")
    #add exercises of types that are not already in exercises list
    exercises.extend(add_other_types(cbr_exercise_items,number_exercises-len(exercises),exercises))
    if len(exercises)==number_exercises:
        return exercises
    print(exercises,"other types cbr")
    #same as above but for exercises from elasticsearch
    exercises.extend(add_other_types(es_exercise_items,number_exercises-len(exercises),exercises))
    if len(exercises)==number_exercises:
        return exercises
    print(exercises,"other types es")
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

@router.post("/next")
async def next(
    current_user: Annotated[User, Depends(get_current_user)],
    plan_info: Plan_info
):
    if not es.indices.exists(index="plan"):
        es.indices.create(index = 'plan')
    #TODO: check if current plan has expired before creating a new plan, if not error

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
                    "created":curr_dt.timestamp(),
                    "start":int(datetime.datetime.combine(curr_dt, datetime.time.min).timestamp()),
                    "end":int(datetime.datetime.combine(curr_dt+datetime.timedelta(days=7), datetime.time.max).timestamp()),
                    "exercises_duration":plan_info.exercises_duration,
                    "history":history,
                    "plan":{
                        "date":curr_dt.timestamp(),
                        "educations":generate_plan_education(current_user,base_questionnaire,plan_info.questionnaire),
                        "exercises":exercises,
                        "activity":generate_activity_goal(current_user)
                    },
                    "done":{"steps":0} #TODO: what is this supposed to be? Woulfnt it just be 0?
                   }
    
    #TODO: need to check if plan is valid first
    es.index(index='plan', body=json.dumps(complete_plan))


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
    return {"status":"Success"}

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
    
    return {"status":"Success"}



@router.get("/latest")
async def latest(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if not es.indices.exists(index="plan"):
        es.indices.create(index = 'plan')
    print("kashleem")
    res=es.search(index="plan", query={'match' : {"userid":current_user.userid}},size=1)["hits"]["hits"]
    if res==[]:
        return [] 
    return res[0]["_source"]



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
    return True
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




@router.get("/exercise/completed")
async def exercise_completed_get(
    current_user: Annotated[User, Depends(get_current_user)],
    date:int
):
    exercises=es.search(index="exercise", query={
        "bool": {
      "filter": [
        {
          "range": {
            "date":{
              "gte":date
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
    date:int
):
    education_items=es.search(index="education", query={
        "bool": {
      "filter": [
        {
          "range": {
            "date":{
              "gte":date
            }
          }
        },
      ]
    }},size=100)["hits"]["hits"]
    if education_items!=[]:
        return list(map(lambda x: x["_source"],education_items))
    return education_items 
    

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
    print(list(filter(lambda x: ("skipped" in x.keys()) and (x["Type"]==exercise_type),exercises_from_plan )))
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