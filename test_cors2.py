import requests

headers = {
    "Origin": "http://localhost:5173",
    "Access-Control-Request-Method": "POST",
    "Access-Control-Request-Headers": "content-type"
}

resp = requests.options("http://127.0.0.1:8000/upload_csv", headers=headers)
print("Status:", resp.status_code)
for k, v in resp.headers.items():
    print(f"{k}: {v}")
