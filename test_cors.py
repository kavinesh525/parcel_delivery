import requests

print("Testing OPTIONS /upload_csv")
try:
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
    }
    resp = requests.options("http://127.0.0.1:8000/upload_csv", headers=headers)
    print(f"Status Code: {resp.status_code}")
    print("Headers:", resp.headers)
except Exception as e:
    print("Error:", e)

print("\nTesting OPTIONS /optimize_route")
try:
    resp2 = requests.options("http://127.0.0.1:8000/optimize_route", headers=headers)
    print(f"Status Code: {resp2.status_code}")
    print("Headers:", resp2.headers)
except Exception as e:
    print("Error:", e)
