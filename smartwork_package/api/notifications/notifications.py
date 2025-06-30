import asyncio
from fastapi import FastAPI
from api.resources.constants import ES_PASSWORD,ES_URL,MYCBR_URL,PHQ_ANSWER_MAP
# from api.services.patient import activity_done
from api.resources.helper_functions import get_between
from elasticsearch import Elasticsearch
import time
import datetime
import firebase_admin
from firebase_admin import credentials, messaging
import json
import random
def main_loop():
    es= Elasticsearch(ES_URL, basic_auth=("elastic", ES_PASSWORD), verify_certs=False)
    # users=["stuart4"]
    users=es.search(index="account", query={"match_all": {}}, size=1000)["hits"]["hits"]
    users=list(map(lambda x: x["_id"], users))

    # user_appsettings= es.search(index='appsettings', query={"match": {"_id":"stuart4"}})
    # user_appsettings = user_appsettings['hits']['hits']
    # user_appsettings = [doc['_source'] for doc in user_appsettings]
    print("Checking for notifications")
    while True:
        for user in users:
            plan = es.search(
                index='plan',
                query={"match": {"userid": user}},
                sort=[{"created": {"order": "desc"}}],
                size=1
            )
            plan = plan['hits']['hits'][0]['_source'] if plan['hits']['hits'] else None
            app_settings = es.get(index='appsettings', id=user)['_source'] if es.exists(index='appsettings', id=user) else None
            if app_settings is None:
                # print(f"No app settings found for user {user}. Skipping notification.")
                continue
            token=app_settings["pushToken"]
            if not token:
                # print(f"No token found for user. Skipping notification.")
                continue
            # progress_notification(app_settings, plan,es)
            
            low_activity_notification(app_settings, plan, es, user)
            decide_exercise_notification_type(app_settings, plan, es, user)
            app_not_opened_notification(app_settings,plan, es,user)
            education_reminder(app_settings, plan, es, user)
        time.sleep(60) 
    # for user in user_appsettings:
    
def get_achievement_level(score):
    if score < 0.5:
        return "Low"
    elif 0.5 <= score < 0.75:
        return "Medium"
    elif 0.75 <= score < 1.0:
        return "High"
    else:
        return "Full"
def fetch_text(notification_type,score):
    with open("./api/notifications/notification_texts.json", "r") as f:
        texts = json.load(f)
    
    if notification_type == "progress_notification":
        level= get_achievement_level(score)
        text=random.choice(list(texts["PhysicalActivity"][level].items()))[1]
        title=texts["Titles"]["StepsUpdate"]
    elif notification_type == "app_not_opened":
        text=random.choice(list(texts["App"]["OpenApp"].items()))[1]
        title=texts["Titles"]["OpenApp"]
    elif notification_type == "exercise_reminder_pain":
        text=random.choice(list(texts["Exercise"]["PainAndFunction"].items()))[1]
        title=texts["Titles"]["ExerciseReminder"]
    elif notification_type == "exercise_reminder":
        text=random.choice(list(texts["Exercise"]["ZeroDays"].items()))[1]
        title=texts["Titles"]["ExerciseReminder"]
    elif notification_type == "education_reminder":
        text=random.choice(list(texts["Education"]["EducationReminder"].items()))[1]
        title=texts["Titles"]["Education"]
    elif notification_type == "completed_exercises":
        text=random.choice(list(texts["Exercise"]["SufficientDays"].items()))[1]
        title=texts["Titles"]["ExerciseUpdate"]
    elif notification_type == "not_completed_exercise":
        text=random.choice(list(texts["Exercise"]["IncompleteDay"].items()))[1]
        title=texts["Titles"]["ExerciseUpdate"]
    elif notification_type == "new_plan":
        text=random.choice(list(texts["Plan"]["NewPlan"].items()))[1]
        title=texts["Titles"]["NewPlan"]
    elif notification_type == "tailoring_reminder":
        text=random.choice(list(texts["Plan"]["NewPlanReminder"].items()))[1]
        title=texts["Titles"]["NewPlanReminder"]
    elif notification_type == "exercise_reminder_emotional_wellbeing":
        text=random.choice(list(texts["PhysicalActivity"]["EmotionalWellbeing"].items()))[1]
        title=texts["Titles"]["LowActivity"]
    elif notification_type == "exercise_reminder_barriers":
        barrier_type = random.choice(list(texts["PhysicalActivity"]["Barriers"].keys()))
        text=random.choice(list(texts["PhysicalActivity"]["Barriers"][barrier_type].items()))[1]
        title=texts["Titles"]["LowActivity"]
    elif notification_type == "exercise_reminder_pain":
        text=random.choice(list(texts["PhysicalActivity"]["PainAndFunction"].items()))[1]
        title=texts["Titles"]["LowActivity"]
    elif notification_type == "exercise_reminder":
        text=random.choice(list(texts["PhysicalActivity"]["Low"].items()))[1]
        title=texts["Titles"]["LowActivity"]
    return title,text
        

    # raise
