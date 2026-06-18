from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import engine, Base
from routers import *

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="<% app_name %>",
    description="<% app_description %>",
    version="<% version %>",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

<%% if enable_auth %%>
from auth import auth_router
app.include_router(auth_router, prefix="<% api_prefix %>")
<%% endif %%>

app.include_router(form1_router, prefix="<% api_prefix %>")

@app.get("/")
async def root():
    return {"message": "Welcome to <% app_name %> API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
