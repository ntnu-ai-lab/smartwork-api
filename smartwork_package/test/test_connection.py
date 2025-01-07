import unittest
import requests
import datetime
from smartwork_package.api.resources.constants import URL
from smartwork_package.test.resources.constants import ADMIN_PASSWORD,ADMIN_USERNAME
import json
class TestGetESDataRange(unittest.TestCase):
    def test_questionnaire_answer(self):
        #admin token
        response=requests.get(f"{URL}/oauth/token",data={"username":ADMIN_USERNAME,"password":ADMIN_PASSWORD})
        token=response.json()["access_token"]
        #add test user
        with open('./smartwork_package/test/resources/test-content.json') as f:
            questionnaire = json.load(f)
        response=requests.post(f"{URL}/admin/adduser",verify=False,
                      headers={"Authorization": f"Bearer {token}"},
                      json={
                              "group": "LBP_NP",
                              "language": "nb",
                              "password": 'secret',
                              "questionnaire": questionnaire,
                              "date_completed":datetime.datetime.now().timestamp(),
                              "role": "ROLE_USER",
                              "username": "tbarr"
                              }
                      )
        #fetch user token
        response=requests.post(f"{URL}/oauth/token",data={"username":"tbarr","password":"secret"})
        token=response.json()["access_token"]
        #insert tailoring questionnaires
        with open('./smartwork_package/test/resources/T_barriers0.json') as f:
            tailoring_questionnaires = json.load(f)
        for tailoring in tailoring_questionnaires:
            response=requests.post(f"{URL}/patient/plan/tailoring",verify=False,
                      headers={"Authorization": f"Bearer {token}"},
                      json=tailoring
                      )
        #upload all his tbarr tailoring questionnaires
        #fetch the questionnaires
        self.assertEqual("0",questionnaires[0]["answer"])
        self.assertEqual("none",questionnaires[1]["answer"])
        self.assertEqual("0;1",questionnaires[2]["answer"])
        self.assertEqual("0;1",questionnaires[3]["answer"])
        self.assertEqual("lac_of_time;too_tired",questionnaires[4]["answer"])

if __name__ == "__main__":
    print("sause")
    unittest.main()