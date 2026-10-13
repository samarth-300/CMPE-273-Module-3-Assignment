"""REST Inventory Service (port 5001).
Set INVENTORY_DELAY_SECONDS to simulate a slow service."""
import os, time
from flask import Flask, jsonify, request

app = Flask(__name__)
STOCK = {"apple": 100, "banana": 5, "cherry": 0}
DELAY = float(os.environ.get("INVENTORY_DELAY_SECONDS", "0"))

@app.post("/inventory/check")
def check():
    data = request.get_json(silent=True) or {}
    item_id, qty = data.get("item_id"), data.get("quantity")
    if not isinstance(item_id, str) or not isinstance(qty, int) or qty <= 0:
        return jsonify(error="item_id (string) and quantity (positive int) required"), 400
    if DELAY:
        print(f"[inventory] sleeping {DELAY}s", flush=True)
        time.sleep(DELAY)
    if item_id not in STOCK:
        return jsonify(error=f"item '{item_id}' not found"), 404
    available = STOCK[item_id]
    if available < qty:
        return jsonify(item_id=item_id, requested=qty, available=available,
                       in_stock=False, error="insufficient stock"), 409
    return jsonify(item_id=item_id, requested=qty, available=available, in_stock=True), 200

if __name__ == "__main__":
    app.run(port=5001, threaded=True)
