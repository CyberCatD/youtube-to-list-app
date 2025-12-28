from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from .api.v1.endpoints import youtube, cards
from .database import engine, Base

def create_tables_on_startup():
    """
    Creates database tables if they don't exist.
    """
    Base.metadata.create_all(bind=engine)

app = FastAPI()

templates = Jinja2Templates(directory="src/templates")

@app.on_event("startup")
async def startup_event():
    create_tables_on_startup()

app.include_router(youtube.router, prefix="/api/v1/youtube", tags=["youtube"])
app.include_router(cards.router, prefix="/api/v1/cards", tags=["cards"])

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse, tags=["frontend"])
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})