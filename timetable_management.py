from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from auth_dependencies import get_current_active_user

router = APIRouter()

# In-memory storage for demo; replace with DB integration
timetable_store = {}

@router.put("/timetable/update")
def update_timetable(dept_code: str, updated_schedule: List[Dict], current_user: dict = Depends(get_current_active_user)):
    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Not authorized to update timetable")

    timetable_store[dept_code] = updated_schedule
    return {"message": "Timetable updated successfully"}

@router.get("/timetable/{dept_code}")
def get_timetable(dept_code: str, current_user: dict = Depends(get_current_active_user)):
    schedule = timetable_store.get(dept_code)
    if not schedule:
        raise HTTPException(status_code=404, detail="Timetable not found")
    return schedule
