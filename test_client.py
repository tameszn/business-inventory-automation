"""
Simple CLI to talk to the running agent, like a business owner would.

Usage:
    python test_client.py
    (make sure `uvicorn app.main:app --reload` is running first)
"""
import requests

BASE_URL = "http://localhost:8000"
USER_ID = "owner_cli"

print("Personal Productivity Agent — CLI test client")
print("Type a question, or 'reset' to clear conversation, or 'quit' to exit.\n")

while True:
    message = input("You: ").strip()
    if not message:
        continue
    if message.lower() in ("quit", "exit"):
        break
    if message.lower() == "reset":
        requests.post(f"{BASE_URL}/reset", json={"user_id": USER_ID})
        print("(conversation reset)\n")
        continue

    try:
        resp = requests.post(f"{BASE_URL}/chat", json={"user_id": USER_ID, "message": message})
        resp.raise_for_status()
        print("Agent:", resp.json()["reply"], "\n")
    except requests.exceptions.ConnectionError:
        print("Could not reach the agent. Is `uvicorn app.main:app --reload` running?\n")
        break
    except Exception as e:
        print("Error:", e, "\n")
