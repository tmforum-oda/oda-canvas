# from https://fastapi.tiangolo.com/tutorial/bigger-applications/#the-main-fastapi
from fastapi import FastAPI
from contextlib import asynccontextmanager
import os

from app.database import LocalDatabase
from app.routers import components, exposedapis


DATABASE_FILE = os.getenv("DATABASE_FILE", "data/database.db")
print(f"DATABASE_FILE={DATABASE_FILE}")

db = LocalDatabase.create_instance(DATABASE_FILE)

@asynccontextmanager
async def lifespan(app: FastAPI):
    db.startup()
    yield
    db.shutdown()

app = FastAPI(lifespan=lifespan)

app.include_router(components.router)
app.include_router(exposedapis.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
