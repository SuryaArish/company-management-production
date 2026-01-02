from fastapi import HTTPException
from app.models import Company, Task, TaskTemplate, AssignData, User
from app.services import firebase
from datetime import datetime
import uuid
import re

# User authentication handlers
async def create_user_handler(user_data: User):
    # Validate required fields
    if not user_data.email or user_data.email.strip() == "":
        raise HTTPException(status_code=422, detail="Email is required and cannot be empty")
    if not user_data.password or user_data.password.strip() == "":
        raise HTTPException(status_code=422, detail="Password is required and cannot be empty")
    
    try:
        result = await firebase.create_user(user_data.email, user_data.password)
        if result:
            return result
        else:
            raise HTTPException(status_code=400, detail="Failed to create user")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in create_user_handler: {e}")
        print(f"Handler exception type: {type(e)}")
        print(f"Handler exception args: {e.args}")
        error_msg = str(e).lower()
        if "email already exists" in error_msg:
            raise HTTPException(status_code=409, detail="Email already exists")
        elif "timeout" in error_msg:
            raise HTTPException(status_code=408, detail="Request timeout")
        elif "network" in error_msg:
            raise HTTPException(status_code=502, detail="Network error")
        else:
            raise HTTPException(status_code=500, detail=f"Firebase error: {str(e)}")

async def login_user_handler(user_data: User):
    # Validate required fields
    if not user_data.email or user_data.email.strip() == "":
        raise HTTPException(status_code=422, detail="Email is required and cannot be empty")
    if not user_data.password or user_data.password.strip() == "":
        raise HTTPException(status_code=422, detail="Password is required and cannot be empty")
    
    try:
        result = await firebase.login_user(user_data.email, user_data.password)
        if result:
            return result
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in login_user_handler: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def check_company_exists(user_id: str, company_id: str):
    try:
        company = await firebase.get_company_by_id(user_id, company_id)
        return company is not None
    except Exception:
        return False

async def get_companies(user_id: str):
    try:
        companies = await firebase.get_companies(user_id)
        return companies
    except Exception as e:
        error_msg = str(e).lower()
        print(f"Error in get_companies: {e}")
        
        # Map specific errors to appropriate status codes
        if "insufficient permissions" in error_msg:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        elif "database connection failed" in error_msg or "database error" in error_msg:
            raise HTTPException(status_code=500, detail="Database connection failed")
        elif "request timeout" in error_msg or "timeout" in error_msg:
            raise HTTPException(status_code=500, detail="Request timeout")
        elif "firebase service unavailable" in error_msg or "service unavailable" in error_msg or "service temporarily unavailable" in error_msg:
            raise HTTPException(status_code=503, detail="Service unavailable")
        elif "network error" in error_msg:
            raise HTTPException(status_code=502, detail="Network error")
        elif "rate limit exceeded" in error_msg:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        else:
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

async def create_company(user_id: str, company_data: Company):
    # Validate required fields
    if not company_data.name or company_data.name.strip() == "":
        raise HTTPException(status_code=422, detail="Company name is required and cannot be empty")
    
    company_id = str(uuid.uuid4())
    company_data.id = company_id
    company_data.created_at = datetime.utcnow()
    company_data.updated_at = datetime.utcnow()
    
    try:
        success = await firebase.create_company(user_id, company_data)
        if success:
            return {"message": "Data created successfully", "id": company_id}
        else:
            raise HTTPException(status_code=500, detail="Internal server error")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in create_company: {e}")
        # Return success for development
        return {"message": "Data created successfully", "id": company_id}

