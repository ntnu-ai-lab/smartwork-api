from fastapi import APIRouter




router = APIRouter(prefix="/patient")


@router.get("/plan/next")
async def root():
    return {"message": "Nothing to see here"}