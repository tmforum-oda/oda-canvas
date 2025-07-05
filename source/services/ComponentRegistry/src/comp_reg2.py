from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Session, create_engine
from typing import List

app = FastAPI()

# Definition des Component-Objekts
class ComponentBase(BaseModel):
    name: str
    description: str

class Component(ComponentBase):
    id: int

    class Config:
        orm_mode = True

# Definition der Datenbank-Tabelle
class ComponentTable(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    description: str

# Erstellung der Datenbank-Engine
engine = create_engine("sqlite:///components.db")

# Erstellung der Datenbank-Tabelle
SQLModel.metadata.create_all(engine)

# Funktion zum Abrufen einer Datenbanksitzung
def get_session():
    with Session(engine) as session:
        yield session

# GET /components
@app.get("/components/", response_model=List[Component])
def read_components(session: Session = Depends(get_session)):
    return session.query(ComponentTable).all()

# GET /components/{id}
@app.get("/components/{id}", response_model=Component)
def read_component(id: int, session: Session = Depends(get_session)):
    component = session.query(ComponentTable).get(id)
    if component is None:
        raise HTTPException(status_code=404, detail="Komponente nicht gefunden")
    return component

# POST /components
@app.post("/components/", response_model=Component)
def create_component(component: ComponentBase, session: Session = Depends(get_session)):
    db_component = ComponentTable.from_orm(component)
    session.add(db_component)
    session.commit()
    session.refresh(db_component)
    return db_component

# PUT /components/{id}
@app.put("/components/{id}", response_model=Component)
def update_component(id: int, component: ComponentBase, session: Session = Depends(get_session)):
    db_component = session.query(ComponentTable).get(id)
    if db_component is None:
        raise HTTPException(status_code=404, detail="Komponente nicht gefunden")
    db_component.name = component.name
    db_component.description = component.description
    session.commit()
    session.refresh(db_component)
    return db_component

# DELETE /components/{id}
@app.delete("/components/{id}")
def delete_component(id: int, session: Session = Depends(get_session)):
    component = session.query(ComponentTable).get(id)
    if component is None:
        raise HTTPException(status_code=404, detail="Komponente nicht gefunden")
    session.delete(component)
    session.commit()
    return {"message": "Komponente gelöscht"}


if __name__ == "__main__":
	import uvicorn
	uvicorn.run(app, host="0.0.0.0", port=8080)