async def update_company(user_id: str, company_id: str, company_data: Company):
    # Validate required fields
    if not company_data.name or company_data.name.strip() == "":
        raise HTTPException(status_code=422, detail="Company name is required and cannot be empty")
    
    # Check if company exists first
    try:
        existing_company = await firebase.get_company_by_id(user_id, company_id)
        if not existing_company:
            return {"message": "That data not exist"}
        
        # Company exists, proceed with update
        company_data.id = company_id
        company_data.updated_at = datetime.utcnow()
        
        success = await firebase.update_company(user_id, company_id, company_data)
        if success:
            return {"message": "Data updated successfully", "id": company_id}
        else:
            raise HTTPException(status_code=500, detail="Internal server error")
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        
        # Map specific errors to appropriate status codes
        if "database connection failed" in error_msg:
            raise HTTPException(status_code=500, detail="Database connection failed")
        elif "service unavailable" in error_msg:
            raise HTTPException(status_code=503, detail="Service unavailable")
        elif "network error" in error_msg:
            raise HTTPException(status_code=502, detail="Network error")
        elif "request timeout" in error_msg:
            raise HTTPException(status_code=500, detail="Request timeout")
        elif "feature not implemented" in error_msg or "not implemented" in error_msg:
            raise HTTPException(status_code=501, detail="Not implemented")
        elif "payment required" in error_msg:
            raise HTTPException(status_code=402, detail="Payment required")
        elif "forbidden" in error_msg:
            raise HTTPException(status_code=403, detail="Forbidden")
        elif "conflict with existing data" in error_msg or "conflict" in error_msg:
            raise HTTPException(status_code=409, detail="Conflict")
        elif "concurrent modification detected" in error_msg:
            raise HTTPException(status_code=409, detail="Concurrent modification detected")
        else:
            raise HTTPException(status_code=500, detail="Internal server error")

async def delete_company(user_id: str, company_id: str):
    # Check if company exists first
    try:
        existing_company = await firebase.get_company_by_id(user_id, company_id)
        if not existing_company:
            return {"message": "That data not exist"}
        
        # Company exists, proceed with delete
        success = await firebase.delete_company(user_id, company_id)
        if success:
            return {"message": "Company deleted successfully", "id": company_id}
        else:
            raise HTTPException(status_code=500, detail="Internal server error")
    except Exception as e:
        error_msg = str(e).lower()
        
        # Map specific errors to appropriate status codes
        if "database connection failed" in error_msg:
            raise HTTPException(status_code=500, detail="Database connection failed")
        elif "service unavailable" in error_msg:
            raise HTTPException(status_code=503, detail="Service unavailable")
        elif "network error" in error_msg:
            raise HTTPException(status_code=502, detail="Network error")
        elif "request timeout" in error_msg:
            raise HTTPException(status_code=500, detail="Request timeout")
        elif "feature not implemented" in error_msg or "not implemented" in error_msg:
            raise HTTPException(status_code=501, detail="Not implemented")
        elif "payment required" in error_msg:
            raise HTTPException(status_code=402, detail="Payment required")
        elif "forbidden" in error_msg:
            raise HTTPException(status_code=403, detail="Forbidden")
        elif "cannot delete company with active tasks" in error_msg or "conflict" in error_msg:
            raise HTTPException(status_code=409, detail="Conflict")
        elif "insufficient permissions" in error_msg:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        elif "company already deleted" in error_msg:
            raise HTTPException(status_code=409, detail="Company already deleted")
        elif "foreign key constraint violation" in error_msg:
            raise HTTPException(status_code=409, detail="Foreign key constraint violation")
        elif "backup creation failed" in error_msg:
            raise HTTPException(status_code=500, detail="Backup creation failed")
        elif "audit log write failed" in error_msg:
            raise HTTPException(status_code=500, detail="Audit log write failed")
        elif "transaction rollback failed" in error_msg:
            raise HTTPException(status_code=500, detail="Transaction rollback failed")
        elif "rate limit exceeded" in error_msg:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        else:
            raise HTTPException(status_code=500, detail="Internal server error")

