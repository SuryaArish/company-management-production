# Company Todo API - Python FastAPI

Python FastAPI application for company and task management using Firebase Firestore.

## Setup

1. Set up Firebase project and download service account key
2. Place the service account key file as `firebase-key.json` in the project root
3. Update `.env` file with your Firebase project ID
4. Install Python dependencies: `pip install -r requirements.txt`
5. Run the server: `python main.py` or `uvicorn main:app --host 0.0.0.0 --port 8080`

## API Endpoints

### Company APIs
- `GET /getall_companies` - Get all companies
- `GET /get_company/{id}` - Get company by ID
- `POST /create_company` - Create new company
- `PUT /update_company/{id}` - Update company
- `DELETE /delete_company/{id}` - Delete company

### Task APIs
- `GET /getall_tasks` - Get all tasks
- `GET /get_task/{id}` - Get task by ID
- `POST /create_task` - Create new task
- `PUT /update_task/{id}` - Update task
- `DELETE /delete_task/{id}` - Delete task

### Task Template APIs
- `GET /getall_templates` - Get all task templates
- `POST /create_template` - Create new task template
- `DELETE /delete_template/{id}` - Delete task template
- `POST /assign_template/{id}` - Assign template to companies

## Example Usage

```bash
# Create a company
curl -X POST http://localhost:8080/create_company \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Company",
    "EIN": "12-3456789",
    "startDate": "2024-01-01",
    "stateIncorporated": "CA",
    "contactPersonName": "John Doe",
    "contactPersonPhNumber": "555-1234",
    "address1": "123 Main St",
    "address2": "Suite 100",
    "city": "San Francisco",
    "state": "CA",
    "zip": "94105"
  }'

# Create a task
curl -X POST http://localhost:8080/create_task \
  -H "Content-Type: application/json" \
  -d '{
    "companyId": "company-uuid",
    "title": "Complete project",
    "description": "Finish the todo app",
    "completed": false
  }'

# Create a task template
curl -X POST http://localhost:8080/create_template \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "title": "Weekly Review",
    "description": "Review weekly progress"
  }'
```

## Dependencies

- **FastAPI**: Web framework
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation
- **httpx**: HTTP client for Firebase API
- **python-dotenv**: Environment variables
- **PyJWT**: JWT token handling

## Files Structure

- `main.py`: FastAPI application with all routes
- `models.py`: Pydantic models for data validation
- `handlers.py`: Business logic handlers
- `firebase.py`: Firebase Firestore integration
- `requirements.txt`: Python dependencies
- `.env`: Environment configuration