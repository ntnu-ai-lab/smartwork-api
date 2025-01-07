import pandas as pd
from elasticsearch import helpers
from fastapi import HTTPException
from elasticsearch import Elasticsearch
import json
es = Elasticsearch("http://localhost:9400",basic_auth=("elastic","secret"),verify_certs=False)

def read_json_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data
BACKEND_FOLDER="./kerstin_scripts/backend_static_data/"
education = read_json_file(BACKEND_FOLDER+"education_nb.json")
helpers.bulk(es,education,index="data_description")

exercise = read_json_file(BACKEND_FOLDER+"exercise_nb.json")
helpers.bulk(es,exercise,index="data_description")

achievements= read_json_file(BACKEND_FOLDER+"achievements_nb.json")

helpers.bulk(es,achievements,index="data_description")

tailoring=read_json_file(BACKEND_FOLDER+"tailoring_nb.json")
# print(tailoring)
for tail in tailoring:
    tail["_source"]["description_type"]="tailoring"
    del tail["_type"]
helpers.bulk(es,tailoring,index="data_description")

