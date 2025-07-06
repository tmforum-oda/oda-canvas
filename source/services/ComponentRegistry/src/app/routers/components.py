from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import Annotated

from app.database import LocalDatabase
from app.model import Component, ComponentCreate, ComponentPublic, ComponentUpdate

# Depends(LocalDatabase.get_instance_session)
SessionDep = Annotated[Session, Depends(LocalDatabase.get_instance_session)]

router = APIRouter(prefix="/components", tags=["components"])

# POST /components
@router.post("/", response_model=ComponentPublic)
def create_component(session: SessionDep, component: ComponentCreate):
    db_component = Component.model_validate(component)
    session.add(db_component)
    session.commit()
    session.refresh(db_component)
    return db_component


# GET /components
@router.get("/")
def read_components(session: SessionDep, offset: int = 0, limit: int = Query(default=100, le=100)):
    components = session.exec(select(Component).offset(offset).limit(limit)).all()
    return components


# GET /components/{comp_id}
@router.get("/components/{comp_id}", tags=["components"], response_model=ComponentPublic, responses={404: {"description": "Not found"}})
def read_component(session: SessionDep, comp_id: int):
    component = session.get(Component, comp_id)
    if component is None:
        raise HTTPException(status_code=404, detail="Component not found")
    return component


# PUT /components/{comp_id}
@router.put("/components/{comp_id}", tags=["components"], response_model=ComponentPublic, responses={404: {"description": "Not found"}})
def update_component(session: SessionDep, comp_id: int, component: ComponentUpdate):
    db_component = session.get(Component, comp_id)
    if db_component is None:
        raise HTTPException(status_code=404, detail="Component not found")
    if component.labels is not None:
        merged_labels = db_component.labels | component.labels
        merged_labels = {k:v for (k,v) in merged_labels.items() if v is not None}
        db_component.labels = merged_labels
    session.add(db_component)
    session.commit()
    session.refresh(db_component)
    return db_component


# DELETE /components/{comp_id}
@router.delete("/components/{comp_id}", tags=["components"], responses={404: {"description": "Not found"}})
def delete_component(session: SessionDep, comp_id: int):
    component = session.get(Component, comp_id)
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    session.delete(component)
    session.commit()
    return {"ok": True}

