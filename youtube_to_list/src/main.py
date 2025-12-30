from fastapi import FastAPI
from .api.v1.endpoints import youtube, recipes
from .database import engine, Base

def create_tables_on_startup():
    """
    Creates database tables if they don't exist.
    """
    Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    create_tables_on_startup()

app.include_router(youtube.router, prefix="/api/v1/youtube", tags=["youtube"])
app.include_router(recipes.router, prefix="/api/v1/recipes", tags=["recipes"])

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}