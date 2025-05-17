import requests
import json

BASE_URL = "http://localhost:8000/api/auth"

def create_admin():
    data = {
        "username": "admin",
        "password": "admin123"
    }
    response = requests.post(f"{BASE_URL}/create-admin", json=data)
    print("Create Admin Response:", response.status_code)
    print(response.json() if response.ok else response.text)

def test_login():
    data = {
        "username": "admin",
        "password": "admin123"
    }
    response = requests.post(f"{BASE_URL}/login", json=data)
    print("\nLogin Response:", response.status_code)
    print(response.json() if response.ok else response.text)

if __name__ == "__main__":
    print("Creating admin user...")
    create_admin()
    print("\nTesting login...")
    test_login() 