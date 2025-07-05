# from https://sqlmodel.tiangolo.com/tutorial/fastapi/simple-component-api/#install-fastapi

from fastapi import FastAPI, Depends, HTTPException, Query
from contextlib import asynccontextmanager
from sqlmodel import Field, Session, SQLModel, create_engine, select
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import JSON



class ComponentBase(SQLModel):
    name: str = Field(index=True)
    owner: str
    labels: dict[str, str] = Field(default={"key": "value"}, sa_column=Column(JSON))

class Component(ComponentBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

class ComponentCreate(ComponentBase):
    pass

class ComponentPublic(ComponentBase):
    id: int
    
class ComponentUpdate(SQLModel):
    labels: dict[str, str|None] | None = None
    
    
    
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True, connect_args={"check_same_thread": False})



@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield
    # SHUTDOWN

app = FastAPI(lifespan=lifespan)



def get_session():
    with Session(engine) as session:
        yield session
    


# POST /components
@app.post("/components/", response_model=ComponentPublic)
def create_component(component: ComponentCreate, session: Session = Depends(get_session)):
    db_component = Component.model_validate(component)
    session.add(db_component)
    session.commit()
    session.refresh(db_component)
    return db_component


# GET /components
@app.get("/components/")
def read_components(offset: int = 0, limit: int = Query(default=100, le=100), session: Session = Depends(get_session)):
    components = session.exec(select(Component).offset(offset).limit(limit)).all()
    return components


# GET /components/{id}
@app.get("/components/{id}", response_model=ComponentPublic)
def read_component(id: int, session: Session = Depends(get_session)):
    component = session.get(Component, id)
    if component is None:
        raise HTTPException(status_code=404, detail="Component not found")
    return component
    

# PUT /components/{id}
@app.put("/components/{id}", response_model=ComponentPublic)
def update_component(id: int, component: ComponentUpdate, session: Session = Depends(get_session)):
    db_component = session.get(Component, id)
    if db_component is None:
        raise HTTPException(status_code=404, detail="Component not found")
    #component_data = component.model_dump(exclude_unset=True)
    #db_component.sqlmodel_update(component_data)
    if component.labels is not None:
        merged_labels = db_component.labels | component.labels
        merged_labels = {k:v for (k,v) in merged_labels.items() if v is not None}
        db_component.labels = merged_labels
    session.add(db_component)
    session.commit()
    session.refresh(db_component)
    return db_component


# DELETE /components/{id}
@app.delete("/components/{id}")
def delete_component(id: int, session: Session = Depends(get_session)):
    component = session.get(Component, id)
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    session.delete(component)
    session.commit()
    return {"ok": True}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)