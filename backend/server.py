import uvicorn
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "goon"}

if __name__ == "__main__":
    uvicorn.run("server:app")
