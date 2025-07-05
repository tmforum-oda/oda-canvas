from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Definition des Component-Objekts
class Component(BaseModel):
    id: int
    name: str
    description: str

# Speicher für die Component-Objekte
components = [
    {"id": 1, "name": "Komponente 1", "description": "Beschreibung 1"},
    {"id": 2, "name": "Komponente 2", "description": "Beschreibung 2"},
]

# GET /components
@app.get("/components/")
def read_components():
    return components

# GET /components/{id}
@app.get("/components/{id}")
def read_component(id: int):
    component = next((c for c in components if c["id"] == id), None)
    if component is None:
        raise HTTPException(status_code=404, detail="Komponente nicht gefunden")
    return component

# POST /components
@app.post("/components/")
def create_component(component: Component):
    components.append(component.dict())
    return component

# PUT /components/{id}
@app.put("/components/{id}")
def update_component(id: int, component: Component):
    existing_component = next((c for c in components if c["id"] == id), None)
    if existing_component is None:
        raise HTTPException(status_code=404, detail="Komponente nicht gefunden")
    existing_component["name"] = component.name
    existing_component["description"] = component.description
    return existing_component

# DELETE /components/{id}
@app.delete("/components/{id}")
def delete_component(id: int):
    component = next((c for c in components if c["id"] == id), None)
    if component is None:
        raise HTTPException(status_code=404, detail="Komponente nicht gefunden")
    components.remove(component)
    return {"message": "Komponente gelöscht"}

if __name__ == "__main__":
	import uvicorn
	uvicorn.run(app, host="0.0.0.0", port=8080)
