import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from aplicacion.base_de_datos import Base, get_db
from aplicacion.principal import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_tareas.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _create_task(client, **kwargs):
    payload = {"title": "Test task", "categoria": None, **kwargs}
    resp = client.post("/tasks/", json=payload)
    assert resp.status_code == 201
    return resp.json()


def test_update_done_task_returns_400(client):
    task = _create_task(client, status="done")

    resp = client.patch(f"/tasks/{task['id']}", json={"title": "New title"})

    assert resp.status_code == 400
    assert resp.json()["detail"] == "Cannot update a completed task"


def test_update_pending_task_succeeds(client):
    task = _create_task(client)

    resp = client.patch(f"/tasks/{task['id']}", json={"title": "Updated"})

    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated"


def test_update_in_progress_task_succeeds(client):
    task = _create_task(client, status="in_progress")

    resp = client.patch(
        f"/tasks/{task['id']}", json={"status": "done"}
    )

    assert resp.status_code == 200
    assert resp.json()["status"] == "done"


def test_update_done_task_status_change_blocked(client):
    task = _create_task(client, status="done")

    resp = client.patch(f"/tasks/{task['id']}", json={"status": "pending"})

    assert resp.status_code == 400
    assert resp.json()["detail"] == "Cannot update a completed task"


def test_delete_all_tasks_clears_database(client):
    _create_task(client, title="Task 1")
    _create_task(client, title="Task 2")
    _create_task(client, title="Task 3")

    resp = client.delete("/tasks/")

    assert resp.status_code == 204
    assert client.get("/tasks/").json() == []


def test_delete_all_tasks_on_empty_database_returns_204(client):
    resp = client.delete("/tasks/")

    assert resp.status_code == 204
    assert client.get("/tasks/").json() == []


def test_create_task_with_categoria(client):
    task = _create_task(client, categoria="Trabajo")
    assert task["categoria"] == "Trabajo"


def test_create_task_without_categoria(client):
    task = _create_task(client)
    assert task["categoria"] is None


def test_update_task_categoria(client):
    task = _create_task(client)
    resp = client.patch(f"/tasks/{task['id']}", json={"categoria": "Personal"})
    assert resp.status_code == 200
    assert resp.json()["categoria"] == "Personal"


def test_get_task_includes_categoria(client):
    task = _create_task(client, categoria="Estudio")
    resp = client.get(f"/tasks/{task['id']}")
    assert resp.status_code == 200
    assert resp.json()["categoria"] == "Estudio"


def test_create_task_returns_201():
    response = client.post(
        "/tasks/",
        json={"title": "Test"}
    )
    assert response.status_code == 201
