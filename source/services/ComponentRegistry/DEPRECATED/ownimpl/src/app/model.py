# from https://sqlmodel.tiangolo.com/tutorial/fastapi/simple-component-api/#install-fastapi
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import JSON

# see https://sqlmodel.tiangolo.com/tutorial/fastapi/relationships/#why-arent-we-getting-more-data

    # ========== #
    #  COMPONENT #
    # ========== #


class ComponentBase(SQLModel):
    name: str = Field(index=True)
    owner: str
    labels: dict[str, str] = Field(default={"key": "value"}, sa_column=Column(JSON))


class Component(ComponentBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    
    exposed_apis: list["ExposedAPI"] = Relationship(back_populates="component")


class ComponentPublic(ComponentBase):
    id: int
    

class ComponentCreate(ComponentBase):
    pass


class ComponentUpdate(SQLModel):
    labels: dict[str, str|None] | None = None


    # ============ #
    #  EXPOSED API #
    # ============ #


class ExposedAPIBase(SQLModel):
    specification_url: str = Field(index=True)
    specification_version: str
    name: str
    description: str | None
    apiType: str
    ready: bool
    url: str
    
    component_id: int | None = Field(default=None, foreign_key="component.id")


class ExposedAPI(ExposedAPIBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    component: Component | None = Relationship(back_populates="exposed_apis")


class ExposedAPIPublic(ExposedAPIBase):
    id: int


class ExposedAPICreate(ExposedAPIBase):
    pass


class ExposedAPIUpdate(SQLModel):
    ready: bool | None = None
    url: str | None = None



    # ============== #
    #  RELATIONSHIPS #
    # ============== #


class ExposedAPIPublicWithComponent(ExposedAPIPublic):
    component: ComponentPublic | None = None


class ComponentPublicWithExposedAPIs(ComponentPublic):
    exposed_apis: list[ExposedAPIPublic] = []


