from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import Annotated

from app.database import LocalDatabase
from app.model import ExposedAPI, ExposedAPICreate, ExposedAPIPublic, ExposedAPIUpdate, ExposedAPIPublicWithComponent

# Depends(LocalDatabase.get_instance_session)
SessionDep = Annotated[Session, Depends(LocalDatabase.get_instance_session)]

router = APIRouter(prefix="/exposedapis", tags=["exposedapis"])

E404={404: {"description": "Not found"}}


# POST /exposedapis
@router.post("/", response_model=ExposedAPIPublic)
def create_exposedapi(*, session: SessionDep, exposedapi: ExposedAPICreate):
    db_exposedapi = ExposedAPI.model_validate(exposedapi)
    session.add(db_exposedapi)
    session.commit()
    session.refresh(db_exposedapi)
    return db_exposedapi


# GET /exposedapis
@router.get("/", response_model=list[ExposedAPIPublic])
def read_exposedapis(*, session: SessionDep, offset: int = 0, limit: int = Query(default=100, le=100)):
    exposedapis = session.exec(select(ExposedAPI).offset(offset).limit(limit)).all()
    return exposedapis


# GET /exposedapis/{eapi_id}
@router.get("/{eapi_id}", response_model=ExposedAPIPublicWithComponent, responses=E404)
def read_exposedapi(*, session: SessionDep, eapi_id: int):
    exposedapi = session.get(ExposedAPI, eapi_id)
    if exposedapi is None:
        raise HTTPException(status_code=404, detail="ExposedAPI not found")
    return exposedapi


# PATCH /exposedapis/{eapi_id}
@router.patch("/{eapi_id}", response_model=ExposedAPIPublic, responses=E404)
def update_exposedapi(*, session: SessionDep, eapi_id: int, exposedapi: ExposedAPIUpdate):
    db_exposedapi = session.get(ExposedAPI, eapi_id)
    if db_exposedapi is None:
        raise HTTPException(status_code=404, detail="ExposedAPI not found")
    if exposedapi.labels is not None:
        merged_labels = db_exposedapi.labels | exposedapi.labels
        merged_labels = {k:v for (k,v) in merged_labels.items() if v is not None}
        db_exposedapi.labels = merged_labels
    session.add(db_exposedapi)
    session.commit()
    session.refresh(db_exposedapi)
    return db_exposedapi


# DELETE /exposedapis/{eapi_id}
@router.delete("/{eapi_id}", responses=E404)
def delete_exposedapi(*, session: SessionDep, eapi_id: int):
    exposedapi = session.get(ExposedAPI, eapi_id)
    if not exposedapi:
        raise HTTPException(status_code=404, detail="ExposedAPI not found")
    session.delete(exposedapi)
    session.commit()
    return {"ok": True}