def send_notification(notification_type, user_id, token, es, score=None):
    # Initialize the Firebase app (only do this once in your notebook)
    title,text= fetch_text(notification_type,score)
    if not firebase_admin._apps:
        cred = credentials.Certificate("./api/resources/serviceAccountKey.json")  # Replace with your service account key path
        firebase_admin.initialize_app(cred)
    # Create the message
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=text,
            ),
            token=token,
        ) 
        # Send the message
        response = messaging.send(message)
    except:
        print("Error sending notification to user:", user_id,"probably caused by expired token")
    print('Successfully sent message to :', user_id)

    # Ensure the notifications index exists
    if not es.indices.exists(index="notifications"):
        es.indices.create(index="notifications")

    # Add notification record
    doc = {
        "user_id": user_id,
        "notification_type": notification_type,
        "date": datetime.datetime.now().timestamp(),
        "score": score
    }
    es.index(index="notifications", document=doc)


def get_last_notification(es, user_id,notification_type=None):
    if not es.indices.exists(index="notifications"):
        es.indices.create(index="notifications")
    try:
        if notification_type:
            must=[
                                        {"match": {"user_id": user_id}},
                                        {"match": {"notification_type": notification_type} }
                                    ]
        else:
            must=[
                                        {"match": {"user_id": user_id}},
                                    ]
        previous_notification=es.search(
                        index="notifications",
                        query={
                            "bool": {
                                "must": must
                            }
                        },
                        sort=[{"date": {"order": "desc"}}],
                        size=1
                    )["hits"]["hits"]
        previous_notification = previous_notification[0]["_source"] if previous_notification else None
    except:
        previous_notification = None
    return previous_notification


#Sends a progress notification appropriate for the level of physical activity goal the user has achieved
def progress_notification(app_settings,plan,es):
    print("Progress notification called")
    if plan["end"]<datetime.datetime.now().timestamp():
        return
    else:
        activities=get_between(es,"activity",plan["start"],plan["end"],plan["userid"])
        done=sum(list(map(lambda x: x["_source"]["steps"],activities)))
        # ( plan["start"], plan["end"],plan["userid"])
        goal=plan["plan"]["activity"]["goal"]
        # print(done, goal)
        if goal>0:
            score= done / goal
            print(score)
            if score > 0.5:
                previous_notification = get_last_notification(es, plan["userid"])
                if previous_notification is None:
                    last_date=0
                    last_score = 0
                else:
                    last_score = previous_notification["score"]
                    last_date=datetime.datetime.fromtimestamp(previous_notification["date"]).date()
                    
                send_notification("progress_notification", plan["userid"], app_settings["pushToken"],es,score)
                if score >= 1:
                    if last_score < 1:
                        # send notification for achieving goal
                        send_notification("progress_notification", plan["userid"], app_settings["pushToken"],es,score)
                    elif last_date != datetime.datetime.now().date():
                        send_notification("progress_notification", plan["userid"], app_settings["pushToken"],es,score)
                elif last_date != datetime.datetime.now().date():
                    send_notification("progress_notification", plan["userid"], app_settings["pushToken"],es,score)
                
