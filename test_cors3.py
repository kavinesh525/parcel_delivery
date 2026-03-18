import requests
import json

headers = {
    "Origin": "http://localhost:5173",
    "Access-Control-Request-Method": "POST",
    "Access-Control-Request-Headers": "content-type"
}
with open("d:\\quiz\\out.json", "w") as f:
    resp = requests.options("http://127.0.0.1:8000/upload_csv", headers=headers)
    json.dump({"status": resp.status_code, "headers": dict(resp.headers)}, f, indent=2)
