# Running the Application

## Local Development

### Quick Start

```bash
# From the task-management-api directory
python src/app.py
```

The application will start on `http://localhost:8000`

### Using Uvicorn with Hot Reload

```bash
# From the task-management-api directory
uvicorn src.app:app --reload --port 8000

# Or specify host as well
uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload
```

### Run Tests

```bash
# From the task-management-api directory
pytest test_app.py -v
```

## API Documentation

Once running, access:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Example Requests

### Health Check
```bash
curl http://localhost:8000/health
```

### Create a Task
```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Implement feature",
    "category": "development",
    "priority": "high"
  }'
```

### Get All Tasks
```bash
curl http://localhost:8000/tasks
```

### Get Statistics
```bash
curl http://localhost:8000/tasks/stats/summary
```

## Application Features

- Full CRUD operations for tasks
- Advanced filtering by status, priority, category, assignee, tags
- Sorting and pagination support
- Task dependencies and relationships
- Background job processing
- Analytics and statistics endpoints
- Bulk operations support

## Technology Stack

- **FastAPI**: Modern async web framework
- **Pydantic**: Data validation
- **Uvicorn**: ASGI server
- **pytest**: Testing framework