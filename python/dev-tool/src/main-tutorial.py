# Content Points
# * Simple Endpoint
# * Automatic Documentation
# * Data Validation (Path Parameters, Query Parameters, Request Body)
# * Query Parameters required or optional
# * Enumerated parameters
# * POST Endpoint with request body documentation & validation
# * Browser Cookies
# * Request Headers
# * Typed Response
# * Explicit Status Codes
# * Throw HTTP Errors
# * Background Tasks
# * Cross Origin Requests (CORS)

import time

from enum import Enum
from typing import List
from typing import Optional
from urllib import response

import uvicorn
from fastapi import Cookie, FastAPI, Header, status, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel, Field


class Notification(BaseModel):
    email: str
    notification_type: int


class Department(str, Enum):
    MATH = "math"
    ENGLISH = "english"
    CHEMISTRY = "chemistry"
    COMPUTER_SCIENCE = "computer_science"


class Employee(BaseModel):
    id: int = Field(description="Employee ID")
    department: Department = Field(
        description="The department the employee belongs to.",
    )
    age: int = Field(description="The age of the employee")
    gender: str = Field(max_length=1, description="The gender of the employee")


fake_employees_db = []

app = FastAPI(debug=True)

origins = [
    "http://localhost:5000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/status")
async def check_status():
    return "Hello World"


@app.get(
    "/employees/{employee_id}", response_model=Employee, status_code=status.HTTP_200_OK
)
async def get_employees(
    employee_id: int, age: int, department: Department, gender: str = None
):
    return [{"id": 1, "name": "Bob"}, {"id": 2, "name": "Mike"}]


@app.post("/employees", response_model=Employee, status_code=status.HTTP_201_CREATED)
async def create_employee(employee: Employee):
    print(employee)
    return employee


def send_notification(email: str):
    time.sleep(10)
    print(f"Sending email to {email}")


@app.post("/send_email")
async def send_email(
    background_tasks: BackgroundTasks,
    notification_payload: Notification,
    token: Optional[str] = Cookie(None),
    user_agent: Optional[str] = Header(None),
):
    if notification_payload.email in ["fake_email"]:
        raise HTTPException(status_code=400, detail="Fake email detected")

    background_tasks.add_task(send_notification, notification_payload.email)
    return {"cookie_received": token, "user_agent_from_header": user_agent}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)