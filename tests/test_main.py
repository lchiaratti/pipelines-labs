import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import Base, app, get_db

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


class TestHealthEndpoint:
    def test_health_check(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestTaskCRUD:
    def test_create_task(self, client):
        task_data = {
            "title": "Test Task",
            "description": "Test Description",
            "priority": "high",
        }
        response = client.post("/api/tasks", json=task_data)
        assert response.status_code == 200

        data = response.json()
        assert data["title"] == task_data["title"]
        assert data["description"] == task_data["description"]
        assert data["priority"] == task_data["priority"]
        assert data["completed"] == False
        assert "id" in data
        assert "created_at" in data

    def test_create_task_minimal(self, client):
        task_data = {"title": "Minimal Task"}
        response = client.post("/api/tasks", json=task_data)
        assert response.status_code == 200

        data = response.json()
        assert data["title"] == task_data["title"]
        assert data["priority"] == "medium"  # default value
        assert data["completed"] == False

    def test_get_empty_tasks(self, client):
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_tasks(self, client):
        # Create a task first
        task_data = {"title": "Test Task", "priority": "low"}
        create_response = client.post("/api/tasks", json=task_data)
        assert create_response.status_code == 200

        # Get all tasks
        response = client.get("/api/tasks")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == task_data["title"]

    def test_get_task_by_id(self, client):
        # Create a task first
        task_data = {"title": "Test Task"}
        create_response = client.post("/api/tasks", json=task_data)
        task_id = create_response.json()["id"]

        # Get task by ID
        response = client.get(f"/api/tasks/{task_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == task_id
        assert data["title"] == task_data["title"]

    def test_get_nonexistent_task(self, client):
        response = client.get("/api/tasks/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"

    def test_update_task(self, client):
        # Create a task first
        task_data = {"title": "Original Task", "priority": "low"}
        create_response = client.post("/api/tasks", json=task_data)
        task_id = create_response.json()["id"]

        # Update the task
        update_data = {
            "title": "Updated Task",
            "description": "Updated Description",
            "priority": "high",
            "completed": True,
        }
        response = client.put(f"/api/tasks/{task_id}", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["description"] == update_data["description"]
        assert data["priority"] == update_data["priority"]
        assert data["completed"] == update_data["completed"]

    def test_update_partial_task(self, client):
        # Create a task first
        task_data = {"title": "Original Task", "priority": "low"}
        create_response = client.post("/api/tasks", json=task_data)
        task_id = create_response.json()["id"]
        original_data = create_response.json()

        # Partial update
        update_data = {"completed": True}
        response = client.put(f"/api/tasks/{task_id}", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["title"] == original_data["title"]  # unchanged
        assert data["priority"] == original_data["priority"]  # unchanged
        assert data["completed"] == True  # changed

    def test_update_nonexistent_task(self, client):
        update_data = {"title": "Updated Task"}
        response = client.put("/api/tasks/999", json=update_data)
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"

    def test_delete_task(self, client):
        # Create a task first
        task_data = {"title": "Task to Delete"}
        create_response = client.post("/api/tasks", json=task_data)
        task_id = create_response.json()["id"]

        # Delete the task
        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["message"] == "Task deleted successfully"

        # Verify task is deleted
        get_response = client.get(f"/api/tasks/{task_id}")
        assert get_response.status_code == 404

    def test_delete_nonexistent_task(self, client):
        response = client.delete("/api/tasks/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"


class TestTaskFiltering:
    def setup_tasks(self, client):
        """Helper method to create test tasks"""
        tasks = [
            {"title": "High Priority Task", "priority": "high", "completed": False},
            {"title": "Medium Priority Task", "priority": "medium", "completed": True},
            {"title": "Low Priority Task", "priority": "low", "completed": False},
            {"title": "Another High Priority", "priority": "high", "completed": True},
        ]

        created_tasks = []
        for task in tasks:
            response = client.post("/api/tasks", json=task)
            created_tasks.append(response.json())

        return created_tasks

    def test_filter_by_completed_status(self, client):
        self.setup_tasks(client)

        # Get completed tasks
        response = client.get("/api/tasks?completed=true")
        assert response.status_code == 200
        completed_tasks = response.json()
        assert len(completed_tasks) == 2
        assert all(task["completed"] for task in completed_tasks)

        # Get pending tasks
        response = client.get("/api/tasks?completed=false")
        assert response.status_code == 200
        pending_tasks = response.json()
        assert len(pending_tasks) == 2
        assert all(not task["completed"] for task in pending_tasks)

    def test_filter_by_priority(self, client):
        self.setup_tasks(client)

        # Get high priority tasks
        response = client.get("/api/tasks?priority=high")
        assert response.status_code == 200
        high_priority_tasks = response.json()
        assert len(high_priority_tasks) == 2
        assert all(task["priority"] == "high" for task in high_priority_tasks)

        # Get medium priority tasks
        response = client.get("/api/tasks?priority=medium")
        assert response.status_code == 200
        medium_priority_tasks = response.json()
        assert len(medium_priority_tasks) == 1
        assert medium_priority_tasks[0]["priority"] == "medium"

    def test_filter_combined(self, client):
        self.setup_tasks(client)

        # Get high priority completed tasks
        response = client.get("/api/tasks?priority=high&completed=true")
        assert response.status_code == 200
        filtered_tasks = response.json()
        assert len(filtered_tasks) == 1
        assert filtered_tasks[0]["priority"] == "high"
        assert filtered_tasks[0]["completed"] == True

    def test_pagination(self, client):
        self.setup_tasks(client)

        # Test limit
        response = client.get("/api/tasks?limit=2")
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 2

        # Test skip
        response = client.get("/api/tasks?skip=2&limit=2")
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 2


class TestTaskStats:
    def test_empty_stats(self, client):
        response = client.get("/api/stats")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 0
        assert data["completed"] == 0
        assert data["pending"] == 0
        assert data["high_priority"] == 0

    def test_stats_with_tasks(self, client):
        # Create test tasks
        tasks = [
            {"title": "Task 1", "priority": "high", "completed": False},
            {"title": "Task 2", "priority": "high", "completed": True},
            {"title": "Task 3", "priority": "medium", "completed": False},
            {"title": "Task 4", "priority": "low", "completed": True},
        ]

        for task in tasks:
            client.post("/api/tasks", json=task)

        response = client.get("/api/stats")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 4
        assert data["completed"] == 2
        assert data["pending"] == 2
        assert data["high_priority"] == 2


class TestStaticFiles:
    def test_root_endpoint_returns_html(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_health_endpoint_accessibility(self, client):
        """Test that health endpoint is accessible for monitoring"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data


class TestDataValidation:
    def test_create_task_without_title_fails(self, client):
        task_data = {"description": "Task without title"}
        response = client.post("/api/tasks", json=task_data)
        assert response.status_code == 422  # Validation error

    def test_create_task_with_invalid_priority(self, client):
        # This test assumes the API validates priority values
        # Since the current implementation doesn't validate priority,
        # this would need to be implemented in the main app
        task_data = {"title": "Test Task", "priority": "invalid_priority"}
        response = client.post("/api/tasks", json=task_data)
        # Currently this would pass, but in a production app you might want validation
        assert response.status_code == 200

    def test_update_task_with_empty_payload(self, client):
        # Create a task first
        task_data = {"title": "Test Task"}
        create_response = client.post("/api/tasks", json=task_data)
        task_id = create_response.json()["id"]

        # Update with empty payload
        response = client.put(f"/api/tasks/{task_id}", json={})
        assert response.status_code == 200
        # Should return the task unchanged
