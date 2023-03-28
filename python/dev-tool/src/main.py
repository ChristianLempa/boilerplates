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

## App defenition
version = "1.0.0"
title = "FastAPI Container-based Code Example"
description = """
FastAPI Container-based example

## ITEMS

You can see **hit** counts and some stats

## USERS

You will be able to:

* **See status**
* **Get employees by ID**
* **Post employes by Json**
"""
contact ="info@vmlab.be"

## end Defenition
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
    name: str = Field(max_length=40, description="Name of the employee")
    department: Department = Field(
        description="The department the employee belongs to.",
    )
    age: int = Field(description="Age of the employee")
    gender: str = Field(max_length=1, description="Gender of the employee")

employees_dB = redis.Redis(host="redis", port=6379)
e = employees_dB.set[{"id": 1, "name": "Bob", "department": "math", "age": 49, "gender": "m"}, {"id": 2, "name": "Mike", "department": "chemistry", "age": 50, "gender": "m"}, {"id": 3, "name": "Elise", "department": "english", "age": 51, "gender": "f"}]

app = FastAPI(
    title = "FastAPI Container-based Code Example",
    description= description,
    version = "1.0.0",
    contact={
      "name": "VMLAB",
      "url": "https://vmlab.be",
      "email": "info@vmlab.be",
    },
    debug=True
)

#origins = [
#    "http://localhost:5000",
#]
#app.add_middleware(
#    CORSMiddleware,
#    allow_origins=origins,
#    allow_credentials=True,
#    allow_methods=["*"],
#    allow_headers=["*"],
#)


@app.get("/status")
async def check_status():
    return "Healthy"


@app.get(
    "/employees/{employee_id}", response_model=Employee, status_code=status.HTTP_200_OK
)
async def get_employees(
    employee_id: int, department: str = None, age: int = None, gender: str = None
):
    
    return fake_employees_db(employee_id)
    
#    [{"id": 1, "department": "math", "age": "49", "gender": "m"}]
#     {"id": 2, "department": "math", "age": "49""name": "Mike","gender": "male"},
#     {"id": 3, "department": "math", "name": "Elise","gender": "female"}]


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
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=True)