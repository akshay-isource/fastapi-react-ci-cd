from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Hello from FastAPI 🚀"}


@app.get("/hi")
def say_hi():
    return {"message": "Hi Akshay 👋"}


@app.get("/echo/{name}")
def echo(name: str):
    return {"message": f"Hello {name}"}
