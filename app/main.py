from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from dotenv import load_dotenv
from app.models import Company, Task, TaskTemplate, AssignData, User
from app.api import handlers
import firebase_admin
from firebase_admin import auth, credentials
from typing import Optional
import traceback
import time

load_dotenv("config/.env")

# Initialize Firebase Admin SDK
try:
    firebase_admin.get_app()
except ValueError:
    import os
    firebase_creds = {
        "type": "service_account",
        "project_id": os.getenv("FIREBASE_PROJECT_ID"),
        "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
        "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace('\\n', '\n'),
        "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
        "client_id": os.getenv("FIREBASE_CLIENT_ID"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{os.getenv('FIREBASE_CLIENT_EMAIL')}"
    }
    
    if all([firebase_creds["project_id"], firebase_creds["private_key"], firebase_creds["client_email"]]):
        cred = credentials.Certificate(firebase_creds)
    else:
        cred = credentials.Certificate("config/firebase-key.json")
    
    firebase_admin.initialize_app(cred)

app = FastAPI(title="Company Management API", version="1.0.0")

# Token cache for performance
_token_cache = {}
_cache_expiry = {}

# Simplified middleware
class FastContentTypeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if content_type and not content_type.startswith("application/json"):
                return JSONResponse(
                    status_code=422,
                    content={"detail": "Content-Type must be application/json"}
                )
        response = await call_next(request)
        return response

app.add_middleware(FastContentTypeMiddleware)

# Simplified exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation error", "errors": [str(error) for error in exc.errors()]}
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Optimized token validation with caching
async def get_user_id_from_token(request: Request):
    authorization = request.headers.get("Authorization") or request.headers.get("authorization")
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    
    # Check cache first
    now = int(time.time())
    if token in _token_cache and now < _cache_expiry.get(token, 0):
        return _token_cache[token]
    
    try:
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token.get('uid')
        
        # Cache for 2 minutes
        _token_cache[token] = user_id
        _cache_expiry[token] = now + 120
        
        return user_id
    except Exception as e:
        error_msg = str(e).lower()
        if "expired" in error_msg:
            raise HTTPException(status_code=401, detail="Token expired")
        elif "revoked" in error_msg:
            raise HTTPException(status_code=401, detail="Token revoked")
        elif "invalid" in error_msg:
            raise HTTPException(status_code=401, detail="Invalid token")
        else:
            raise HTTPException(status_code=401, detail="Authentication failed")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Company API Routes
@app.get("/getall_companies")
async def get_companies(user_id: str = Depends(get_user_id_from_token)):
    return await handlers.get_companies(user_id)

@app.get("/get_company/{company_id}")
async def get_company_by_id(company_id: str, user_id: str = Depends(get_user_id_from_token)):
    if "../" in company_id or "..\\" in company_id or "<script>" in company_id.lower():
        raise HTTPException(status_code=404, detail="Not found")
    return await handlers.get_company_by_id(user_id, company_id)

@app.post("/create_company")
async def create_company(company_data: Company, user_id: str = Depends(get_user_id_from_token)):
    return await handlers.create_company(user_id, company_data)

@app.put("/update_company/{company_id}")
async def update_company(company_id: str, company_data: Company, user_id: str = Depends(get_user_id_from_token)):
    return await handlers.update_company(user_id, company_id, company_data)

@app.delete("/delete_company/{company_id}")
async def delete_company(company_id: str, user_id: str = Depends(get_user_id_from_token)):
    if "<script>" in company_id.lower():
        raise HTTPException(status_code=404, detail="Not found")
    return await handlers.delete_company(user_id, company_id)

# Task API Routes
@app.get("/getall_tasks")
async def get_tasks(user_id: str = Depends(get_user_id_from_token)):
    return await handlers.get_tasks(user_id)

@app.get("/get_task/{task_id}")
async def get_task_by_id(task_id: str, user_id: str = Depends(get_user_id_from_token)):
    if "../" in task_id or "..\\" in task_id or "<script>" in task_id.lower():
        raise HTTPException(status_code=404, detail="Not found")
    return await handlers.get_task_by_id(user_id, task_id)

@app.post("/create_task")
async def create_task(task_data: Task, user_id: str = Depends(get_user_id_from_token)):
    return await handlers.create_task(user_id, task_data)

@app.put("/update_task/{task_id}")
async def update_task(task_id: str, task_data: Task, user_id: str = Depends(get_user_id_from_token)):
    return await handlers.update_task(user_id, task_id, task_data)

@app.delete("/delete_task/{task_id}")
async def delete_task(task_id: str, user_id: str = Depends(get_user_id_from_token)):
    if "<script>" in task_id.lower():
        raise HTTPException(status_code=404, detail="Not found")
    return await handlers.delete_task(user_id, task_id)

# Template API Routes
@app.get("/getall_templates")
async def get_templates(user_id: str = Depends(get_user_id_from_token)):
    return await handlers.get_templates(user_id)

@app.post("/create_template")
async def create_template(template_data: TaskTemplate, user_id: str = Depends(get_user_id_from_token)):
    return await handlers.create_template(user_id, template_data)

@app.delete("/delete_template/{template_id}")
async def delete_template(template_id: str, user_id: str = Depends(get_user_id_from_token)):
    if "<script>" in template_id.lower():
        raise HTTPException(status_code=404, detail="Not found")
    return await handlers.delete_template(user_id, template_id)

@app.post("/assign_template/{template_id}")
async def assign_template(template_id: str, assign_data: AssignData, user_id: str = Depends(get_user_id_from_token)):
    return await handlers.assign_template(user_id, template_id, assign_data)

# User Authentication Routes
@app.post("/create_user")
async def create_user(user_data: User):
    return await handlers.create_user_handler(user_data)

@app.post("/login_user")
async def login_user(user_data: User):
    return await handlers.login_user_handler(user_data)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8080,
        access_log=False,
        workers=1
    )
