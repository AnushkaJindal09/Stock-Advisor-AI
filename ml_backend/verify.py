import requests

# 1. Registration Test
user_data = {
    "name": "Anushka Boss",
    "email": "test_user@gmail.com",
    "password": "password123"
}

print("--- Step 1: Registering User ---")
response = requests.post("http://127.0.0.1:5000/auth/register", json=user_data)
print(f"Status: {response.status_code}")
print(f"Message: {response.json()}")

print("\n--- Step 2: Logging In ---")
# 2. Login Test
login_data = {
    "email": "test_user@gmail.com",
    "password": "password123"
}
response_login = requests.post("http://127.0.0.1:5000/auth/login", json=login_data)
print(f"Status: {response_login.status_code}")
print(f"Token: {response_login.json().get('token')}")

# Portfolio Test
print("\n--- Step 3: Adding Stock to Portfolio ---")
portfolio_data = {
    "email": "test_user@gmail.com",
    "ticker": "RELIANCE.NS",
    "quantity": 10,
    "avg_price": 2500
}
response_port = requests.post("http://127.0.0.1:5000/portfolio/add", json=portfolio_data)
print(f"Status: {response_port.status_code}")
print(f"Message: {response_port.json()}")

# --- Step 4: AI Chat Testing ---
print("\n--- Step 4: Testing AI Chat Memory ---")
token = response_login.json().get('token') # Token nikalo
headers = {"Authorization": f"Bearer {token}"} # Header banao

chat_data = {
    "email": "test_user@gmail.com",
    "message": "Is Reliance a good buy?"
}

# Headers ke saath request bhejo
response_ai = requests.post("http://127.0.0.1:5000/ai/chat", json=chat_data, headers=headers)

print(f"Status: {response_ai.status_code}")
try:
    print(f"AI Reply: {response_ai.json().get('reply')}")
except:
    print(f"Response Error: {response_ai.text}")