# Sends a notification to a user if the app has not been opened over a time interval.
#     This function checks the last opened timestamp and compares it with the current time.
def app_not_opened_notification(app_settings,plan, es,user_id):
    # send_notification("app_not_opened", user_id, app_settings["pushToken"], es)
    if plan is None or not app_settings["notifications"]["all"]:
        return
    
    # activity is updated every time app is opened, so we can use the activity index to check the last opened time
    activity = es.search(
        index="activity",
        query={"match": {"userid": user_id}},
        sort=[{"date": {"order": "desc"}}],
        size=1
    )
    # print(activity)
    # raise
    latest_activity = activity["hits"]["hits"][0]["_source"] if activity["hits"]["hits"] else None
    if latest_activity is None:
        return
    last_opened= datetime.datetime.fromtimestamp(latest_activity["date"])
    current_time = datetime.datetime.now()
    plan_received= datetime.datetime.fromtimestamp(plan["created"])
    
    previous_notification_not_opened = get_last_notification(es, user_id,"app_not_opened")
    previous_notification_not_opened_time = datetime.datetime.fromtimestamp(previous_notification_not_opened["date"]) if previous_notification_not_opened else None
    if previous_notification_not_opened is None:
        return
    #if the app has not been opened for more than 36 hours and the plan was received more than 36 hours ago
    if (current_time - last_opened).total_seconds() > 36 * 3600 and (current_time - plan_received).total_seconds() > 36 * 3600:
        #previous notification is more than 24 hours ago and the app was opened in the last 7 days
        if  (current_time - previous_notification_not_opened_time).total_seconds() > 24 * 3600 and (current_time - last_opened).total_seconds() < 7 * 24 * 3600:
            previous_notification = get_last_notification(es, user_id)
            previous_notification_time= datetime.datetime.fromtimestamp(previous_notification["date"]) if previous_notification else None
            # if no previous notification or the last notification was sent more than 1 hour ago
            if not previous_notification or (current_time - previous_notification_time).total_seconds() >  3600:
                send_notification("app_not_opened", user_id, app_settings["pushToken"], es)


def get_level_difference(es,user_id,field):
    tailoring = es.search(
        index="tailoring",
        query={
            "bool": {
                "must": [
                    {"match": {"userid": user_id}},
                ]
            }
        },
        sort=[{"date": {"order": "desc"}}],
        size=9999
    )["hits"]["hits"]
    #keep only tailoring documents that have the field in the questionnaire
    # print(tailoring)
    # print(tailoring,"tailoring")
    tailoring_rel_field=[]
    for t in tailoring:
        for question in t["_source"]["questionnaire"]:
            if question["questionid"] == field:
                if "phq" in field:
                    answer = question["answer"]
                    answer=PHQ_ANSWER_MAP[answer]
                    tailoring_rel_field.append(answer)
                else:
                    tailoring_rel_field.append(question["answer"])
                break
    if len(tailoring_rel_field) < 2:
        return 0
    # print(tailoring_rel_field,"relevnat",field)
    recent = tailoring_rel_field[0]
    previous = tailoring_rel_field[1]
    return int(recent) - int(previous)


