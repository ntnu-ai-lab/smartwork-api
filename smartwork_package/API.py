import uvicorn
from fastapi import FastAPI,Depends,Request
import os
import sys

from api.services.oauth import router as oauth_router
from api.services.patient import router as patient_router
from api.services.data import router as data_router
from api.services.admin import router as admin_router
from api.services.plan import router as plan_router





app = FastAPI(
    title="SmartWork",
    docs_url="/"
)


app.include_router(oauth_router)
app.include_router(patient_router)
app.include_router(data_router)
app.include_router(admin_router)
app.include_router(plan_router)

@app.get("/")
async def root():
    return {"message": "Nothing to see here"}





if __name__ == "__main__":
    uvicorn.run(
        "API:app", 
        host="0.0.0.0", 
        port=443, 
        ssl_keyfile="/opt/selfback/smartwork_cert.key",
        ssl_certfile="/opt/selfback/smartwork_cert.pem",
        reload=True,
        # workers=4
        )
    #back-up:~/smartwork/smartwork_package$ sudo ~/.venv/bin/python API.py Trux32
    #ssh -R 443:localhost:8080 stuartgo@back-up.idi.ntnu.no