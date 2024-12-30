from fastapi import FastAPI
from app.routers import grading
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from app.db.session import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event: Create tables and seed data
    SQLModel.metadata.create_all(engine)
    yield

# Create FastAPI application
app = FastAPI(swagger_ui_parameters={"syntaxHighlight": True}, lifespan=lifespan)

# Enable CORS for all origins (use caution in production)
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers for grading
app.include_router(grading.router, prefix="/grading", tags=["/grading"])