#Sends a notification to a user if no exercise data update is received over a time interval
def exercise_reminder(app_settings,plan, es,user_id):
    if app_settings["notifications"]["all"] and app_settings["notifications"]["exercise"]:
        if plan is None:
            return
        last_exercise_reminder = get_last_notification(es, user_id, "exercise_reminder")
        last_exercise_reminder_time = datetime.datetime.fromtimestamp(last_exercise_reminder["date"]) if last_exercise_reminder else None
        # Check if the last exercise reminder was sent more than 3 days ago
        if last_exercise_reminder_time is None or (datetime.datetime.now() - last_exercise_reminder_time).total_seconds() > 3*24 * 3600:
            last_notification= get_last_notification(es, user_id)
            last_notification_time = datetime.datetime.fromtimestamp(last_notification["date"]) if last_notification else None
            # If no previous notification or the last notification was sent more than 1 hour ago
            if not last_notification or (datetime.datetime.now() - last_notification_time).total_seconds() > 3600:
                painlevel=get_level_difference(es, user_id, "BT_pain_average")
                functionlevel=get_level_difference(es, user_id, "T_cpg_function")
                if painlevel >=2 or functionlevel <=-2:
                    send_notification("exercise_reminder_pain", user_id, app_settings["pushToken"], es)
                else:
                    send_notification("exercise_reminder", user_id, app_settings["pushToken"], es)
                    
           


# Sends a notification to a user if they do not complete their education materials over a time interval.
# This function checks the last completed timestamp and compares it with the current time.
def education_reminder(app_settings, plan, es, user_id):
    """
    
    """
    if app_settings["notifications"]["all"] and app_settings["notifications"]["education"]:
        if plan is None:
            return
        # Check if the user has completed their education materials
        education = es.search(
            index="education",
            query={"match": {"userid": user_id}},
            sort=[{"date": {"order": "desc"}}],
            size=1
        )
        latest_education = education["hits"]["hits"][0]["_source"] if education["hits"]["hits"] else None
        if latest_education is None:
            return

        current_time = datetime.datetime.now()
        
        previous_notification_education = get_last_notification(es, user_id, "education_reminder")
        previous_notification_education_time = datetime.datetime.fromtimestamp(previous_notification_education["date"]) if previous_notification_education else None
        previous_notification=get_last_notification(es, user_id)
        previous_notification_time = datetime.datetime.fromtimestamp(previous_notification["date"]) if previous_notification else None
        # print(previous_notification,"slooo")
        # If the last education notification was 3 days ago and no notification has been sent in the last hour
        if (previous_notification is None or (current_time - previous_notification_education_time).total_seconds() > 3 * 24 * 3600) and (previous_notification is None or (current_time - previous_notification_time).total_seconds() >  3600):
            send_notification("education_reminder", user_id, app_settings["pushToken"], es)



# Sends a notification to a user if they achieve the recommended days of exercise.
# This function checks the number of completed exercises and compares it with the recommended days.
def sufficient_days_exercise(app_settings, plan, es, user_id):
    # send_notification("completed_exercises", user_id, app_settings["pushToken"], es)
    if app_settings["notifications"]["all"] and app_settings["notifications"]["exercise"]:
        if plan is None:
            return
        previous_notification_completed = get_last_notification(es, user_id, "completed_exercises")
        # print(previous_notification_completed,"sssss")
        previous_notification_completed_time = datetime.datetime.fromtimestamp(previous_notification_completed["date"]) if previous_notification_completed else None
        plan_created_time = datetime.datetime.fromtimestamp(plan["created"])
        # print((previous_notification_completed is None),(plan_created_time> previous_notification_completed_time))
        if (previous_notification_completed is None) or (plan_created_time> previous_notification_completed_time):
            previous_notification= get_last_notification(es, user_id)
            # print(previous_notification)
            previous_notification_time = datetime.datetime.fromtimestamp(previous_notification["date"]) if previous_notification else None
            # If no previous notification or the last notification was sent more than 1 hour ago
            if not previous_notification or (datetime.datetime.now() - previous_notification_time).total_seconds() > 3600:
                send_notification("completed_exercises", user_id, app_settings["pushToken"], es)


