from elasticsearch import Elasticsearch, helpers
from datetime import datetime,time,timedelta
import pandas as pd
from api.resources.constants import ES_PASSWORD,ES_URL
from api.resources.helper_functions import get_between
es = Elasticsearch(ES_URL,basic_auth=("elastic",ES_PASSWORD),verify_certs=False)



def update_goal(userid,goalid,progress=1,achievedat=1):
    #possible goal ids
    #SetGoalSetting,SetSleepTool,UseMindfulness,QACompleted,SessionCompleted
    id=userid+"_"+goalid
    res = es.get(index="achievements",  
          id=id)
    res=res["_source"]
    res["progress"]=progress
    res["achievedat"]=achievedat#
    if achievedat:
      res["achievedate"]=datetime.now().timestamp()
    es.update(index='achievements',id=id,
                doc=res)



def complete_quiz(userid):
    correct=es.search(index="education",query={"bool":
                                          {"must":[
                                              {"match":{"is_correct":True}},
                                                {"match":{"userid":userid}}
                                          ]
                                         
                                          }}
    ,size=900).body["hits"]["hits"]
    print(correct)
    num_correct=len(correct)
    update_goal(userid,"EducationalQuizAnswers",num_correct,float(num_correct>=1))
    for i in [1,2,7,14,25]:
        completed=-1
        if num_correct>=i:
          completed=1
        update_goal(userid,"EducationalCorrectQuiz"+str(i),num_correct,completed)


def complete_educational_read(userid):
    read=es.search(index="education",query={"match":{"userid":userid}},size=900).body["hits"]["hits"]
    num_read=len(read)
    update_goal(userid,"EducationalRead",num_read,float(num_read>=1))
    for i in [1,3,7,14,25,40,60,80,100]:
        completed=-1
        if num_read>=i:
          completed=1
        update_goal(userid,"EducationalMaterialRead"+str(i),num_read,completed)

def complete_exercise_day(userid):
    plans=es.search(index="plan",query={"match":{"userid":userid}},size=900).body["hits"]["hits"]
    days_completed=0
    for plan in plans:
      start_plan=datetime.fromtimestamp(plan["_source"]["start"])
      end_plan=datetime.fromtimestamp(plan["_source"]["end"])
      num_exercises_plan=len(plan["_source"]["plan"]["exercises"])
      for day in pd.date_range(start_plan,end_plan):
        start_day=day.replace(hour=0,minute=0,second=0,microsecond=0).timestamp()
        end_day=day.replace(hour=23,minute=59,second=59,microsecond=999999).timestamp()
        exercises_done=get_between(es,"exercise",start_day,end_day,userid)
        if len(exercises_done)>=num_exercises_plan:
          days_completed+=1
    update_goal(userid,"ExercisesCompleted",days_completed,float(days_completed>=1))
    for i in [1,3,7,14,25,40,60,80,100]:
        completed=-1
        if days_completed>=i:
          completed=1
        update_goal(userid,"ExerciseDaysCompleted"+str(i),days_completed,completed)


def total_steps(userid):
    res = es.search(index="activity", query={'match' : {"userid":userid}},size=10000)["hits"]["hits"]
    steps=list(map(lambda x: x["_source"]["steps"],res))
    total_steps=sum(steps)
    for i in [42.195,50,100,200,400,600,800,1000]:
        complete=-1
        if total_steps>=i*1000:
            complete=1
        if i == 42.195:
            update_goal(userid,"Marathon",total_steps,complete)
        else:
            update_goal(userid,"TotalSteps"+str(i),total_steps,complete)


def daily_steps(userid):
    current_goal = es.search(index="plan", query={'match' : {"userid":userid}},sort=[
    {
      "start": {
        "order": "desc"
      }
    }],size=10000)["hits"]["hits"][0]["_source"]["plan"]["activity"]["goal"]
    steps = es.search(index="activity", query={"bool":{"must":[
                                                  {'match' : {"userid":userid}},
                                                  {'range' : {"start":{"gte":datetime.combine(datetime.now(), time.min).timestamp()*1000}}},
                                                  {'range' : {"start":{"lte":datetime.combine(datetime.now(), time.max).timestamp()*1000}}},
                                                    ]
                                                  }
                                          }
                      ,size=10000)["hits"]["hits"]
    steps=list(map(lambda x: x["_source"]["steps"],steps))
    #checks if goal that is currently active is reached
    first_ach=es.get(index="achievements", id=userid+"_"+"DailyGoalSteps1")["_source"]
    last_updated= first_ach["achievedat"]
    progress=first_ach["progress"]
    print(sum(steps))
    for i in [10,12,14,16,18,20]:
        completed=-1
        if sum(steps)>=i*1000:
            completed=1
        update_goal(userid,"DailyRecordSteps"+str(i),sum(steps),completed)
    if last_updated<datetime.now().timestamp()*1000:
      if sum(steps)>=current_goal:
          for i in [1,3,7,14,25,40,60,80,100]:
            if i==1:
              update_goal(userid,"DailyGoalSteps"+str(i),progress+1,datetime.combine(datetime.now(), time.max).timestamp()*1000)
            else:
               update_goal(userid,"DailyGoalSteps"+str(i),progress+1,1 if progress+1>=i else -1)
          ach=es.get(index="achievements", id=userid+"_"+"RowCompletedSteps3")["_source"]
          last_updated= ach["achievedat"]
          progress=ach["progress"]
          #if the last time it was updated was yesterday then increase counter by one, if not set to 1
          if last_updated>(datetime.combine(datetime.now(), time.min)-timedelta(days=1)).timestamp()*1000:
            for i in [3,7,14,25,40]:
              update_goal(userid,"RowCompletedSteps"+str(i),progress+1,1 if progress+1>=i else -1)
          # else:
          #    update_goal(userid,"RowCompletedSteps"+str(i),1,-1)
          
          

def avg_weekly_steps(userid):
    steps = es.search(index="activity", query={"bool":{"must":[
                                                  {'match' : {"userid":userid}},
                                                  {'range' : {"start":{"gte":(datetime.now()- timedelta(weeks=1)).timestamp()*1000}}},
                                                    ]
                                                  }
                                          }
                      ,size=10000)["hits"]["hits"]
    steps=list(map(lambda x: x["_source"]["steps"],steps))
    for i in [5,6,8,10,12]:
        complete=-1
        if sum(steps)/7>=i*1000:
          complete=1
          print("AverageStepsWeek"+str(i))
          update_goal(userid,"AverageStepsWeek"+str(i),round(sum(steps)/7),complete)
