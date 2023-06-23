import uvicorn
from fastapi import FastAPI

from services.oauth import router as oauth_router
from services.patient import router as patient_router
from services.data import router as data_router
from services.admin import router as admin_router
from services.plan import router as plan_router
from static import load_static
from elasticsearch import Elasticsearch
app = FastAPI()

es = Elasticsearch("https://localhost:9400",basic_auth=("elastic","DBAZ-j1uxuEq2s+fXTcI"),verify_certs=False)

app.include_router(oauth_router)
app.include_router(patient_router)
app.include_router(data_router)
app.include_router(admin_router)
app.include_router(plan_router)


@app.get("/")
async def root():
    return {"message": "Nothing to see here"}


if __name__ == "__main__":
    if not es.indices.exists(index="education"):
        load_static(es)
    uvicorn.run("API:app", host="0.0.0.0", port=30000, reload=True)