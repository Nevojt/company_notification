
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine
from .routers import notification
from app import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    docs_url="/docs",
    title="Notification API",
    description="Notification API",
    version="0.0.1",
)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(notification.router)