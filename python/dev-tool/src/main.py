from fastapi import FastAPI
from datetime import datetime
import redis

app = FastAPI()
r = redis.Redis(host="redis", port=6379)

@app.get("/")
def read_root():
    return {"Hello": "World1234"}

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
