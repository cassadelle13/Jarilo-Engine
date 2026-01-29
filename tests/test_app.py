from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/test")
def test_endpoint(data: dict):
    return {"received": data}