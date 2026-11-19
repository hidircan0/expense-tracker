import pytest


@pytest.mark.asyncio
async def test_register_login_and_profile(client):
    response = await client.post("/api/v1/auth/register", json={"email": "person@example.com", "password": "long-password-123", "full_name": "Test Person"})
    assert response.status_code == 201
    token_response = await client.post("/api/v1/auth/login", data={"username": "person@example.com", "password": "long-password-123"})
    assert token_response.status_code == 200
    headers = {"Authorization": f"Bearer {token_response.json()['access_token']}"}
    profile = await client.get("/api/v1/auth/me", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["email"] == "person@example.com"


@pytest.mark.asyncio
async def test_expense_access_is_user_scoped(client):
    first = await client.post("/api/v1/auth/register", json={"email": "one@example.com", "password": "password-one-123", "full_name": "One"})
    second = await client.post("/api/v1/auth/register", json={"email": "two@example.com", "password": "password-two-123", "full_name": "Two"})
    first_token = (await client.post("/api/v1/auth/login", data={"username": "one@example.com", "password": "password-one-123"})).json()["access_token"]
    second_token = (await client.post("/api/v1/auth/login", data={"username": "two@example.com", "password": "password-two-123"})).json()["access_token"]
    first_headers = {"Authorization": f"Bearer {first_token}"}
    second_headers = {"Authorization": f"Bearer {second_token}"}
    category = (await client.post("/api/v1/categories/", headers=first_headers, json={"name": "Food"})).json()
    expense = await client.post("/api/v1/expenses/", headers=first_headers, json={"amount": "12.50", "currency": "USD", "description": "Lunch", "date": "2025-01-01", "category_id": category["id"]})
    assert expense.status_code == 201
    hidden = await client.get(f"/api/v1/expenses/{expense.json()['id']}", headers=second_headers)
    assert hidden.status_code == 404
