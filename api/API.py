import uvicorn
from fastapi import FastAPI

from services.oauth import router as oauth_router
from services.patient import router as patient_router
from services.data import router as data_router
app = FastAPI()


app.include_router(oauth_router)
app.include_router(patient_router)
app.include_router(data_router)



@app.get("/")
async def root():
    return {"message": "Nothing to see here"}


if __name__ == "__main__":
    uvicorn.run("API:app", host="0.0.0.0", port=30000, reload=True)