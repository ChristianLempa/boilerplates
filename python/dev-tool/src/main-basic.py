from fastapi import FastAPI
from datetime import datetime
import redis

version = "1.0.0"
title = "FastAPI Container-based Code Example"
description = """
FastAPI Container-based example

## ITEMS

You can see **hit** counts and some stats

## USERS

You will be able to:

* **See hello-world**
* **See number of hits**
* **See Latest-hit**
"""
contact ="info@vmlab.be"

app = FastAPI(
    title = "FastAPI Container-based Code Example",
    description= description,
    version = "1.0.0",
    contact={
      "name": "VMLAB",
      "url": "https://vmlab.be",
      "email": "info@vmlab.be",
    },
)

r = redis.Redis(host="redis", port=6379)

@app.get("/")
def read_root():
    r.incr("hits")
    return {"Hello": "World!"}

@app.get("/hits")
def read_root():
    dt = datetime.now().strftime('%Y-%m-%d@%H:%M:%S.%f')
    r.incr("hits")
    r.set("latest_hit", dt) 
    print(dt)
    return {"Hits": r.get("hits")}

@app.get("/latest")
def read_root():
    return {"Latest Hit was": r.get("latest_hit")}
