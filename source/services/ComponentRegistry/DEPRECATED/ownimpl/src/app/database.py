# from https://sqlmodel.tiangolo.com/tutorial/fastapi/simple-component-api/#install-fastapi
from sqlmodel import SQLModel, create_engine, Session

# import all sql model classes that create tables
from app.model import Component   # keep this import for create_all()


class LocalDatabase:    
    instance = None

    def __init__(self, sqlite_file_name):
        self.sqlite_file_name = sqlite_file_name
        self.sqlite_url = f"sqlite:///{sqlite_file_name}"
        self.engine = None
        
    @classmethod
    def create_instance(cls, sqlite_file_name):
        cls.instance = cls(sqlite_file_name)
        return cls.instance

    @classmethod
    def get_instance(cls):
        return cls.instance

    @staticmethod
    def get_instance_session():
        with Session(LocalDatabase.get_instance().get_engine()) as session:
            yield session    

    def startup(self):
        self.engine = create_engine(self.sqlite_url, echo=True, connect_args={"check_same_thread": False})
        [Component]  # not needed, just to fix unresolved imports
        (SQLModel.metadata).create_all(self.engine)

    def get_engine(self):
        return self.engine

    def shutdown(self):
        self.engine.dispose()
        self.engine = None

