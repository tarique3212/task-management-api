"""
Unit tests for the Task Management API
"""
import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import pytest
import pytest_asyncio
from httpx import AsyncClient
from app import app


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check endpoint"""
    response = await client.get('/health')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'
    assert 'timestamp' in data
    assert 'version' in data
    assert 'total_tasks' in data


@pytest.mark.asyncio
async def test_create_task(client):
    """Test task creation"""
    response = await client.post('/tasks', json={
        'title': 'Test Task',
        'description': 'Test Description',
        'category': 'development',
        'priority': 'high',
        'tags': ['test', 'api']
    })
    assert response.status_code == 201
    data = response.json()
    assert data['title'] == 'Test Task'
    assert data['status'] == 'pending'
    assert data['priority'] == 'high'
    assert 'checksum' in data


@pytest.mark.asyncio
async def test_create_task_missing_title(client):
    """Test task creation without required fields"""
    response = await client.post('/tasks', json={
        'description': 'Test Description'
    })
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_create_task_invalid_priority(client):
    """Test task creation with invalid priority"""
    response = await client.post('/tasks', json={
        'title': 'Test Task',
        'category': 'development',
        'priority': 'invalid_priority'
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_tasks(client):
    """Test getting all tasks"""
    # Create a task first
    await client.post('/tasks', json={
        'title': 'Task 1',
        'category': 'testing'
    })
    
    response = await client.get('/tasks')
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_tasks_with_filters(client):
    """Test getting tasks with filters"""
    # Create tasks with different priorities
    await client.post('/tasks', json={
        'title': 'High Priority Task',
        'category': 'development',
        'priority': 'high'
    })
    await client.post('/tasks', json={
        'title': 'Low Priority Task',
        'category': 'development',
        'priority': 'low'
    })
    
    # Filter by priority
    response = await client.get('/tasks?priority=high')
    assert response.status_code == 200
    data = response.json()
    assert all(task['priority'] == 'high' for task in data)


@pytest.mark.asyncio
async def test_get_tasks_pagination(client):
    """Test task pagination"""
    # Create multiple tasks
    for i in range(5):
        await client.post('/tasks', json={
            'title': f'Task {i}',
            'category': 'development'
        })
    
    # Test pagination
    response = await client.get('/tasks?limit=2&offset=0')
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 2


@pytest.mark.asyncio
async def test_get_task_by_id(client):
    """Test getting a specific task"""
    # Create a task
    create_response = await client.post('/tasks', json={
        'title': 'Task 1',
        'category': 'bugfix'
    })
    task_id = create_response.json()['id']
    
    response = await client.get(f'/tasks/{task_id}')
    assert response.status_code == 200
    data = response.json()
    assert data['id'] == task_id


@pytest.mark.asyncio
async def test_get_nonexistent_task(client):
    """Test getting a task that doesn't exist"""
    response = await client.get('/tasks/99999')
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_task(client):
    """Test updating a task"""
    # Create a task
    create_response = await client.post('/tasks', json={
        'title': 'Original Title',
        'category': 'development'
    })
    task_id = create_response.json()['id']
    
    # Update the task
    response = await client.put(f'/tasks/{task_id}', json={
        'title': 'Updated Title',
        'status': 'completed',
        'actual_hours': 5.5
    })
    assert response.status_code == 200
    data = response.json()
    assert data['title'] == 'Updated Title'
    assert data['status'] == 'completed'
    assert data['actual_hours'] == 5.5
    assert data['completed_at'] is not None


@pytest.mark.asyncio
async def test_update_task_with_dependencies(client):
    """Test updating task with dependencies"""
    # Create two tasks
    task1_response = await client.post('/tasks', json={
        'title': 'Task 1',
        'category': 'development'
    })
    task1_id = task1_response.json()['id']
    
    task2_response = await client.post('/tasks', json={
        'title': 'Task 2',
        'category': 'development'
    })
    task2_id = task2_response.json()['id']
    
    # Update task2 to depend on task1
    response = await client.put(f'/tasks/{task2_id}', json={
        'dependencies': [task1_id]
    })
    assert response.status_code == 200
    data = response.json()
    assert task1_id in data['dependencies']


@pytest.mark.asyncio
async def test_delete_task(client):
    """Test deleting a task"""
    # Create a task
    create_response = await client.post('/tasks', json={
        'title': 'Task to Delete',
        'category': 'testing'
    })
    task_id = create_response.json()['id']
    
    # Delete the task
    response = await client.delete(f'/tasks/{task_id}')
    assert response.status_code == 200
    
    # Verify it's deleted
    get_response = await client.get(f'/tasks/{task_id}')
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_task_with_dependencies(client):
    """Test deleting a task that has dependents"""
    # Create two tasks
    task1_response = await client.post('/tasks', json={
        'title': 'Task 1',
        'category': 'development'
    })
    task1_id = task1_response.json()['id']
    
    await client.post('/tasks', json={
        'title': 'Task 2',
        'category': 'development',
        'dependencies': [task1_id]
    })
    
    # Delete task1
    response = await client.delete(f'/tasks/{task1_id}')
    assert response.status_code == 200
    data = response.json()
    assert data['affected_tasks'] == 1


@pytest.mark.asyncio
async def test_get_statistics(client):
    """Test getting task statistics"""
    # Create some tasks
    await client.post('/tasks', json={
        'title': 'Task 1',
        'category': 'development',
        'priority': 'high'
    })
    await client.post('/tasks', json={
        'title': 'Task 2',
        'category': 'testing',
        'priority': 'low'
    })
    
    response = await client.get('/tasks/stats/summary')
    assert response.status_code == 200
    data = response.json()
    assert 'total' in data
    assert 'by_status' in data
    assert 'by_priority' in data
    assert 'by_category' in data
    assert 'completion_rate' in data


@pytest.mark.asyncio
async def test_get_productivity_analytics(client):
    """Test getting productivity analytics"""
    # Create tasks with assignees
    await client.post('/tasks', json={
        'title': 'Task 1',
        'category': 'development',
        'assignee': 'john.doe',
        'estimated_hours': 8.0
    })
    
    response = await client.get('/tasks/analytics/productivity')
    assert response.status_code == 200
    data = response.json()
    assert 'total_estimated_hours' in data
    assert 'tasks_by_assignee' in data
    assert 'efficiency_rate' in data


@pytest.mark.asyncio
async def test_bulk_create_tasks(client):
    """Test bulk task creation"""
    tasks_data = [
        {
            'title': f'Bulk Task {i}',
            'category': 'development',
            'priority': 'medium'
        }
        for i in range(5)
    ]
    
    response = await client.post('/tasks/bulk', json=tasks_data)
    assert response.status_code == 200
    data = response.json()
    assert 'task_ids' in data
    assert len(data['task_ids']) == 5


@pytest.mark.asyncio
async def test_bulk_create_tasks_limit(client):
    """Test bulk task creation exceeds limit"""
    tasks_data = [
        {
            'title': f'Task {i}',
            'category': 'development'
        }
        for i in range(101)
    ]
    
    response = await client.post('/tasks/bulk', json=tasks_data)
    assert response.status_code == 400