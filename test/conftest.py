from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import Settings
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, Base
from app.router.oauth2 import create_access_token
import pytest
from app import models

settings = Settings()
SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.database_username}:{settings.database_password}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}_test"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False,autoflush=False, bind=engine)

@pytest.fixture
def session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(session):
    def override_get_db():
        try:
            yield session
        finally:
            session.close()
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)

@pytest.fixture
def test_user(client):
    user_data = {"email": "muse@gmail.com", "password": "123456"}
    res = client.post('/api/auth/', json=user_data)
    assert res.status_code == 201

    new_user = res.json()
    new_user["password"] = user_data["password"]
    return new_user

@pytest.fixture
def test_user2(client):
    user_data = {"email": "kraft@gmail.com", "password": "123456"}
    res = client.post('/api/auth/', json=user_data)
    assert res.status_code == 201

    new_user = res.json()
    new_user["password"] = user_data["password"]
    return new_user

@pytest.fixture
def token(test_user):
    return create_access_token({"user_id": test_user['id']})

@pytest.fixture
def authorized_client(client, token):
    client.headers = {**client.headers, "Authorization": f'Bearer {token}'}
    return client

@pytest.fixture
def create_payment_link(client, test_user):
    def _create_payment_link():
        link_data = {
            "amount": 100.0,
            "currency": "USD",
            "description": "Test payment link",
            "expiration_date": "2024-12-31T23:59:59"
        }
        return client.post("/api/payment-links/", json=link_data)
    return _create_payment_link