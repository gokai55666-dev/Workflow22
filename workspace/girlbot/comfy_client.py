import aiohttp

class Comfy:
 def __init__(s,u="http://localhost:8188"): s.u=u
 async def gen(s,w):
  async with aiohttp.ClientSession() as c:
   async with c.post(f"{s.u}/prompt",json={"prompt":w}) as r:
    return (await r.json())["prompt_id"]
 async def res(s,p):
  async with aiohttp.ClientSession() as c:
   async with c.get(f"{s.u}/history/{p}") as r:
    return await r.json()