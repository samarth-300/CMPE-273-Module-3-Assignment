"""REST Order Service (port 5000) -> calls Inventory over HTTP/JSON with a timeout."""
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)
INVENTORY_URL = "http://localhost:5001/inventory/check"
TIMEOUT_SECONDS = 2

@app.post("/orders")
def create_order():
    data = request.get_json(silent=True) or {}
    item_id, qty = data.get("item_id"), data.get("quantity")
    if not isinstance(item_id, str) or not isinstance(qty, int) or qty <= 0:
        return jsonify(error="item_id (string) and quantity (positive int) required"), 400
    try:
        r = requests.post(INVENTORY_URL, json={"item_id": item_id, "quantity": qty},
                          timeout=TIMEOUT_SECONDS)
    except requests.exceptions.Timeout:
        print(f"[order] Inventory timed out after {TIMEOUT_SECONDS}s", flush=True)
        return jsonify(status="failed", error="inventory service timed out"), 504
    except requests.exceptions.ConnectionError:
        return jsonify(status="failed", error="inventory service unavailable"), 503
    body = r.json()
    if r.status_code == 200:
        return jsonify(status="accepted", item_id=item_id, quantity=qty), 201
    if r.status_code == 404:
        return jsonify(status="rejected", error=body["error"]), 404
    if r.status_code == 409:
        return jsonify(status="rejected", error=body["error"], available=body["available"]), 409
    return jsonify(status="failed", error="unexpected inventory response"), 502

@app.get("/health")
def health():
    return jsonify(status="ok")

if __name__ == "__main__":
    app.run(port=5000, threaded=True)
