from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from database import get_db
from models import FormData

router = APIRouter(prefix="/forms/测试表单", tags=["测试表单"])


class FormDataCreate(BaseModel):
    data: dict
    workflow_instance_id: Optional[str] = None


class FormDataResponse(BaseModel):
    id: str
    form_id: str
    data: dict
    status: str
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime


@router.post("/", response_model=FormDataResponse)
async def create_form_data(form_data: FormDataCreate, db = Depends(get_db)):
    db_form = FormData(
        id="fd_{datetime.now().timestamp()}",
        form_id="1781747625664_e6e34550",
        workflow_instance_id=form_data.workflow_instance_id,
        data=form_data.data,
        status="submitted"
    )
    db.add(db_form)
    db.commit()
    db.refresh(db_form)
    return db_form


@router.get("/", response_model=List[FormDataResponse])
async def list_form_data(skip: int = 0, limit: int = 100, db = Depends(get_db)):
    return db.query(FormData).filter(FormData.form_id == "1781747625664_e6e34550").offset(skip).limit(limit).all()


@router.get("/{item_id}", response_model=FormDataResponse)
async def get_form_data(item_id: str, db = Depends(get_db)):
    db_form = db.query(FormData).filter(FormData.id == item_id).first()
    if not db_form:
        raise HTTPException(status_code=404, detail="Data not found")
    return db_form


@router.put("/{item_id}", response_model=FormDataResponse)
async def update_form_data(item_id: str, form_data: FormDataCreate, db = Depends(get_db)):
    db_form = db.query(FormData).filter(FormData.id == item_id).first()
    if not db_form:
        raise HTTPException(status_code=404, detail="Data not found")
    db_form.data = form_data.data
    db.commit()
    db.refresh(db_form)
    return db_form


@router.delete("/{item_id}")
async def delete_form_data(item_id: str, db = Depends(get_db)):
    db_form = db.query(FormData).filter(FormData.id == item_id).first()
    if not db_form:
        raise HTTPException(status_code=404, detail="Data not found")
    db.delete(db_form)
    db.commit()
    return {"message": "Deleted successfully"}
