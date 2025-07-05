# from https://sqlmodel.tiangolo.com/tutorial/fastapi/simple-component-api/#install-fastapi

from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
from sqlmodel import Field, Session, SQLModel, create_engine, select
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import JSON

class Component(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    owner: str
    labels: dict[str, str] = Field(default={"key": "value"}, sa_column=Column(JSON))


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


#===============================================================================
# @app.on_event("startup")
# def on_startup():
#     create_db_and_tables()
#===============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    create_db_and_tables()
    yield
    # SHUTDOWN

app = FastAPI(lifespan=lifespan)


# Funktion zum Abrufen einer Datenbanksitzung
def get_session():
    with Session(engine) as session:
        yield session
    

# POST /components
@app.post("/components/")
def create_component(component: Component):
    with Session(engine) as session:
        session.add(component)
        session.commit()
        session.refresh(component)
        return component


# GET /components
@app.get("/components/")
def read_components():
    with Session(engine) as session:
        components = session.exec(select(Component)).all()
        return components

# GET /components/{id}
@app.get("/components/{id}", response_model=Component)
def read_component(id: int, session: Session = Depends(get_session)):
    component = session.exec(select(Component).where(Component.id == id)).one_or_none()
    if component is None:
        raise HTTPException(status_code=404, detail="Komponente nicht gefunden")
    return component
    
    
    
    
@app.delete("/components/{id}")
def delete_component(id: int, session: Session = Depends(get_session)):
    component = session.exec(select(Component).where(Component.id == id)).one_or_none()
    if component is None:
        raise HTTPException(status_code=404, detail="Komponente nicht gefunden")
    
    print("Component: ", component)
    session.delete(component)
    session.commit()    
    return {"message": "Component deleted"}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)