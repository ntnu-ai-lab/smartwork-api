import pandas as pd
from elasticsearch import helpers
from fastapi import HTTPException
from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9400",basic_auth=("elastic","secret"),verify_certs=False)
def load_static(es):
    try:
        if not es.indices.exists(index="data_description"):
            #create description index
            es.indices.create(index = 'data_description')

            #populate with education items
            education=pd.read_excel("./init_scripts/Education-ES-plain-nb.xlsx")
            education.fillna("Missing value", inplace=True)
            education=education.to_dict(orient="records")
            education=list(map(lambda x: x|{"description_type":"education"},education))
            helpers.bulk(es,education,index="data_description")

            #populate with exercise items
            exercise=pd.read_excel("./init_scripts/Exercises-ES-plain-nb.xlsx")
            print(exercise)
            exercise.fillna("Missing value", inplace=True)
            exercise.drop(columns="Type",inplace=True)
            exercise=exercise[exercise.ExerciseID!="Missing value"]
            exercise=exercise.to_dict(orient="records")
            exercise=list(map(lambda x: x|{"description_type":"exercise"},exercise))
            helpers.bulk(es,exercise,index="data_description")
            for country in ["da","en","nb","nl"]:
                achievements=pd.read_json(f"./init_scripts/achievements_{country}.json")
                achievements.fillna("No value",inplace=True)
                achievements=achievements.to_dict(orient="records")
                achievements==list(map(lambda x: x|{"description_type":"achievements"},education))
                helpers.bulk(es,achievements,index="achievement")
    except:
        raise HTTPException(status_code=500,detail="Could not create static indices.")
load_static(es)

exercise=pd.read_excel("./init_scripts/Exercises-ES-plain-nb.xlsx")
print(exercise["Type"])

# import pandas as pd
# from elasticsearch import helpers
# from fastapi import HTTPException
# from elasticsearch import Elasticsearch

# es = Elasticsearch("https://localhost:9400",basic_auth=("elastic","6EyF411gLeZnfcvbdT0q"),verify_certs=False)
# def load_static(es):
#     try:
        
#         if not es.indices.exists(index="education"):
#             #create education index and populate
#             es.indices.create(index = 'education')
#             education=pd.read_excel("./init_scripts/Education-ES-plain-nb.xlsx")
#             education.fillna("Missing value", inplace=True)
#             education=education.to_dict(orient="records")
#             helpers.bulk(es,education,index="education")
#         if not es.indices.exists(index="exercise"):
#             #create exercise index and populate
#             es.indices.create(index = 'exercise')
#             exercise=pd.read_excel("./init_scripts/Exercises-ES-plain-nb.xlsx")
#             exercise.fillna("Missing value", inplace=True)
#             exercise.drop(columns="Type",inplace=True)
#             exercise=exercise[exercise.ExerciseID!="Missing value"]
#             exercise=exercise.to_dict(orient="records")
#             helpers.bulk(es,exercise,index="exercise")
#         if not es.indices.exists(index="achievement"):
#             es.indices.create(index = 'achievement')
#             for country in ["da","en","nb","nl"]:
#                 achievememnts=pd.read_json(f"./init_scripts/achievements_{country}.json")
#                 achievememnts.fillna("No value",inplace=True)
#                 helpers.bulk(es,achievememnts.to_dict(orient="records"),index="achievement")

#     except:
#         raise HTTPException(status_code=500,detail="Could not create static indices.")

# load_static(es)