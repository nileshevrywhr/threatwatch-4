import requests
import json

TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6IlJYa1RCQzlWUW0wbTBqOUoiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3Z4bnFqdHpld2pmY2h6YnJ0aWxvLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI5MWEzNGNlZS1kNjEzLTRmZmQtOWMyZC05OGViYTM4MDMzYTAiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzcwMjM5MDcyLCJpYXQiOjE3NzAyMzU0NzIsImVtYWlsIjoiaWxldW1zaHJhbmtAZ21haWwuY29tIiwicGhvbmUiOiIiLCJhcHBfbWV0YWRhdGEiOnsicHJvdmlkZXIiOiJlbWFpbCIsInByb3ZpZGVycyI6WyJlbWFpbCJdfSwidXNlcl9tZXRhZGF0YSI6eyJlbWFpbCI6ImlsZXVtc2hyYW5rQGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJmdWxsX25hbWUiOiJJbGV1bSBTIiwicGhvbmVfdmVyaWZpZWQiOmZhbHNlLCJzdWIiOiI5MWEzNGNlZS1kNjEzLTRmZmQtOWMyZC05OGViYTM4MDMzYTAiLCJzdWJzY3JpcHRpb25fdGllciI6ImZyZWUifSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJwYXNzd29yZCIsInRpbWVzdGFtcCI6MTc3MDIzNTQ3Mn1dLCJzZXNzaW9uX2lkIjoiOTIzOTliYzgtMjUzNy00MzFmLWJiYjYtOGQ0MDcyMmQwMDdjIiwiaXNfYW5vbnltb3VzIjpmYWxzZX0.wwTSwdG0cGCAVNTqSH-fWrL38Xpu2E0Gkp-zzInWNds"
URL = "https://web-api-production-1627.up.railway.app/api/monitors"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

payload = {
    "monitor_id": "88888888-4444-4444-4444-121212121212",
    "term": "Body Test",
    "frequency": "daily",
    "created_at": "2024-01-01T00:00:00Z",
    "next_run_at": "2024-01-01T00:00:00Z",
    "status": "active"
}

print("Testing POST with body...")
r = requests.post(URL, headers=headers, json=payload)
print(f"Status: {r.status_code}")
print(f"Response: {r.text}")

print("\nTesting POST with query params...")
params = payload
r = requests.post(URL, headers=headers, params=params)
print(f"Status: {r.status_code}")
print(f"Response: {r.text}")
