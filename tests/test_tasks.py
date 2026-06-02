# Tests de integración para los endpoints de tareas

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from aplicacion.base_de_datos import Base, get_db
from aplicacion.principal import app

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
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
    payload = {"title": "Test task", **kwargs}
    resp = client.post("/tasks/", json=payload)
    assert resp.status_code == 201
    return resp.json()


# ── Regresión Bug 1: update_task comprobaba payload.status en vez de task.status ──


def test_update_done_task_returns_400(client):
    """Una tarea con estado done no debe admitir cambios en ningún campo."""
    task = _create_task(client, status="done")

    resp = client.patch(f"/tasks/{task['id']}", json={"title": "New title"})

    assert resp.status_code == 400
    assert resp.json()["detail"] == "Cannot update a completed task"


def test_update_done_task_status_change_blocked(client):
    """Revertir el estado de una tarea completada también debe bloquearse."""
    task = _create_task(client, status="done")

    resp = client.patch(f"/tasks/{task['id']}", json={"status": "pending"})

    assert resp.status_code == 400
    assert resp.json()["detail"] == "Cannot update a completed task"


def test_update_pending_task_succeeds(client):
    """Las tareas pendientes sí pueden actualizarse."""
    task = _create_task(client)

    resp = client.patch(f"/tasks/{task['id']}", json={"title": "Updated"})

    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated"


def test_update_in_progress_task_succeeds(client):
    """Las tareas en progreso pueden pasar a done."""
    task = _create_task(client, status="in_progress")

    resp = client.patch(f"/tasks/{task['id']}", json={"status": "done"})

    assert resp.status_code == 200
    assert resp.json()["status"] == "done"


# ── Regresión Bug 2: create_task no validaba longitud mínima del título ──


def test_create_task_short_title_returns_400(client):
    """Un título con menos de 3 caracteres debe rechazarse con 400."""
    resp = client.post("/tasks/", json={"title": "ab"})

    assert resp.status_code == 400
    assert resp.json()["detail"] == "El título debe tener al menos 3 caracteres"


def test_create_task_whitespace_only_title_returns_400(client):
    """Un título con solo espacios en blanco debe rechazarse."""
    resp = client.post("/tasks/", json={"title": "   "})

    assert resp.status_code == 400
    assert resp.json()["detail"] == "El título debe tener al menos 3 caracteres"


def test_create_task_empty_title_returns_400(client):
    """Un título vacío debe rechazarse."""
    resp = client.post("/tasks/", json={"title": ""})

    assert resp.status_code == 400
    assert resp.json()["detail"] == "El título debe tener al menos 3 caracteres"


def test_create_task_min_valid_title_succeeds(client):
    """Un título con exactamente 3 caracteres debe aceptarse."""
    resp = client.post("/tasks/", json={"title": "abc"})

    assert resp.status_code == 201
    assert resp.json()["title"] == "abc"
