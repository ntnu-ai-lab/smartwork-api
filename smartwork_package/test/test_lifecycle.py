import unittest
import requests

from datetime import datetime,timezone,timedelta
from elasticsearch import Elasticsearch
from smartwork_package.api.resources.constants import URL,ES_URL,BASIC_AUTH,EXERCISE_MAX_SIZE,EDUCATION_QUIZ_MAX,STEP_GOAL_MIN,STEP_GOAL_MAX
from smartwork_package.test.resources.helper_functions import delete_all_indicies,create_plan
from smartwork_package.test.resources.constants import ADMIN_PASSWORD,ADMIN_USERNAME
import json
# from fastapi.testclient import TestClient
from freezegun import freeze_time
class TestLifeCycle(unittest.TestCase):

    # def setUp(self):
        
    @classmethod
    def tearDownClass(cls):
        # delete_all_indicies(cls.es)
        print(12312)
    @classmethod
    def setUpClass(cls):
        
        #add data_description files
        from init_scripts import static
        #import es and read questionnaire from file
        cls.es= Elasticsearch(ES_URL,basic_auth=BASIC_AUTH,verify_certs=False)
        with open('./smartwork_package/test/resources/test-content.json') as f:
            questionnaire = json.load(f)
        cls.base_questionnaire=questionnaire

        #add admin user
        cls.es.indices.create(index = 'account')
        res = cls.es.index(index='account', id=ADMIN_USERNAME, 
                    document={
                        'userid': ADMIN_USERNAME,
                        'password': '$2b$12$phrVybcm8uyeTl9D/cdYoeZxiOHsjddjitMoYWv8lMVu9bMuY1L2a',
                        'country': 'nl',
                        'clinician': 'NTNU',
                        'rights': ['ROLE_ADMIN', 'ACTUATOR'],
                        'isaccountnonexpired': True,
                        'isaccountnonlocked': True,
                        'iscredentialsnonexpired': True,
                        'isenabled': True}
        )
        cls.es.indices.refresh(index='account')
        #get admin token
        response=requests.post(f"{URL}/oauth/token",data={"username":ADMIN_USERNAME,"password":ADMIN_PASSWORD})
        token=response.json()["access_token"]
        cls.admin_token=token
        #add test user
        response=requests.post(f"{URL}/admin/adduser",
                      headers={"Authorization": f"Bearer {token}"},
                      json={
                              "group": "LBP_NP",
                              "language": "nb",
                              "password": 'secret',
                              "questionnaire": cls.base_questionnaire,
                              "role": "ROLE_USER",
                              "username": "test"
                              }
                      )
        #fetch user token
        response=requests.post(f"{URL}/oauth/token",data={"username":"test","password":"secret"})
        token=response.json()["access_token"]
        cls.token=token

    def basicPlanValidation(self,plan):

        self.assertLessEqual(len(plan["plan"]["exercises"]),EXERCISE_MAX_SIZE)
        # self.assertTrue(False)
        self.assertTrue(len(plan["plan"]["exercises"])>=3)
        exercise_ids=list(map(lambda x:x["exerciseid"],plan["plan"]["exercises"]))
        self.assertEqual(len(exercise_ids),len(set(exercise_ids)))
        education_ids=list(map(lambda x:x["educationid"],plan["plan"]["educations"]))
        self.assertEqual(len(education_ids),len(set(education_ids)))
        # print(plan["plan"]["educations"])
        total_quizes=list(map(lambda x:x["is_quiz"],plan["plan"]["educations"]))
        self.assertLessEqual(sum(total_quizes),EDUCATION_QUIZ_MAX)
        self.assertGreaterEqual(plan["plan"]["activity"]["goal"],STEP_GOAL_MIN)
        self.assertLessEqual(plan["plan"]["activity"]["goal"],STEP_GOAL_MAX)

        


    def testLifeCycle(self):
        #each row is one week
        testSteps = [
                [4340, 4797, 5632, 3823, 5982, 3623, 4398],
                [4500, 8567, 5632, 8823, 5982, 3623, 4398],
                [2500, 8567, 5632, 7823, 8882, 8623, 4398],
                [8500, 8567, 8632, 7823, 8882, 567, 875],
                [967, 1567, 937, 567, 1875, 7823, 8882],
                [2000, 2000, 2000, 2000, 15000, 2000, 2000]
                ]
        #expected values for the step goal
        goals=[4000,5800]
        #add user and check if it works, with 35min of workout
        self.assertTrue(self.es.exists(index="account", id="test"))
        #this is used to temporarily change the datetime of python
        # freezer = freeze_time("2010-10-01 00:00:00")
        # freezer.start()
        first_plan=requests.post(f"{URL}/patient/plan/next",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "questionnaire":None,
                "exercises_duration":35
            }
        )
        # freezer.stop()
        #basic plan validation
        self.basicPlanValidation(first_plan.json())
        #modify date in ES 
        
        #update app settings with notification settings?? necessary, done in java code

        #check if get plan/on works
        response=requests.get(f"{URL}/patient/plan/on/2024-10-06",headers={"Authorization": f"Bearer {self.token}"})
        print(response.json())



        #day 0, create first plan providing empty tailoring data
        #check if plan corresponds to preset values

        #check if getplanon works for the the correct date

        #check achievement intro session
        #check achievement tailoring session

        #check that there are 7 exercises in the plan

        #check that all exercise types are present

        #check that three sets are required for back exercise and 10 reps

        #check that first step goal is 3000

        #add steps for first day

        ##day 1 week 0

        #post completion of all exercises
        #add activity
        ##day 2 week 0
        #this day has 100% completion of all three activities
        #add activity
        #complete all exercises
        #complete all educational items

        ##day 3 week 0
        #add activity
        #add exercises

        ##day 4 week 0
        #add activity
        #add exercises

        ##day 5 week 0
        #add activity
        #skip core and back exercise to raise the level

        ##day 6 week 0
        #add activity
        #add exercises
        #check can skip exercise for core, back and glute, should be false for core and back

        ##day 7 week 0
        #add steps

        ##day 1 week 1

        #check that the completed educational items are the correct ones, also check uncompleted ones

        #check activity values from past week, both specific days and sums over longer periods
        #ask Kerstin here, what is the point of all of these tests for stepbuckets in the java code?

        #get patient plan for day 0, week 1
        #check date, exerciseduration, if plan is the same as the one inserted
        #exercise completed size, educational items completed size
        #check the days an exercise or educational item was completed
        

        #week 2, day 0

        #update settings
        #fetch tailoring questions and check if pain question is there

        #return tailoring questions


        #do basic plan validation(needs to be implemented)

        #assert that suggested goal for this week should be same as last week?

        ##day 1 week 2
        #add activity

        #test that BT_PSEQ_2items, BT_PSS_4items, BT_PHQ_2item are aggregated correctly
        # what is this? None of those items are in the tailoring questionnaires
        #check that stepgoal is correct
        # 
        # check that at least one of preset items appear in educational plan as they should be triggered by QUESTION_BT_PHQ
        # 
        # should be 7 exercises in the plan
        # all exercises should either start with flex or have 3 sets
        # and should start with flex or have 10 reps
        # there must be either a back and an ab exercse or a core exercise
        # 
        # back and core where skipped as easy so the level should be 2
        # all other items should be level 1   



        

if __name__ == "__main__":
    unittest.main()