import json
import random

from locust import HttpUser, between, task


class TaskManagerUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Setup - called when a user starts"""
        self.task_ids = []

    @task(3)
    def view_homepage(self):
        """Test loading the homepage"""
        self.client.get("/")

    @task(2)
    def check_health(self):
        """Test health endpoint"""
        self.client.get("/api/health")

    @task(2)
    def get_stats(self):
        """Test stats endpoint"""
        self.client.get("/api/stats")

    @task(5)
    def list_tasks(self):
        """Test listing tasks"""
        self.client.get("/api/tasks")

    @task(3)
    def create_task(self):
        """Test creating a new task"""
        priorities = ["low", "medium", "high"]
        task_data = {
            "title": f"Load Test Task {random.randint(1000, 9999)}",
            "description": f"This is a task created during load testing at {random.randint(1, 100)}%",
            "priority": random.choice(priorities),
        }

        response = self.client.post(
            "/api/tasks", json=task_data, headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            task_id = response.json().get("id")
            if task_id:
                self.task_ids.append(task_id)

    @task(2)
    def get_specific_task(self):
        """Test getting a specific task"""
        if self.task_ids:
            task_id = random.choice(self.task_ids)
            self.client.get(f"/api/tasks/{task_id}")

    @task(2)
    def update_task(self):
        """Test updating a task"""
        if self.task_ids:
            task_id = random.choice(self.task_ids)
            update_data = {
                "completed": random.choice([True, False]),
                "priority": random.choice(["low", "medium", "high"]),
            }

            self.client.put(
                f"/api/tasks/{task_id}",
                json=update_data,
                headers={"Content-Type": "application/json"},
            )

    @task(1)
    def delete_task(self):
        """Test deleting a task"""
        if self.task_ids:
            task_id = self.task_ids.pop()
            self.client.delete(f"/api/tasks/{task_id}")

    @task(2)
    def filter_tasks(self):
        """Test filtering tasks"""
        filters = [
            "?completed=true",
            "?completed=false",
            "?priority=high",
            "?priority=medium",
            "?priority=low",
            "?priority=high&completed=false",
        ]

        filter_param = random.choice(filters)
        self.client.get(f"/api/tasks{filter_param}")

    @task(1)
    def load_static_files(self):
        """Test loading static files"""
        static_files = ["/static/style.css", "/static/script.js"]

        for file_path in static_files:
            self.client.get(file_path)
