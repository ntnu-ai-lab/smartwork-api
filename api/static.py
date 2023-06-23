import pandas as pd
from elasticsearch import helpers
from fastapi import HTTPException


def load_static(es):
    try:
        #create exercise index and populate
        es.indices.create(index = 'exercise')
        exercise=pd.read_excel("./Exercises-ES-plain-nb.xlsx")
        exercise.fillna("Missing value", inplace=True)
        exercise.drop(columns="Type",inplace=True)
        exercise=exercise[exercise.ExerciseID!="Missing value"]
        exercise=exercise.to_dict(orient="records")
        helpers.bulk(es,exercise,index="exercise")

        #create education index and populate
        es.indices.create(index = 'education')
        education=pd.read_excel("./Education-ES-plain-nb.xlsx")
        education.fillna("Missing value", inplace=True)
        education=education.to_dict(orient="records")
        helpers.bulk(es,education,index="education")
    except:
        raise HTTPException(status_code=500,detail="Could not create static indices.")

