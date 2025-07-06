# from https://sqlmodel.tiangolo.com/tutorial/fastapi/simple-component-api/#install-fastapi
from sqlmodel import Field, SQLModel
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

