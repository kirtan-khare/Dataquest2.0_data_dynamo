from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date
import uuid
from auth_dependencies import get_current_active_user

router = APIRouter()

class SubstituteAssignment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: date
    original_teacher_id: str
    substitute_teacher_id: str
    course_id: str
    timeslot: str

substitutions_db: List[SubstituteAssignment] = []

@router.post("/substitutes", response_model=SubstituteAssignment)
def add_substitution(substitution: SubstituteAssignment, current_user: dict = Depends(get_current_active_user)):
    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    substitutions_db.append(substitution)
    return substitution

@router.get("/substitutes", response_model=List[SubstituteAssignment])
def get_substitutions(date_filter: Optional[date] = None, current_user: dict = Depends(get_current_active_user)):
    if date_filter:
        filtered = [sub for sub in substitutions_db if sub.date == date_filter]
        return filtered
    return substitutions_db

@router.put("/substitutes/{sub_id}", response_model=SubstituteAssignment)
def update_substitution(sub_id: str, substitution: SubstituteAssignment, current_user: dict = Depends(get_current_active_user)):
    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    for index, sub in enumerate(substitutions_db):
        if sub.id == sub_id:
            substitutions_db[index] = substitution
            return substitution
    raise HTTPException(status_code=404, detail="Substitution not found")

@router.delete("/substitutes/{sub_id}")
def delete_substitution(sub_id: str, current_user: dict = Depends(get_current_active_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    for index, sub in enumerate(substitutions_db):
        if sub.id == sub_id:
            substitutions_db.pop(index)
            return {"detail": "Substitution deleted"}
    raise HTTPException(status_code=404, detail="Substitution not found")
