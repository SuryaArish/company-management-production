from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from models import Company, Task, TaskTemplate, AssignData
import handlers
import firebase_admin
from firebase_admin import auth, credentials
from typing import Optional

load_dotenv()

# Initialize Firebase Admin SDK
try:
    firebase_admin.get_app()
except ValueError:
    import os
    import json
    
    # Try to use environment variables for Firebase credentials
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
    
    # Check if we have the required environment variables
    if all([firebase_creds["project_id"], firebase_creds["private_key"], firebase_creds["client_email"]]):
        cred = credentials.Certificate(firebase_creds)
    else:
        # Fallback to file if environment variables are not set
        cred = credentials.Certificate("firebase-key.json")
    
    firebase_admin.initialize_app(cred)

app = FastAPI()

async def get_user_id_from_token(request: Request):
    print(f"All headers received: {dict(request.headers)}")
    authorization = request.headers.get("Authorization") or request.headers.get("authorization")
    print(f"Authorization header found: {authorization is not None}")
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    try:
        # Remove 'Bearer ' prefix if present
        token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token.get('uid')
        print(f"Token validated successfully, user_id: {user_id}")
        return user_id
    except Exception as e:
        print(f"Token validation error: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

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
    return await handlers.get_company_by_id(user_id, company_id)

@app.post("/create_company")
async def create_company(company_data: Company, user_id: str = Depends(get_user_id_from_token)):
    print(f"Creating company for user: {user_id}")
    return await handlers.create_company(user_id, company_data)

@app.put("/update_company/{company_id}")
async def update_company(company_id: str, company_data: Company, user_id: str = Depends(get_user_id_from_token)):
    return await handlers.update_company(user_id, company_id, company_data)

@app.delete("/delete_company/{company_id}")
async def delete_company(company_id: str, user_id: str = Depends(get_user_id_from_token)):
    return await handlers.delete_company(user_id, company_id)

# Task API Routes
@app.get("/getall_tasks")
async def get_tasks(user_id: str = Depends(get_user_id_from_token)):
    return await handlers.get_tasks(user_id)

@app.get("/get_task/{task_id}")
async def get_task_by_id(task_id: str, user_id: str = Depends(get_user_id_from_token)):
    return await handlers.get_task_by_id(user_id, task_id)

@app.post("/create_task")
async def create_task(task_data: Task, user_id: str = Depends(get_user_id_from_token)):
    return await handlers.create_task(user_id, task_data)

@app.put("/update_task/{task_id}")
async def update_task(task_id: str, task_data: Task, user_id: str = Depends(get_user_id_from_token)):
    return await handlers.update_task(user_id, task_id, task_data)

@app.delete("/delete_task/{task_id}")
async def delete_task(task_id: str, user_id: str = Depends(get_user_id_from_token)):
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
    return await handlers.delete_template(user_id, template_id)

@app.post("/assign_template/{template_id}")
async def assign_template(template_id: str, assign_data: AssignData, user_id: str = Depends(get_user_id_from_token)):
    return await handlers.assign_template(user_id, template_id, assign_data)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

# ride it
# yad