#Sends a notification to a user if the user does not complete an exercise session for the day
def not_completed_exercise(app_settings, plan, es, user_id):

    if app_settings["notifications"]["all"] and app_settings["notifications"]["exercise"]:
        if plan is None:
            return
        exercise = es.search(
            index="exercise",
            query={"match": {"userid": user_id}},
            sort=[{"date": {"order": "desc"}}],
            size=1
        )
        # send_notification("not_completed_exercise", user_id, app_settings["pushToken"], es)
        last_no_exercise_reminder = get_last_notification(es, user_id, "not_completed_exercise")
        last_no_exercise_reminder_time = datetime.datetime.fromtimestamp(last_no_exercise_reminder["date"]) if last_no_exercise_reminder else None
        # Check if the last no exercise reminder was sent in last 23 hours
        if last_no_exercise_reminder_time is None or (datetime.datetime.now() - last_no_exercise_reminder_time).total_seconds() > 23 * 3600:
            latest_exercise = exercise["hits"]["hits"][0]["_source"] if exercise["hits"]["hits"] else None
            last_exercise_time= datetime.datetime.fromtimestamp(latest_exercise["date"]) if latest_exercise else None
            if latest_exercise is None or (datetime.datetime.now() - last_exercise_time).total_seconds() > 3 * 3600:
                latest_notification = get_last_notification(es, user_id)
                latest_notification_time = datetime.datetime.fromtimestamp(latest_notification["date"]) if latest_notification else None
                if latest_notification is None or (datetime.datetime.now() - latest_notification_time).total_seconds() > 3600:
                    send_notification("not_completed_exercise", user_id, app_settings["pushToken"], es)
                    # print("Sent not completed exercise notification to user:", user_id)

# Sends a notification to a user if their current plan expires to encourage them to start weekly tailoring session in order to receive a new plan.
# Also sends follow up reminders if the user ignores the first notification.
def tailoring_reminder(app_settings, plan, es, user_id):
    """
    
    """
    if app_settings["notifications"]["all"]:
        if plan is None:
            return
        plan_end_time = datetime.datetime.fromtimestamp(plan["end"])
        current_time = datetime.datetime.now()
        end_time=plan_end_time + datetime.timedelta(days=7)
        if (current_time> plan_end_time) & (current_time < end_time):
            previous_notification = get_last_notification(es, user_id, "tailoring_reminder")
            previous_notification_time = datetime.datetime.fromtimestamp(previous_notification["date"]) if previous_notification else None
            if previous_notification_time<plan_end_time:
                    send_notification("new_plan", user_id, app_settings["pushToken"], es)
            elif previous_notification is None or (current_time - previous_notification_time).total_seconds() > 10* 3600:
                    send_notification("tailoring_reminder", user_id, app_settings["pushToken"], es)




def get_barriers(es, user_id):
    tailoring=es.search(
                index="tailoring",
                query={"match": {"userid": user_id}},
                sort=[{"date": {"order": "desc"}}],
                size=1
            )["hits"]["hits"]
    if len(tailoring) == 0:
        return []
    tailoring=tailoring[0]["_source"]["questionnaire"]
    for question in tailoring:
        if question["questionid"] == "T_barriers":
            barriers = question["answer"]
            break
    else:
        barriers = []
    return barriers
    
