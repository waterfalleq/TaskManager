import pytest
from datetime import datetime, timedelta, timezone
from app.models.enums import TaskStatus, TaskPriority


# ---------- COMMON FIXTURES ----------

@pytest.fixture
def sample_task_data():
    """Base task data for most tests"""
    now = datetime.now(timezone.utc)
    return {
        "title": "Test Task",
        "description": "This is a test task",
        "deadline": (now + timedelta(days=3)).isoformat(),
        "status": TaskStatus.TODO.value,
        "priority": TaskPriority.HIGH.value,
    }


@pytest.fixture
def create_task(client):
    """Helper fixture to create tasks easily"""
    def _create_task(**overrides):
        now = datetime.now(timezone.utc)
        base = {
            "title": "Default Task",
            "description": "Default description",
            "deadline": None,
            "status": TaskStatus.TODO.value,
            "priority": TaskPriority.NONE.value,
        }
        base.update(overrides)
        response = client.post("/tasks/", json=base)
        assert response.status_code == 200, response.text
        return response.json()
    return _create_task


# ---------- CRUD TESTS ----------

def test_create_task(client, test_user, sample_task_data):
    response = client.post("/tasks/", json=sample_task_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == sample_task_data["title"]
    assert data["owner_id"] == test_user.id


def test_get_task_by_id(client, create_task):
    created = create_task(title="Unique Task")
    task_id = created["id"]

    get_resp = client.get(f"/tasks/{task_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["id"] == task_id
    assert data["title"] == "Unique Task"


def test_update_task(client, create_task):
    created = create_task(title="To Update")
    task_id = created["id"]

    update_data = {
        "title": "Updated Task",
        "status": TaskStatus.IN_PROGRESS.value,
    }

    update_resp = client.put(f"/tasks/{task_id}", json=update_data)
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["title"] == "Updated Task"
    assert data["status"] == TaskStatus.IN_PROGRESS.value


def test_delete_task(client, create_task):
    created = create_task()
    task_id = created["id"]

    delete_resp = client.delete(f"/tasks/{task_id}")
    assert delete_resp.status_code == 204

    get_resp = client.get(f"/tasks/{task_id}")
    assert get_resp.status_code == 404


# ---------- FILTERING / SEARCH ----------

def test_search_tasks(client, create_task):
    create_task(title="Find Me Task")
    resp = client.get("/tasks/search?title=Find")
    assert resp.status_code == 200
    results = resp.json()
    assert results
    assert any(task["title"] == "Find Me Task" for task in results)


def test_get_tasks_with_filters(client, create_task):
    create_task(priority=TaskPriority.HIGH.value, status=TaskStatus.TODO.value)
    resp = client.get("/tasks/?priority=high&status=to-do&order_by=created_at&order_dir=asc")
    assert resp.status_code == 200
    tasks = resp.json()
    assert tasks
    assert all(task["priority"] == "high" for task in tasks)
    assert all(task["status"] == "to-do" for task in tasks)


def test_filter_by_deadline_before(client, create_task):
    now = datetime.now(timezone.utc)
    create_task(
        title="Deadline Task",
        deadline=(now + timedelta(days=5)).isoformat(),
        priority=TaskPriority.MEDIUM.value,
    )
    filter_date = (now + timedelta(days=10)).isoformat()

    resp = client.get("/tasks/", params={"deadline_before": filter_date})
    assert resp.status_code == 200
    tasks = resp.json()
    assert tasks
    assert any(t["title"] == "Deadline Task" for t in tasks)


def test_filter_by_deadline_after(client, create_task):
    now = datetime.now(timezone.utc)
    create_task(
        title="Future Task",
        deadline=(now + timedelta(days=1)).isoformat(),
        priority=TaskPriority.LOW.value,
    )
    resp = client.get("/tasks/", params={"deadline_after": now.isoformat()})
    assert resp.status_code == 200
    tasks = resp.json()
    assert tasks
    assert any(t["title"] == "Future Task" for t in tasks)


def test_order_by_deadline_desc(client, create_task):
    now = datetime.now(timezone.utc)
    create_task(title="Soon", deadline=(now + timedelta(days=1)).isoformat())
    create_task(title="Later", deadline=(now + timedelta(days=5)).isoformat())

    resp = client.get("/tasks/?order_by=deadline&order_dir=desc")
    assert resp.status_code == 200
    tasks = resp.json()
    assert len(tasks) >= 2
    assert tasks[0]["title"] == "Later"


def test_pagination_limit_offset(client, create_task):
    for i in range(5):
        create_task(title=f"Task {i}")

    resp = client.get("/tasks/?limit=2&offset=2")
    assert resp.status_code == 200
    tasks = resp.json()
    assert len(tasks) == 2
    assert tasks[0]["title"] == "Task 2"


def test_show_completed_false(client, create_task):
    create_task(title="Completed Task", status=TaskStatus.DONE.value)
    resp = client.get("/tasks/?show_completed=false")
    assert resp.status_code == 200
    tasks = resp.json()
    assert all(t["status"] != "done" for t in tasks)


def test_invalid_enum_filter(client):
    resp = client.get("/tasks/?priority=INVALID")
    assert resp.status_code == 422


# ---------- PERMISSIONS ----------

def test_forbidden_get_other_users_task(client, db_session):
    from app.models.models import Task, User
    now = datetime.now(timezone.utc)

    other_user = User(email="other@example.com", hashed_password="fake", created_at=now)
    db_session.add(other_user)
    db_session.commit()
    db_session.refresh(other_user)

    task = Task(
        title="Other's Task",
        description="Should not be accessible",
        owner_id=other_user.id,
        status=TaskStatus.TODO.value,
        priority=TaskPriority.LOW.value,
        created_at=now,
        updated_at=now,
    )
    db_session.add(task)
    db_session.commit()

    response = client.get(f"/tasks/{task.id}")
    assert response.status_code == 403
    assert response.json()["detail"] == "Not allowed to access this task"


def test_forbidden_update_other_users_task(client, db_session):
    from app.models.models import Task, User
    now = datetime.now(timezone.utc)

    other_user = User(email="other2@example.com", hashed_password="fake", created_at=now)
    db_session.add(other_user)
    db_session.commit()
    db_session.refresh(other_user)

    task = Task(
        title="Other's Task",
        description="Should not be editable",
        owner_id=other_user.id,
        status=TaskStatus.TODO.value,
        priority=TaskPriority.MEDIUM.value,
        created_at=now,
        updated_at=now,
    )
    db_session.add(task)
    db_session.commit()

    response = client.put(f"/tasks/{task.id}", json={"title": "Hacked"})
    assert response.status_code == 403
    assert response.json()["detail"] == "Not allowed to update this task"


def test_forbidden_delete_other_users_task(client, db_session):
    from app.models.models import Task, User
    now = datetime.now(timezone.utc)

    other_user = User(email="other3@example.com", hashed_password="fake", created_at=now)
    db_session.add(other_user)
    db_session.commit()
    db_session.refresh(other_user)

    task = Task(
        title="Other's Task",
        description="Should not be deletable",
        owner_id=other_user.id,
        status=TaskStatus.TODO.value,
        priority=TaskPriority.HIGH.value,
        created_at=now,
        updated_at=now,
    )
    db_session.add(task)
    db_session.commit()

    response = client.delete(f"/tasks/{task.id}")
    assert response.status_code == 403
    assert response.json()["detail"] == "Not allowed to delete this task"