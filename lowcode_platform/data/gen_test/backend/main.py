from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import engine, Base
from routers import *

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="测试应用",
    description="测试生成的应用",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from auth import auth_router
app.include_router(auth_router, prefix="/api/v1")


app.include_router(form1_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to 测试应用 API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}