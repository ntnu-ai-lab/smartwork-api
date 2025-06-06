import pandas as pd
from elasticsearch import helpers
from fastapi import HTTPException
from elasticsearch import Elasticsearch

import json
import argparse
import requests
from init_scripts.config_backup import BACKEND_STATIC_DIR
from init_scripts.parsing import run_parse
def init_mycbr(mycbr_url):
    response=requests.put(mycbr_url+"/concepts/Case/attributes/Activity_StepCount/sequence/similarityFunctions/test_sequence",
                      json={"maxDiff":1000}
    )
    print(response.text)
    response=requests.put(mycbr_url+"/concepts/Case/attributes/BT_pain_average/sequence/similarityFunctions/test_sequence",
                      json={"maxDiff":1000}
    )
    print(response.text)

def populate_db(es_url,es_password):
    run_parse()
    es = Elasticsearch(es_url,basic_auth=("elastic",es_password),verify_certs=False)

    def read_json_file(file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data
    #run parsing scripts


    # education = read_json_file(BACKEND_STATIC_DIR+"education_nb.json")
    # helpers.bulk(es,education,index="education_description")
    # exercise = read_json_file(BACKEND_STATIC_DIR+"exercise_nb.json")
    # helpers.bulk(es,exercise,index="exercise_description")

    # achievements= read_json_file(BACKEND_STATIC_DIR+"achievements_nb.json")
    # helpers.bulk(es,achievements,index="achievement_description")

    tailoring=read_json_file(BACKEND_STATIC_DIR+"tailoring_nb.json")
    # print(tailoring)
    for tail in tailoring:
        tail["_source"]["description_type"]="tailoring"
        del tail["_type"]
    print(tailoring)

    helpers.bulk(es,tailoring,index="tailoring_description",raise_on_error=True)
    print("Tailoring data loaded successfully")
    # for index in ["plan","exercise","education","achievements","activity","appsettings","tailoring_questionnaire","account","baseline","questionnaire"]:

    #     es.indices.create(index = index,ignore=400)
# populate_db("http://localhost:9200","smartwork4ever")