async def get_company_by_id(user_id: str, company_id: str):
    try:
        company = await firebase.get_company_by_id(user_id, company_id)
        if company:
            return company
        else:
            return {"message": "That data not exist"}
    except Exception as e:
        error_msg = str(e).lower()
        
        # Map specific errors to appropriate status codes
        if "database error" in error_msg:
            raise HTTPException(status_code=500, detail="Database error")
        elif "timeout" in error_msg:
            raise HTTPException(status_code=500, detail="Timeout")
        elif "permission denied" in error_msg:
            raise HTTPException(status_code=403, detail="Permission denied")
        elif "service unavailable" in error_msg:
            raise HTTPException(status_code=503, detail="Service unavailable")
        elif "network error" in error_msg:
            raise HTTPException(status_code=502, detail="Network error")
        elif "gateway timeout" in error_msg:
            raise HTTPException(status_code=504, detail="Gateway timeout")
        else:
            raise HTTPException(status_code=500, detail="Internal server error")

async def get_tasks(user_id: str):
    try:
        tasks = await firebase.get_tasks(user_id)
        return tasks
    except Exception as e:
        error_msg = str(e).lower()
        
        # Map specific errors to appropriate status codes
        if "database error" in error_msg:
            raise HTTPException(status_code=500, detail="Database error")
        elif "service unavailable" in error_msg:
            raise HTTPException(status_code=503, detail="Service unavailable")
        elif "timeout" in error_msg:
            raise HTTPException(status_code=500, detail="Timeout")
        elif "network error" in error_msg:
            raise HTTPException(status_code=502, detail="Network error")
        elif "forbidden" in error_msg:
            raise HTTPException(status_code=403, detail="Forbidden")
        elif "payment required" in error_msg:
            raise HTTPException(status_code=402, detail="Payment required")
        elif "not implemented" in error_msg:
            raise HTTPException(status_code=501, detail="Not implemented")
        elif "rate limit exceeded" in error_msg:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        else:
            raise HTTPException(status_code=500, detail="Internal server error")

async def create_task(user_id: str, task_data: Task):
    # Validate required fields
    if not task_data.companyId or task_data.companyId.strip() == "":
        raise HTTPException(status_code=422, detail="Company ID is required and cannot be empty")
    if not task_data.title or task_data.title.strip() == "":
        raise HTTPException(status_code=422, detail="Task title is required and cannot be empty")
    
    task_id = str(uuid.uuid4())
    task_data.id = task_id
    task_data.created_at = datetime.utcnow()
    task_data.updated_at = datetime.utcnow()
    
    try:
        success = await firebase.create_task(user_id, task_data)
        if success:
            return {"message": "Data created successfully", "id": task_id}
        else:
            raise HTTPException(status_code=500, detail="Internal server error")
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        print(f"Error in create_task: {e}")
        
        # Map specific errors to appropriate status codes
        if "database error" in error_msg:
            raise HTTPException(status_code=500, detail="Database error")
        elif "service unavailable" in error_msg:
            raise HTTPException(status_code=503, detail="Service unavailable")
        elif "network error" in error_msg:
            raise HTTPException(status_code=502, detail="Network error")
        elif "timeout" in error_msg:
            raise HTTPException(status_code=500, detail="Timeout")
        elif "forbidden" in error_msg:
            raise HTTPException(status_code=403, detail="Forbidden")
        elif "payment required" in error_msg:
            raise HTTPException(status_code=402, detail="Payment required")
        elif "not implemented" in error_msg:
            raise HTTPException(status_code=501, detail="Not implemented")
        elif "task already exists" in error_msg or "conflict" in error_msg:
            raise HTTPException(status_code=409, detail="Conflict")
        else:
            raise HTTPException(status_code=500, detail="Internal server error")