#Sends a notification to a user they have low activity achievement for over 3 days
def low_activity_notification(app_settings, plan, es, user_id):
  if app_settings["notifications"]["all"] and app_settings["notifications"]["activity"]:
    if plan is None:
        return
    plan_created_time = datetime.datetime.fromtimestamp(plan["created"])
    # print(plan)
    goal= plan["plan"]["activity"]["goal"]

    # send_notification("exercise_reminder", user_id, app_settings["pushToken"], es, score=0)
    if (datetime.datetime.now() - plan_created_time).total_seconds() > 3 * 24 * 3600:
        # Plan is older than 3 days
        for days_ago in range(1, 4):
            day = datetime.datetime.now() - datetime.timedelta(days=days_ago)
            start_of_day = datetime.datetime.combine(day.date(), datetime.time.min).timestamp()
            end_of_day = datetime.datetime.combine(day.date(), datetime.time.max).timestamp()
            activities=get_between(es,"activity",start_of_day,end_of_day,user_id)
            activity= sum(list(map(lambda x: x["_source"]["steps"], activities)))

            if activity>goal*0.5:
                # User has achieved more than 50% of their goal in the last 3 days
                return
        previous_notification = get_last_notification(es, user_id)
        previous_notification_time = datetime.datetime.fromtimestamp(previous_notification["date"]) if previous_notification else None
        if not previous_notification or (datetime.datetime.now() - previous_notification_time).total_seconds() > 3600:
            phq1diff= get_level_difference(es, user_id, "BT_phq_1")
            phq2diff= get_level_difference(es, user_id, "BT_phq_2")
            barriers=get_barriers(es, user_id)
            paindiff= get_level_difference(es, user_id, "BT_pain_average")
            functiondiff= get_level_difference(es, user_id, "T_cpg_function")
            if (phq1diff >= 1) or (phq2diff >= 1):
                #emotional wellbeing message
                send_notification("exercise_reminder_emotional_wellbeing", user_id, app_settings["pushToken"], es, score=0)
            elif len(barriers) > 0:
                send_notification("exercise_reminder_barriers", user_id, app_settings["pushToken"], es, score=0)
            elif (paindiff >= 2) or (functiondiff <= -2):
                #pain and function message
                send_notification("exercise_reminder_pain", user_id, app_settings["pushToken"], es, score=0)
            else:
                #low activity message
                send_notification("exercise_reminder", user_id, app_settings["pushToken"], es, score=0)
                


def num_days_exercised(es, user_id, start, end):
    """
    Returns the number of days the user has exercised between start and end timestamps.
    """
    exercise = es.search(
        index="exercise",
        query={
            "bool": {
                "must": [
                    {"match": {"userid": user_id}},
                    {"range": {"date": {"gte": start, "lte": end}}}
                ]
            }
        },
        size=10000
    )
    days_exercised = set()
    for hit in exercise["hits"]["hits"]:
        date = datetime.datetime.fromtimestamp(hit["_source"]["date"]).date()
        days_exercised.add(date)
    return len(days_exercised)

###         
# * A helper method that decides which type of exercise notification to send based on the user's current exercise
#      * data. Exercise notifications are mutually exclusive and only one type of notification should need to be sent
#      * given a user's current exercise status at any point in time
def decide_exercise_notification_type(app_settings, plan, es, user_id):
    if plan is None:
        return
    # Check if the user has completed their exercise for the day
    plan_start= plan["start"]
    plan_end= plan["end"]
    days_exercised= num_days_exercised(es, user_id, plan_start, plan_end)
    # if days_exercised >= 3:
    #     sufficient_days_exercise(app_settings, plan, es, user_id)
    # else:
        #Check if user has done some but not all exercises today
    today_start = datetime.datetime.combine(datetime.date.today(), datetime.time.min).timestamp()
    today_end = datetime.datetime.combine(datetime.date.today(), datetime.time.max).timestamp()
    exercises_done=len(get_between(es,"exercise",today_start,today_end,user_id))
    exercises_in_plan=len(plan["plan"]["exercises"])
    if days_exercised>=3:
        # User has done enough exercises in the last 3 days
        sufficient_days_exercise(app_settings, plan, es, user_id)
    else:
        if (exercises_done > 0) and (exercises_done < exercises_in_plan):
            # User has done some but not all exercises today
            not_completed_exercise(app_settings, plan, es, user_id)
        else:
            last_exercise_reminder = get_last_notification(es, user_id, "exercise_reminder")
            if not last_exercise_reminder:
                ref_start_time=plan_start
            else:
                ref_start_time=last_exercise_reminder["date"]
            if (datetime.datetime.now().timestamp() - ref_start_time) > 3*24 * 3600:
                if days_exercised <1:
                    exercise_reminder(app_settings, plan, es, user_id)