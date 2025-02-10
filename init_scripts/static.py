import pandas as pd
from elasticsearch import helpers
from fastapi import HTTPException
from elasticsearch import Elasticsearch
import parsing
import json
import argparse

parser=argparse.ArgumentParser()
parser.add_argument("--es_password")
parser.add_argument("--es_url")
args=parser.parse_args()


from config_backup import BACKEND_STATIC_DIR
es = Elasticsearch(parser.es_url,basic_auth=("elastic",parser.es_password),verify_certs=False)

def read_json_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data
#run parsing scripts


education = read_json_file(BACKEND_STATIC_DIR+"education_nb.json")
helpers.bulk(es,education,index="data_description")

exercise = read_json_file(BACKEND_STATIC_DIR+"exercise_nb.json")
helpers.bulk(es,exercise,index="data_description")

achievements= read_json_file(BACKEND_STATIC_DIR+"achievements_nb.json")

helpers.bulk(es,achievements,index="data_description")

tailoring=read_json_file(BACKEND_STATIC_DIR+"tailoring_nb.json")
# print(tailoring)
for tail in tailoring:
    tail["_source"]["description_type"]="tailoring"
    del tail["_type"]
print(tailoring)
helpers.bulk(es,tailoring,index="data_description")

es.indices.create(index = 'plan')
es.indices.create(index = 'exercise')
es.indices.create(index = 'education')
es.indices.create(index = 'achievements')
es.indices.create(index = 'activity')
es.indices.create(index = 'appsettings')
es.indices.create(index = 'tailoring_questionnaire')
es.indices.create(index = 'account')
es.indices.create(index = 'baseline')
es.indices.create(index = 'questionnaire')