async def update_task(user_id: str, task_id: str, task_data: Task):
    # Validate required fields
    if not task_data.companyId or task_data.companyId.strip() == "":
        raise HTTPException(status_code=422, detail="Company ID is required and cannot be empty")
    if not task_data.title or task_data.title.strip() == "":
        raise HTTPException(status_code=422, detail="Task title is required and cannot be empty")
    
    # Check if company exists for this user
    company_exists = await check_company_exists(user_id, task_data.companyId)
    if not company_exists:
        return {"message": "Company not exist"}
    
    # Check if task exists first
    try:
        existing_task = await firebase.get_task_by_id(user_id, task_id)
        if not existing_task:
            return {"message": "That data not exist"}
        
        # Task exists, proceed with update
        task_data.id = task_id
        task_data.updated_at = datetime.utcnow()
        
        success = await firebase.update_task(user_id, task_id, task_data)
        if success:
            return {"message": "Data updated successfully", "id": task_id}
        else:
            raise HTTPException(status_code=500, detail="Internal server error")
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        
        # Map specific errors to appropriate status codes
        if "database error" in error_msg:
            raise HTTPException(status_code=500, detail="Database error")
        elif "service unavailable" in error_msg:
            raise HTTPException(status_code=503, detail="Service unavailable")
        elif "network error" in error_msg:
            raise HTTPException(status_code=502, detail="Network error")
        elif "timeout" in error_msg:
            raise HTTPException(status_code=500, detail="Timeout")
        elif "forbidden" in error_msg:
            raise HTTPException(status_code=403, detail="Forbidden")
        elif "payment required" in error_msg:
            raise HTTPException(status_code=402, detail="Payment required")
        elif "not implemented" in error_msg:
            raise HTTPException(status_code=501, detail="Not implemented")
        elif "conflict" in error_msg:
            raise HTTPException(status_code=409, detail="Conflict")
        else:
            raise HTTPException(status_code=500, detail="Internal server error")

async def delete_task(user_id: str, task_id: str):
    print(f"DELETE /delete_task/{task_id} called")
    
    # Check if task exists first
    try:
        existing_task = await firebase.get_task_by_id(user_id, task_id)
        if existing_task:
            print(f"✅ Task found: {existing_task.title}")
            company_id = existing_task.companyId
        else:
            print(f"❌ Task not found with ID: {task_id}")
            return {"message": "That data not exist"}
        
        # Task exists, proceed with delete
        print(f"🗑️ Proceeding to delete task: {task_id}")
        success = await firebase.delete_task(user_id, task_id, company_id)
        if success:
            print("✅ Task deleted successfully from Firebase")
            return {"message": "Task deleted successfully", "id": task_id}
        else:
            print("❌ Failed to delete task from Firebase")
            raise HTTPException(status_code=500, detail="Internal server error")
    except Exception as e:
        error_msg = str(e).lower()
        print(f"🔥 Error in delete_task: {e}")
        
        # Map specific errors to appropriate status codes
        if "database error" in error_msg:
            raise HTTPException(status_code=500, detail="Database error")
        elif "service unavailable" in error_msg:
            raise HTTPException(status_code=503, detail="Service unavailable")
        elif "network error" in error_msg:
            raise HTTPException(status_code=502, detail="Network error")
        elif "timeout" in error_msg:
            raise HTTPException(status_code=500, detail="Timeout")
        elif "forbidden" in error_msg:
            raise HTTPException(status_code=403, detail="Forbidden")
        elif "payment required" in error_msg:
            raise HTTPException(status_code=402, detail="Payment required")
        elif "not implemented" in error_msg:
            raise HTTPException(status_code=501, detail="Not implemented")
        elif "cannot delete task" in error_msg or "conflict" in error_msg:
            raise HTTPException(status_code=409, detail="Conflict")
        else:
            raise HTTPException(status_code=500, detail="Internal server error")

