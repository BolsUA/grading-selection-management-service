import os
from fastapi import FastAPI, Depends
from app.routers import grading
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlmodel import SQLModel, select
from app.db.session import engine, get_db
from app.models.models import Student

DUMMY_STUDENTS = [
    {"id": 1, "name": "Alice", "email": "z3uzikssmurf@gmail.com"},
    {"id": 2, "name": "Bob", "email": "henriquecc2012@gmail.com"},
    {"id": 3, "name": "Charlie", "email": "hcoelho@ua.pt"}
]

def seed_students(db: Session):
    existing_students = db.execute(select(Student)).scalars().all()
    if not existing_students:
        for student in DUMMY_STUDENTS:
            db.add(Student(**student))
        db.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event: Create tables and seed data
    SQLModel.metadata.create_all(engine)
    db = next(get_db())
    seed_students(db)
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
