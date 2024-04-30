import pandas as pd
from elasticsearch import helpers
from fastapi import HTTPException
from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9400",basic_auth=("elastic","secret"),verify_certs=False)



def load_education(es):
    education=pd.read_excel("./init_scripts/NP_&_LBP_Educational_selfBACK_NO.xlsx")
    education.fillna("Missing value", inplace=True)
    print(education)
    education=education.to_dict(orient="records")
    education=list(map(lambda x: x|{"description_type":"education"},education))
    education=list(map(lambda x: dict((k.lower(), v) for k, v in x.items()) ,education))
    # helpers.bulk(es,education,index="data_description")

def load_exercises(es):
    exercise=pd.read_excel("./init_scripts/NP_&_LBP_Exercises-selfBACK_NO.xlsx")   
    exercise.fillna(value="", inplace=True)
    # exercise.drop(columns="Type",inplace=True)
    
    exercise=exercise[exercise.ExerciseID!=""]
    # exercise.replace("","No value",inplace=True)
    print(exercise)
    exercise=exercise.to_dict(orient="records")
    exercise=list(map(lambda x: x|{"description_type":"exercise"},exercise))
    exercise=list(map(lambda x: dict((k.lower(), v) for k, v in x.items()) ,exercise))

    helpers.bulk(es,exercise,index="data_description")

def load_achievements(es):
    achievements=pd.read_json(f"./init_scripts/achievements_nb.json")
    achievements.fillna("No value",inplace=True)
    achievements=achievements.to_dict(orient="records")
    achievements=list(map(lambda x: x|{"description_type":"achievement"},achievements))
    helpers.bulk(es,achievements,index="data_description")


def load_tailoring(es):
    tailoring=pd.read_json(f"./init_scripts/tailoring_nb.json",orient="records")
    tailoring=tailoring.to_dict(orient="records")
    
    tailoring=list(map(lambda x: x["_source"]|{"description_type":"tailoring"},tailoring))
    
    # helpers.bulk(es,tailoring,index="data_description")


# load_education(es)
try:
    if not es.indices.exists(index="data_description"):
        #create description index
        es.indices.create(index = 'data_description')

        load_exercises(es)
        load_education(es)
        load_achievements(es)
        
except:
    raise HTTPException(status_code=500,detail="Could not create static indices.")