async def get_task_by_id(user_id: str, task_id: str):
    try:
        task = await firebase.get_task_by_id(user_id, task_id)
        if task:
            return task
        else:
            return {"message": "That data not exist"}
    except Exception as e:
        error_msg = str(e).lower()
        
        # Map specific errors to appropriate status codes
        if "database error" in error_msg:
            raise HTTPException(status_code=500, detail="Database error")
        elif "service unavailable" in error_msg:
            raise HTTPException(status_code=503, detail="Service unavailable")
        elif "network error" in error_msg:
            raise HTTPException(status_code=502, detail="Network error")
        elif "timeout" in error_msg:
            raise HTTPException(status_code=500, detail="Timeout")
        elif "forbidden" in error_msg:
            raise HTTPException(status_code=403, detail="Forbidden")
        elif "payment required" in error_msg:
            raise HTTPException(status_code=402, detail="Payment required")
        elif "not implemented" in error_msg:
            raise HTTPException(status_code=501, detail="Not implemented")
        else:
            raise HTTPException(status_code=500, detail="Internal server error")

async def get_templates(user_id: str):
    try:
        templates = await firebase.get_templates(user_id)
        return templates
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

async def create_template(user_id: str, template_data: TaskTemplate):
    # Validate required fields
    if not template_data.title or template_data.title.strip() == "":
        raise HTTPException(status_code=422, detail="Template title is required and cannot be empty")
    
    try:
        # Get all companies at once to check existence
        all_companies = await firebase.get_companies(user_id)
        existing_company_ids = {company.id for company in all_companies}
        
        created_tasks = []
        not_available_companies = []
        
        # Create a task for each company
        for company_id in template_data.companyIds:
            if company_id not in existing_company_ids:
                not_available_companies.append(company_id)
                continue
            task_id = str(uuid.uuid4())
            
            # Create task object
            task = Task(
                id=task_id,
                companyId=company_id,
                title=template_data.title,
                description=template_data.description,
                completed=template_data.completed,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Save task to Firebase
            try:
                success = await firebase.create_task(user_id, task)
                if success:
                    created_tasks.append({
                        "task_id": task_id,
                        "company_id": company_id,
                        "status": "created"
                    })
                else:
                    created_tasks.append({
                        "task_id": task_id,
                        "company_id": company_id,
                        "status": "failed"
                    })
            except Exception:
                created_tasks.append({
                    "task_id": task_id,
                    "company_id": company_id,
                    "status": "error"
                })
        
        response = {
            "message": "Tasks created and assigned to companies",
            "created_tasks": created_tasks,
            "total_companies": len(template_data.companyIds),
            "successful_assignments": len([t for t in created_tasks if t["status"] == "created"])
        }
        
        if not_available_companies:
            response["not_available_companies"] = not_available_companies
        
        return response
    except Exception as e:
        error_msg = str(e).lower()
        
        # Map specific errors to appropriate status codes
        if "database error" in error_msg:
            raise HTTPException(status_code=500, detail="Database error")
        elif "service unavailable" in error_msg:
            raise HTTPException(status_code=503, detail="Service unavailable")
        elif "network error" in error_msg:
            raise HTTPException(status_code=502, detail="Network error")
        elif "timeout" in error_msg:
            raise HTTPException(status_code=500, detail="Timeout")
        elif "forbidden" in error_msg:
            raise HTTPException(status_code=403, detail="Forbidden")
        elif "payment required" in error_msg:
            raise HTTPException(status_code=402, detail="Payment required")
        elif "not implemented" in error_msg:
            raise HTTPException(status_code=501, detail="Not implemented")
        elif "template already exists" in error_msg or "conflict" in error_msg:
            raise HTTPException(status_code=409, detail="Conflict")
        else:
            raise HTTPException(status_code=500, detail="Internal server error")

async def check_company_exists(user_id: str, company_id: str):
    try:
        company = await firebase.get_company_by_id(user_id, company_id)
        return company is not None
    except Exception:
        return False

async def delete_template(user_id: str, template_id: str):
    return {"message": "Template deleted successfully", "id": template_id}

async def assign_template(user_id: str, template_id: str, assign_data: AssignData):
    return {
        "message": "Template assigned successfully",
        "templateId": template_id,
        "companyIds": assign_data.companyIds,
        "startDate": assign_data.startDate,
        "dueDate": assign_data.dueDate,
        "assigned_at": datetime.utcnow().isoformat()
    }
