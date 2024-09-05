from elasticsearch import Elasticsearch, helpers
from datetime import datetime
import pandas as pd
es = Elasticsearch("http://localhost:9400",basic_auth=("elastic","secret"),verify_certs=False)



#engang
def complete_onetime_goal(userid,goalid):
    #possible goal ids
    #SetGoalSetting,SetSleepTool,UseMindfulness,QACompleted,SessionCompleted
    res = es.search(index="achievements", 
          query={"bool":{"must":[
            {'match' : 
                 {"userid":userid}},
            {'match' : 
                 {"achievementid":goalid}}
          ]}},size=10000)["hits"]["hits"][0]
    id=res["_id"]
    res=res["_source"]
    res["progress"]=1
    res["achievedat"]=1
    es.update(index='achievements',id=id,
                doc=res)

def total_steps(userid):
    #This can be implemented more efficiently with fewer requests
    completed_achievements=[]
    res = es.search(index="activity", query={'match' : {"userid":userid}},size=10000)["hits"]["hits"]
    res=list(map(lambda x: x["_source"],res))
    df=pd.DataFrame(res)
    if len(df)==0:
        return None
    df.start=df.start.apply(lambda x: datetime.fromtimestamp(x/1000))
    df.end=df.end.apply(lambda x: datetime.fromtimestamp(x/1000))
    df
    for i in [50,100,200,400,600,800,1000,42.195]:
        if i!=42.195:
            ach_id="TotalSteps"+str(i)
        else:
            ach_id="Marathon"
        res = es.search(index="achievements", 
            query={"bool":{"must":[
                {'match' : 
                    {"userid":userid}},
                {'match' : 
                    {"achievementid":ach_id}}
            ]}},size=10000)["hits"]["hits"][0]
        id=res["_id"]
        res=res["_source"]
        if ach_id=="Marathon":
            res["progress"]=0
        else:
            res["progress"]=df.steps.sum()
        if df.steps.sum()>=i*1000:
            res["achievedat"]=1
            es.update(index='achievements',id=id,doc=res)
        else:
            break
        

def avg_steps_per_week(userid):
    #This can be implemented more efficiently with fewer requests
    res = es.search(index="activity", query={'match' : {"userid":userid}},size=10000)["hits"]["hits"]
    res=list(map(lambda x: x["_source"],res))
    df=pd.DataFrame(res)
    df.start=df.start.apply(lambda x: datetime.fromtimestamp(x/1000))
    df.end=df.end.apply(lambda x: datetime.fromtimestamp(x/1000))
    # display(df[df.start > datetime.now() - pd.to_timedelta("7day")])
    for i in [5,6,8,10,12]:
        res = es.search(index="achievements", 
            query={"bool":{"must":[
                {'match' : 
                    {"userid":userid}},
                {'match' : 
                    {"achievementid":"AverageStepsWeek"+str(i)}}
            ]}},size=10000)["hits"]["hits"][0]
        id=res["_id"]
        res=res["_source"]
        average=df.steps.sum()/7
        res["progress"]=average
        if average>=i*1000:
            res["achievedat"]=1
            es.update(index='achievements',id=id,doc=res)
        else:
            break



def steps_in_a_day(userid):
    res = es.search(index="activity", query={'match' : {"userid":userid}},size=10000)["hits"]["hits"]
    res=list(map(lambda x: x["_source"],res))
    df=pd.DataFrame(res)
    df.start=df.start.apply(lambda x: datetime.fromtimestamp(x/1000))
    df.end=df.end.apply(lambda x: datetime.fromtimestamp(x/1000))
    max_steps_in_a_day=df.groupby(df.start.dt.date).steps.sum().max()
    for i in [10,12,14,16,18,20]:
        res = es.search(index="achievements", 
            query={"bool":{"must":[
                {'match' : 
                    {"userid":userid}},
                {'match' : 
                    {"achievementid":"DailyRecordSteps"+str(i)}}
            ]}},size=10000)["hits"]["hits"][0]
        id=res["_id"]
        res=res["_source"]
        res["progress"]=max_steps_in_a_day
        if max_steps_in_a_day>=i*1000:
            res["achievedat"]=1
            es.update(index='achievements',id=id,doc=res)
        else:
            break
#fullfør en tilpasning av planen din
#fullfør intro


# def correct_quizes()