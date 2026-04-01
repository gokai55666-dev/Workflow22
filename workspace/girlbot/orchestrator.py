from fastapi import FastAPI
import asyncio
from comfy_client import Comfy
from workflow import build

app=FastAPI()
q=asyncio.Queue()
c=Comfy()
res={}

@app.post("/gen")
async def gen(d:dict):
 j=str(id(d)); await q.put((j,d)); return {"job":j}

@app.get("/res/{j}")
async def get(j:str): return res.get(j,{"status":"wait"})

async def worker():
 while 1:
  j,d=await q.get()
  pid=await c.gen(build(d["prompt"]))
  while 1:
   r=await c.res(pid)
   if pid in r:
    try:
     f=r[pid]["outputs"]["7"]["images"][0]["filename"]
     res[j]={"status":"done","file":f}; break
    except: pass
   await asyncio.sleep(2)

@app.on_event("startup")
async def start(): asyncio.create_task(worker())