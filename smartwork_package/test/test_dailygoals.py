import unittest
import requests
from datetime import datetime,timezone,timedelta
from elasticsearch import Elasticsearch
from smartwork_package.api.resources.constants import URL,ES_URL,BASIC_AUTH
from smartwork_package.test.resources.helper_functions import delete_all_indicies,create_plan
from smartwork_package.test.resources.constants import ADMIN_PASSWORD,ADMIN_USERNAME
import json
class TestDailyGoals(unittest.TestCase):

    def setUp(self):
        response=requests.post(f"{URL}/admin/adduser",verify=False,
                        headers={"Authorization": f"Bearer {self.admin_token}"},
                        json={
                                "group": "LBP_NP",
                                "language": "nb",
                                "password": 'secret',
                                "questionnaire": self.base_questionnaire,
                                "date_completed":datetime.datetime.now().timestamp(),
                                "role": "ROLE_USER",
                                "username": "dailyGoalUser"
                                }
                        )
        

    def tearDown(self):
        delete_all_indicies(self.es)

    @classmethod
    def setUpClass(cls):
        #admin token
        # response=requests.post(f"{URL}/oauth/token",data={"username":ADMIN_USERNAME,"password":ADMIN_PASSWORD})
        # token=response.json()["access_token"]
        # cls.admin_token=token
        with open('./smartwork_package/test/resources/test-content.json') as f:
            questionnaire = json.load(f)
        cls.base_questionnaire=questionnaire
        es = Elasticsearch(ES_URL,basic_auth=BASIC_AUTH,verify_certs=False)
        cls.es=es
        


    def testTimeZones(self):
        # #fetch user token
        # response=requests.post(f"{URL}/oauth/token",data={"username":"tbarr","password":"secret"})
        # token=response.json()["access_token"]
        # #increase time zone by 4
        start_time=datetime(2000,1,1,tzinfo=timezone(timedelta(hours=4)))
        utc_start_time=start_time.astimezone(tz=timezone.utc)
        self.assertEqual(20,utc_start_time.hour)
        self.assertEqual(31,utc_start_time.day)
        create_plan(self.es,start_time-timedelta(days=2),"dailyGoalUser")
        #add activity 1 and 2 hours after start of size 1500 and 1800
        #ger profess on 2000.01.01
        #check progress
        

if __name__ == "__main__":
    unittest.main()